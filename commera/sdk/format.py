import os
from urllib.parse import quote, urlencode

import frappe
from frappe import _
from frappe.core.doctype.file.utils import get_local_image
from frappe.utils.data import cint, cstr, flt, fmt_money, sha256_hash
from PIL import Image, ImageOps

from commera.shop_themes.doctype.shop_theme.shop_theme import is_within_directory
from commera.shop_themes.doctype.shop_theme_settings.shop_theme_settings import get_compiled_routes
from commera.shop_themes.theme_resolver import match_route
from commera.utils import get_currency_symbol

__all__ = ["IMAGE_WIDTHS", "URL_KINDS", "image_url", "money", "url_for"]

IMAGE_WIDTHS = (160, 320, 480, 640, 960, 1280, 1920)
RESIZED_IMAGES_URL = "/files/commera-images"
RESIZABLE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
RESIZE_ENDPOINT = "/api/method/commera.api.storefront.images.get_resized_image"
WEBP_QUALITY = 80
LOGIN_PATH = "/login"
STOREFRONT_PAGES = {
	"home": ("pages/index.html", None),
	"products": ("pages/products/list.html", None),
	"product": ("pages/products/details.html", None),
	"collection": ("pages/products/list.html", "category"),
	"search": ("pages/products/list.html", "search"),
	"cart": ("pages/cart/cart.html", None),
	"checkout": ("pages/cart/checkout.html", None),
	"account": ("pages/account/dashboard.html", None),
	"profile": ("pages/account/profile.html", None),
	"orders": ("pages/account/orders/index.html", None),
	"order": ("pages/account/orders/detail.html", "order_id"),
	"addresses": ("pages/account/address.html", None),
	"wishlist": ("pages/account/wishlist.html", None),
	"track_order": ("pages/track_order.html", None),
	"page": ("pages/shop_web_page.html", None),
}
URL_KINDS = ("login", *STOREFRONT_PAGES)
REGEX_SYNTAX = frozenset("()[]{}*+?|^$.")


def money(amount: float | None, currency: str | None = None) -> str:
	return f"{get_currency_symbol(currency)}{fmt_money(flt(amount), precision=2)}"


def url_for(kind: str, handle: str | None = None, **params) -> str:
	if kind not in URL_KINDS:
		frappe.throw(_("URL kind must be one of {0}.").format(", ".join(URL_KINDS)))
	if kind == "login":
		return with_query(LOGIN_PATH, params)

	template_path, handle_param = STOREFRONT_PAGES[kind]
	if handle_param:
		if not handle:
			frappe.throw(_("A {0} URL needs a handle.").format(kind))
		params = {handle_param: handle, **params}
		handle = None
	return with_query(get_route_path(template_path, handle), params)


def get_route_path(template_path: str, handle: str | None) -> str:
	routes = get_compiled_routes()["routes"]
	route = next((route for route in routes if route["template_path"] == template_path), None)
	if not route:
		frappe.throw(
			_("No storefront route serves {0}. Add one in Shop Theme Settings.").format(template_path)
		)

	path, raw_path = reverse_route_pattern(route["pattern"].pattern, handle)
	# The resolver takes the first matching row, so an earlier row can shadow this one.
	matched_route, _match = match_route(routes, raw_path)
	if matched_route is not route:
		throw_unreversible_route(route["pattern"].pattern)
	return f"/{path}"


def reverse_route_pattern(source: str, handle: str | None) -> tuple[str, str]:
	source = source.removeprefix("^").removesuffix("$")
	path, raw_path = [], []
	has_handle_group = False
	position = 0
	while position < len(source):
		character = source[position]
		if source.startswith("(?P<", position):
			name, position = read_named_group(source, position)
			if name == "lang":
				value = raw_value = frappe.local.lang or "en"
			elif has_handle_group:
				throw_unreversible_route(source)
			elif not handle:
				frappe.throw(_("This URL needs a handle."))
			else:
				has_handle_group = True
				value, raw_value = quote(cstr(handle)), cstr(handle)
			path.append(value)
			raw_path.append(raw_value)
			continue
		if character == "\\" and position + 1 < len(source) and not source[position + 1].isalnum():
			character = source[position + 1]
			position += 1
		elif character == "\\" or character in REGEX_SYNTAX:
			throw_unreversible_route(source)
		path.append(character)
		raw_path.append(character)
		position += 1

	if handle and not has_handle_group:
		frappe.throw(_("This URL takes no handle."))
	return "".join(path), "".join(raw_path)


def read_named_group(source: str, start: int) -> tuple[str, int]:
	name_end = source.index(">", start)
	depth, position = 1, name_end + 1
	while depth:
		character = source[position]
		if character == "\\":
			position += 1
		elif character == "(":
			depth += 1
		elif character == ")":
			depth -= 1
		elif character == "[":
			position = source.index("]", position + 2)
		position += 1
	return source[start + 4 : name_end], position


def throw_unreversible_route(pattern: str):
	frappe.throw(_("The storefront route {0} cannot be turned into a link.").format(pattern))


def with_query(path: str, params: dict) -> str:
	query = urlencode({key: value for key, value in params.items() if value is not None}, doseq=True)
	return f"{path}?{query}" if query else path


def image_url(path: str | None, width: int | None = None) -> str | None:
	if not width or not is_resizable(path):
		return path or None
	width = get_image_width(width)
	resized_url = get_resized_image_url(path, width)
	if os.path.isfile(get_public_path(resized_url)):
		return resized_url
	return f"{RESIZE_ENDPOINT}?{urlencode({'path': path, 'width': width})}"


def save_resized_image(path: str, width: int) -> str:
	if not is_resizable(path) or width not in IMAGE_WIDTHS:
		frappe.throw(
			_("Only public JPEG, PNG and WebP files resize, to one of {0} pixels wide.").format(
				", ".join(str(allowed) for allowed in IMAGE_WIDTHS)
			)
		)
	source = get_public_path(path)
	if not is_within_directory(frappe.get_site_path("public", "files"), source) or not os.path.isfile(source):
		raise frappe.DoesNotExistError(_("Image {0} not found").format(path))

	resized_url = get_resized_image_url(path, width)
	target = get_public_path(resized_url)
	if os.path.isfile(target):
		return resized_url

	image = ImageOps.exif_transpose(get_local_image(path)[0])
	image = image.convert("RGBA" if image.has_transparency_data else "RGB")
	image.thumbnail((width, image.height), Image.Resampling.LANCZOS)
	os.makedirs(os.path.dirname(target), exist_ok=True)
	partial_target = f"{target}.{frappe.generate_hash(length=8)}.part"
	image.save(partial_target, format="WEBP", quality=WEBP_QUALITY)
	os.replace(partial_target, target)
	return resized_url


def is_resizable(path: str | None) -> bool:
	path = cstr(path)
	return (
		path.startswith("/files/")
		and not path.startswith(f"{RESIZED_IMAGES_URL}/")
		and path.lower().endswith(RESIZABLE_EXTENSIONS)
	)


def get_image_width(width: int) -> int:
	return next((allowed for allowed in IMAGE_WIDTHS if allowed >= cint(width)), IMAGE_WIDTHS[-1])


def get_resized_image_url(path: str, width: int) -> str:
	return f"{RESIZED_IMAGES_URL}/{width}/{sha256_hash(path)[:24]}.webp"


def get_public_path(url: str) -> str:
	return frappe.get_site_path("public", url.lstrip("/"))
