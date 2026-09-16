# Copyright (c) 2026, company@bwhstudios.com and Contributors
# See license.txt

"""An Item Group gets a shopper-facing display name even when whoever inserts it never sets one."""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils.nestedset import get_root_of

PREFIX = "Test IGD"


class TestItemGroupDisplayname(IntegrationTestCase):
	def setUp(self):
		self.tag = frappe.generate_hash(length=8)

	def tearDown(self):
		frappe.db.delete("Item Group", {"name": ["like", f"{PREFIX}%"]})

	def make_item_group(self, item_group_name, **kwargs):
		item_group = frappe.get_doc(
			{
				"doctype": "Item Group",
				"item_group_name": item_group_name,
				"parent_item_group": get_root_of("Item Group"),
				"is_group": 0,
				**kwargs,
			}
		)
		item_group.insert(ignore_permissions=True)
		return item_group

	def test_insert_without_displayname_falls_back_to_group_name(self):
		# ERPNext's setup wizard inserts its stock groups this way; before the fallback it failed outright.
		item_group_name = f"{PREFIX} Fallback {self.tag}"
		item_group = self.make_item_group(item_group_name)

		self.assertEqual(item_group.custom_displayname, item_group_name)

	def test_explicit_displayname_survives(self):
		item_group_name = f"{PREFIX} Explicit {self.tag}"
		item_group = self.make_item_group(item_group_name, custom_displayname="Sale Rail")

		self.assertEqual(item_group.custom_displayname, "Sale Rail")
