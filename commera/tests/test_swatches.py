# Copyright (c) 2026, company@bwhstudios.com and Contributors
# Tests for colour swatches: what the Swatch doctype refuses, and how a swatch reaches the
# Attributes screen and the storefront. Real-DB, auto-rolled-back.

import frappe
from frappe.tests import IntegrationTestCase

from commera.api.admin.catalog import (
	clear_swatch,
	get_attribute_values,
	get_attributes,
	rename_attribute_value,
	set_swatch,
)
from commera.swatches import CACHE_KEY, COLOUR_ATTRIBUTE, get_swatch_map


class SwatchTestCase(IntegrationTestCase):
	def setUp(self):
		self.suffix = frappe.generate_hash(length=6).upper()
		self.attribute = self.make_attribute(["Navy", "Denim", "Olive"])

	def tearDown(self):
		# The DB rolls back with the test; redis does not, and a stale map would leak into the next one.
		frappe.cache.hdel(CACHE_KEY, self.attribute)

	def make_attribute(self, values):
		attribute = frappe.new_doc("Item Attribute")
		attribute.attribute_name = f"Swatch Colour {self.suffix}"
		for index, value in enumerate(values):
			attribute.append("item_attribute_values", {"attribute_value": value, "abbr": f"S{index}"})
		attribute.insert()
		return attribute.name


class TestSwatchDocument(SwatchTestCase):
	def test_a_swatch_for_a_value_the_attribute_does_not_have_is_refused(self):
		with self.assertRaises(frappe.ValidationError):
			set_swatch(self.attribute, "Puce", color="#CC8899")

	def test_a_swatch_with_neither_colour_nor_image_is_refused(self):
		with self.assertRaises(frappe.ValidationError):
			set_swatch(self.attribute, "Navy")

	def test_setting_the_same_value_twice_updates_rather_than_duplicates(self):
		set_swatch(self.attribute, "Navy", color="#000080")
		set_swatch(self.attribute, "Navy", color="#1B2A4A")

		swatches = frappe.get_all(
			"Swatch", filters={"attribute": self.attribute, "attribute_value": "Navy"}, pluck="color"
		)
		self.assertEqual(swatches, ["#1B2A4A"])

	def test_an_image_and_a_colour_can_both_be_stored(self):
		set_swatch(self.attribute, "Denim", color="#3B5A7A", image="/files/denim.webp")

		swatch = get_swatch_map(self.attribute)["Denim"]
		self.assertEqual(swatch["color"], "#3B5A7A")
		self.assertEqual(swatch["image"], "/files/denim.webp")


class TestSwatchReads(SwatchTestCase):
	def test_get_swatch_map_omits_values_that_have_no_swatch(self):
		set_swatch(self.attribute, "Navy", color="#1B2A4A")

		swatches = get_swatch_map(self.attribute)
		self.assertEqual(list(swatches), ["Navy"])

	def test_get_attribute_values_carries_the_swatch_and_keeps_stored_order(self):
		set_swatch(self.attribute, "Olive", color="#4A5D3A")

		values = get_attribute_values(self.attribute)

		self.assertEqual([row["value"] for row in values], ["Navy", "Denim", "Olive"])
		self.assertEqual(values[2]["color"], "#4A5D3A")
		# A value with no swatch still answers the same keys, so no caller branches on a missing record.
		self.assertIsNone(values[0]["color"])
		self.assertIsNone(values[0]["image"])

	def test_the_attributes_screen_costs_the_same_queries_however_many_swatches_exist(self):
		set_swatch(self.attribute, "Navy", color="#1B2A4A")
		set_swatch(self.attribute, "Denim", image="/files/denim.webp")
		set_swatch(self.attribute, "Olive", color="#4A5D3A")

		# Warm the column cache first: on a cold one Frappe adds an information_schema lookup,
		# which is environment noise rather than anything this test is about.
		get_attributes()

		# Five flat reads. The per-attribute and per-value usage counts cannot be folded into one:
		# a template using two values of the same attribute would be counted twice.
		with self.assertQueryCount(5):
			get_attributes()

	def test_clearing_a_swatch_leaves_the_value_itself(self):
		set_swatch(self.attribute, "Navy", color="#1B2A4A")
		clear_swatch(self.attribute, "Navy")

		self.assertEqual(get_swatch_map(self.attribute), {})
		self.assertEqual(
			[row["value"] for row in get_attribute_values(self.attribute)], ["Navy", "Denim", "Olive"]
		)

	def test_the_cached_map_does_not_outlive_the_swatch_it_described(self):
		set_swatch(self.attribute, "Navy", color="#1B2A4A")
		get_swatch_map(self.attribute)

		set_swatch(self.attribute, "Navy", color="#FFFFFF")

		self.assertEqual(get_swatch_map(self.attribute)["Navy"]["color"], "#FFFFFF")


class TestAttributeValueRename(SwatchTestCase):
	def test_an_unused_value_can_be_renamed(self):
		rename_attribute_value(self.attribute, "Olive", "Moss")

		self.assertEqual(
			[row["value"] for row in get_attribute_values(self.attribute)], ["Navy", "Denim", "Moss"]
		)

	def test_renaming_carries_the_swatch_across(self):
		set_swatch(self.attribute, "Olive", color="#4A5D3A")
		rename_attribute_value(self.attribute, "Olive", "Moss")

		swatches = get_swatch_map(self.attribute)
		self.assertNotIn("Olive", swatches)
		self.assertEqual(swatches["Moss"]["color"], "#4A5D3A")

	def test_a_name_the_attribute_already_has_is_refused(self):
		with self.assertRaises(frappe.ValidationError):
			rename_attribute_value(self.attribute, "Olive", "Navy")

	def test_an_empty_name_is_refused(self):
		with self.assertRaises(frappe.ValidationError):
			rename_attribute_value(self.attribute, "Olive", "   ")

	def test_the_attributes_screen_marks_only_the_colour_axis(self):
		by_name = {row["name"]: row for row in get_attributes()}

		self.assertFalse(by_name[self.attribute]["is_colour"])
		if COLOUR_ATTRIBUTE in by_name:
			self.assertTrue(by_name[COLOUR_ATTRIBUTE]["is_colour"])

	def test_every_value_reports_whether_a_product_uses_it(self):
		values = get_attribute_values(self.attribute)

		# Nothing in this test's own attribute is on a product yet.
		self.assertEqual({row["used_by"] for row in values}, {0})
