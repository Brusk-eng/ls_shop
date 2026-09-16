# Copyright (c) 2026, company@bwhstudios.com and contributors
# For license information, please see license.txt

import frappe

from commera.swatches import COLOUR_ATTRIBUTE

# ERPNext ships the British spelling and commera seeds the American one, so a store ends up with
# two colour attributes. "Color" is the one commera's own code keys off.
DUPLICATE = "Colour"


def execute():
	if not frappe.db.exists("Item Attribute", DUPLICATE):
		return

	# Never touch one a store has actually built products on — that is a merge, not a cleanup, and it
	# would move item codes. An owner who has used it keeps it.
	if frappe.db.exists("Item Variant Attribute", {"attribute": DUPLICATE}):
		return

	if frappe.db.exists("Item Attribute", COLOUR_ATTRIBUTE):
		frappe.delete_doc("Item Attribute", DUPLICATE, ignore_permissions=True, force=True)
