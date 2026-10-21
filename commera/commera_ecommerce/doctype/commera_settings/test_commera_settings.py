# Copyright (c) 2025, company@bwhstudios.com and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from commera import seo
from commera.api.admin.orders import get_reporting_currency
from commera.utils import get_currency_symbol, get_store_currency


class TestCommeraSettings(IntegrationTestCase):
	def setUp(self):
		self.settings = frappe.get_doc("Commera Settings")
		self.store_currency = get_store_currency()
		self.other_currency = frappe.get_all(
			"Currency", filters={"name": ("!=", self.store_currency)}, pluck="name", limit=1
		)[0]

	def make_price_list(self, currency: str) -> str:
		return (
			frappe.get_doc(
				{
					"doctype": "Price List",
					"price_list_name": f"ZZ Store Currency {frappe.generate_hash(length=6)}",
					"currency": currency,
					"selling": 1,
				}
			)
			.insert(ignore_permissions=True)
			.name
		)

	def test_a_sale_price_list_in_another_currency_is_refused(self):
		self.settings.sale_price_list = self.make_price_list(self.other_currency)

		with self.assertRaisesRegex(frappe.ValidationError, f"the store sells in {self.store_currency}"):
			self.settings.save()

	def test_a_store_price_list_keeps_the_store_currency(self):
		price_list = frappe.get_doc("Price List", self.settings.sale_price_list)
		price_list.currency = self.other_currency

		with self.assertRaisesRegex(frappe.ValidationError, f"which sells in {self.store_currency}"):
			price_list.save()

	def test_another_price_list_may_use_any_currency(self):
		price_list = frappe.get_doc("Price List", self.make_price_list(self.store_currency))
		price_list.currency = self.other_currency

		price_list.save()

	def test_prices_are_labelled_in_the_company_currency_not_the_global_default(self):
		frappe.db.set_single_value("Global Defaults", "default_currency", self.other_currency)
		frappe.clear_cache(doctype="Global Defaults")

		symbol = frappe.get_cached_value("Currency", self.store_currency, "symbol")
		self.assertEqual(seo.get_site_currency(), self.store_currency)
		self.assertEqual(get_reporting_currency(), self.store_currency)
		if self.store_currency != "SAR" and symbol:
			self.assertEqual(get_currency_symbol(), symbol)
