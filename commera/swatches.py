# Copyright (c) 2026, company@bwhstudios.com and contributors
# For license information, please see license.txt

import frappe

# ERPNext holds the US spelling; the British "Colour" that appears in labels is presentation only.
COLOUR_ATTRIBUTE = "Color"

CACHE_KEY = "commera_swatches"

# The colours a clothing store actually stocks, so a name it recognises arrives already set and an
# owner only picks for the ones it does not know. Matched case-insensitively.
DEFAULT_SWATCHES = {
	"beige": "#D9CBB3",
	"black": "#111827",
	"blue": "#1E40AF",
	"blush": "#E8B4B8",
	"bronze": "#8C6239",
	"brown": "#6B4423",
	"burgundy": "#5C1A2B",
	"charcoal": "#36393F",
	"cream": "#F5EFE0",
	"crimson": "#9B1C31",
	"gold": "#C9A227",
	"gray": "#8A8F98",
	"green": "#2F6B3F",
	"grey": "#8A8F98",
	"ivory": "#F7F3E8",
	"khaki": "#B5A26B",
	"lavender": "#B39DDB",
	"lilac": "#C8A2C8",
	"maroon": "#7A1F2B",
	"mint": "#A8D5BA",
	"mustard": "#C9A227",
	"navy": "#1B2A4A",
	"olive": "#4A5D3A",
	"orange": "#D2691E",
	"peach": "#F5C2A0",
	"pink": "#EC4899",
	"purple": "#6D28D9",
	"red": "#C81E1E",
	"rust": "#B45309",
	"sand": "#E2D2B8",
	"silver": "#C0C4CC",
	"tan": "#D2B48C",
	"teal": "#0F766E",
	"turquoise": "#40C4B4",
	"white": "#F5F5F0",
	"yellow": "#F5C518",
}


def get_swatch_map(attribute: str = COLOUR_ATTRIBUTE) -> dict[str, dict]:
	return frappe.cache.hget(CACHE_KEY, attribute, generator=lambda: build_swatch_map(attribute))


def build_swatch_map(attribute: str) -> dict[str, dict]:
	rows = frappe.get_all(
		"Swatch",
		filters={"attribute": attribute},
		fields=["attribute_value", "color", "image"],
	)
	return {row.attribute_value: {"color": row.color, "image": row.image} for row in rows}


def get_default_colour(value: str) -> str | None:
	return DEFAULT_SWATCHES.get(frappe.utils.cstr(value).strip().casefold())


def ensure_default_swatch(attribute: str, value: str):
	"""Give a recognised colour name its swatch. Never overwrites one an owner has already set."""
	if attribute != COLOUR_ATTRIBUTE:
		return

	colour = get_default_colour(value)
	if not colour:
		return
	if frappe.db.exists("Swatch", {"attribute": attribute, "attribute_value": value}):
		return

	swatch = frappe.new_doc("Swatch")
	swatch.attribute = attribute
	swatch.attribute_value = value
	swatch.color = colour
	swatch.insert(ignore_permissions=True)


# ERPNext's setup wizard seeds the British spelling after commera installs, so a store would end up
# with two colour attributes; "Color" is the one commera keys off.
DUPLICATE_COLOUR_ATTRIBUTE = "Colour"


def drop_unused_colour_attribute(setup_args=None):
	if not frappe.db.exists("Item Attribute", DUPLICATE_COLOUR_ATTRIBUTE):
		return
	if frappe.db.exists("Item Variant Attribute", {"attribute": DUPLICATE_COLOUR_ATTRIBUTE}):
		return

	frappe.delete_doc("Item Attribute", DUPLICATE_COLOUR_ATTRIBUTE, ignore_permissions=True, force=True)
