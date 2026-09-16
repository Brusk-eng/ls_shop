# Copyright (c) 2026, company@bwhstudios.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from commera.swatches import CACHE_KEY


class Swatch(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		attribute: DF.Link
		attribute_value: DF.Data
		color: DF.Color | None
		image: DF.AttachImage | None

	# end: auto-generated types

	def validate(self):
		self.validate_attribute_value_exists()
		self.validate_has_something_to_show()

	def validate_attribute_value_exists(self):
		if not frappe.db.exists(
			"Item Attribute Value",
			{
				"parent": self.attribute,
				"parenttype": "Item Attribute",
				"attribute_value": self.attribute_value,
			},
		):
			frappe.throw(
				_("{0} has no value called {1}.").format(
					frappe.bold(self.attribute), frappe.bold(self.attribute_value)
				)
			)

	def validate_has_something_to_show(self):
		if not self.color and not self.image:
			frappe.throw(_("Set a colour or an image — a swatch with neither has nothing to show."))

	def on_update(self):
		frappe.cache.hdel(CACHE_KEY, self.attribute)

	def on_trash(self):
		frappe.cache.hdel(CACHE_KEY, self.attribute)
