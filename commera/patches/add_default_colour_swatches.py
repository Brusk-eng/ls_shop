# Copyright (c) 2026, company@bwhstudios.com and contributors
# For license information, please see license.txt

import frappe

from commera.swatches import COLOUR_ATTRIBUTE, ensure_default_swatch


def execute():
	frappe.reload_doc("commera_ecommerce", "doctype", "swatch")

	if not frappe.db.exists("Item Attribute", COLOUR_ATTRIBUTE):
		return

	values = frappe.get_all(
		"Item Attribute Value",
		filters={"parent": COLOUR_ATTRIBUTE, "parenttype": "Item Attribute"},
		pluck="attribute_value",
	)
	for value in values:
		ensure_default_swatch(COLOUR_ATTRIBUTE, value)

	frappe.cache.hdel("commera_swatches", COLOUR_ATTRIBUTE)
