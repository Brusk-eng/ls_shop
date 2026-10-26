import os
from urllib.parse import quote, urlencode

import frappe
from frappe import _
from frappe.core.doctype.file.utils import get_local_image
from frappe.utils.data import cint, cstr, flt, fmt_money, sha256_hash
from PIL import Image, ImageOps

from commera.shop_themes.doctype.shop_theme.shop_theme import is_within_directory
from commera.utils import get_currency_symbol

__all__ = ["IMAGE_WIDTHS", "URL_KINDS", "image_url", "money", "url_for"]

IMAGE_WIDTHS = (160, 320, 480, 640, 960, 1280, 1920)
RESIZED_IMAGES_URL = "/files/commera-images"
RESIZABLE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
RESIZE_ENDPOINT = "/api/method/commera.api.storefront.images.get_resized_image"
WEBP_QUALITY = 80
STOREFRONT_URLS = {
	"home": ("/{lang}", None),
	"products": ("/{lang}/products", None),
	"product": ("/{lang}/products/{handle}", None),
	"collection": ("/{lang}/products", "category"),
	"search": ("/{lang}/products", "search"),
	"cart": ("/{lang}/cart", None),
	"checkout": ("/{lang}/cart/checkout", None),
	"account": ("/{lang}/account/dashboard", None),
	"profile": ("/{lang}/account/profile", None),
	"orders": ("/{lang}/account/orders", None),
	"order": ("/{lang}/account/orders/detail", "order_id"),
	"addresses": ("/{lang}/account/address", None),
	"wishlist": ("/{lang}/account/wishlist", None),
	"page": ("/{lang}/page/{handle}", None),
	"login": ("/login", None),
}
URL_KINDS = tuple(STOREFRONT_URLS)


def money(amount: float | None, currency: str | None = None) -> str:
	return f"{get_currency_symbol(currency)}{fmt_money(flt(amount), precision=2)}"


def url_for(kind: str, handle: str | None = None, **params) -> str:
	if kind not in STOREFRONT_URLS:
		frappe.throw(_("URL kind must be one of {0}.").format(", ".join(URL_KINDS)))
	path, handle_param = STOREFRONT_URLS[kind]
	if ("{handle}" in path or handle_param) and not handle:
		frappe.throw(_("A {0} URL needs a handle.").format(kind))
	if handle_param:
		params = {handle_param: handle, **params}
	path = path.format(lang=frappe.local.lang or "en", handle=quote(cstr(handle)))
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
