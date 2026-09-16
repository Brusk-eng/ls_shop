# Copyright (c) 2026, company@bwhstudios.com and contributors
# For license information, please see license.txt

import frappe

# ERPNext holds the US spelling; the British "Colour" that appears in labels is presentation only.
COLOUR_ATTRIBUTE = "Color"

CACHE_KEY = "commera_swatches"


def get_swatch_map(attribute: str = COLOUR_ATTRIBUTE) -> dict[str, dict]:
	return frappe.cache.hget(CACHE_KEY, attribute, generator=lambda: build_swatch_map(attribute))


def build_swatch_map(attribute: str) -> dict[str, dict]:
	rows = frappe.get_all(
		"Swatch",
		filters={"attribute": attribute},
		fields=["attribute_value", "color", "image"],
	)
	return {row.attribute_value: {"color": row.color, "image": row.image} for row in rows}
