# Copyright (c) 2026, company@bwhstudios.com and Contributors

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils.data import add_days, add_months, flt, formatdate, getdate

from commera.api.admin.customers import (
	CUSTOMER_ORDER_LIMIT,
	SPEND_CHART_MONTHS,
	TOP_PRODUCT_LIMIT,
	get_customer,
	save_customer_note,
)
from commera.tests.test_admin_orders import (
	COMPANY,
	CURRENCY,
	ITEM_GROUP,
	ensure_fiscal_year,
)
from commera.tests.test_order_access import make_website_user

ITEM_RATE = 100.0


def make_customer(currency=None) -> str:
	return (
		frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": f"ZZ Profile Customer {frappe.generate_hash(length=8)}",
				"customer_type": "Individual",
				"default_currency": currency,
			}
		)
		.insert(ignore_permissions=True)
		.name
	)


def make_item(image=None) -> str:
	item_code = f"ZZ-PROFILE-{frappe.generate_hash(length=8)}"
	frappe.get_doc(
		{
			"doctype": "Item",
			"item_code": item_code,
			"item_name": f"ZZ Profile Item {item_code[-4:]}",
			"item_group": ITEM_GROUP,
			"stock_uom": "Nos",
			"is_stock_item": 0,
			"image": image,
		}
	).insert(ignore_permissions=True)
	return item_code


def make_webshop_order(
	customer,
	item_code,
	qty=1,
	rate=ITEM_RATE,
	placed_on=None,
	submit=False,
	payment_mode=None,
	currency=CURRENCY,
):
	"""A storefront order. Left as a draft unless a test needs a submitted one - is_webshop_order counts
	drafts, and a draft skips the whole GL chain."""
	placed_on = getdate(placed_on or getdate())
	ensure_fiscal_year(placed_on)
	if payment_mode:
		ensure_payment_mode(payment_mode)
	sales_order = frappe.new_doc("Sales Order")
	sales_order.update(
		{
			"customer": customer,
			"company": COMPANY,
			"currency": currency,
			"conversion_rate": 1,
			"transaction_date": placed_on,
			"delivery_date": placed_on,
			"order_type": "Shopping Cart",
			"custom_ecommerce_payment_mode": payment_mode,
			"items": [{"item_code": item_code, "qty": qty, "rate": rate, "delivery_date": placed_on}],
		}
	)
	sales_order.flags.ignore_permissions = True
	sales_order.insert()
	if submit:
		sales_order.submit()
	return sales_order


def ensure_payment_mode(name):
	"""custom_ecommerce_payment_mode is a Link to Mode of Payment, and CI's bare site ships none of the
	modes a storefront actually books against — a missing one fails the order with LinkValidationError."""
	if not frappe.db.exists("Mode of Payment", name):
		frappe.get_doc({"doctype": "Mode of Payment", "mode_of_payment": name, "enabled": 1}).insert(
			ignore_permissions=True
		)


class TestCustomerProfile(IntegrationTestCase):
	def setUp(self):
		self.addCleanup(frappe.db.rollback)
		self.addCleanup(frappe.set_user, "Administrator")
		self.customer = make_customer()
		self.item_code = make_item()

	def test_lifetime_figures_are_not_capped_by_the_recent_order_list(self):
		"""The regression: spend and order count were summed off the capped recent list, so a customer
		past CUSTOMER_ORDER_LIMIT read smaller on their own profile than on the Customers list."""
		order_count = CUSTOMER_ORDER_LIMIT + 2
		for _ in range(order_count):
			make_webshop_order(self.customer, self.item_code)

		profile = get_customer(self.customer)

		self.assertEqual(profile["orders"], order_count)
		self.assertAlmostEqual(profile["spend"], ITEM_RATE * order_count)
		self.assertAlmostEqual(profile["average_order"], ITEM_RATE)
		self.assertAlmostEqual(profile["units"], order_count)
		self.assertEqual(len(profile["recent_orders"]), CUSTOMER_ORDER_LIMIT)

	def test_days_between_orders_needs_two_orders(self):
		self.assertIsNone(get_customer(self.customer)["days_between_orders"])

		make_webshop_order(self.customer, self.item_code, placed_on=add_days(getdate(), -20))
		self.assertIsNone(get_customer(self.customer)["days_between_orders"])

		make_webshop_order(self.customer, self.item_code, placed_on=add_days(getdate(), -10))
		make_webshop_order(self.customer, self.item_code, placed_on=getdate())

		profile = get_customer(self.customer)

		self.assertEqual(profile["days_between_orders"], 10)
		self.assertEqual(profile["first_order"], add_days(getdate(), -20))
		self.assertEqual(profile["last_order"], getdate())

	def test_a_customer_without_orders_reports_no_dates(self):
		profile = get_customer(self.customer)

		self.assertEqual(profile["orders"], 0)
		self.assertEqual(profile["spend"], 0)
		self.assertIsNone(profile["first_order"])
		self.assertIsNone(profile["last_order"])
		self.assertIsNone(profile["payment_mode"])
		self.assertEqual(profile["top_products"], [])

	def test_top_products_are_ranked_by_units_and_capped(self):
		item_codes = [make_item(image="/files/zz-profile.png") for _ in range(TOP_PRODUCT_LIMIT + 1)]
		for index, item_code in enumerate(item_codes):
			make_webshop_order(self.customer, item_code, qty=len(item_codes) - index)

		top_products = get_customer(self.customer)["top_products"]

		self.assertEqual(len(top_products), TOP_PRODUCT_LIMIT)
		self.assertEqual([row["item_code"] for row in top_products], item_codes[:TOP_PRODUCT_LIMIT])
		self.assertEqual([row["units"] for row in top_products], [6.0, 5.0, 4.0, 3.0, 2.0])
		self.assertAlmostEqual(top_products[0]["spend"], ITEM_RATE * 6)
		self.assertEqual(top_products[0]["image"], "/files/zz-profile.png")
		self.assertEqual(top_products[0]["name"], frappe.db.get_value("Item", item_codes[0], "item_name"))
		self.assertEqual(top_products[0]["product"], item_codes[0])

	def test_a_variant_links_to_its_template_product(self):
		template = make_item()
		frappe.db.set_value("Item", template, "has_variants", 1)
		variant = make_item()
		frappe.db.set_value("Item", variant, "variant_of", template)
		make_webshop_order(self.customer, variant)

		self.assertEqual(get_customer(self.customer)["top_products"][0]["product"], template)

	def test_units_count_every_order_line(self):
		make_webshop_order(self.customer, self.item_code, qty=3)
		make_webshop_order(self.customer, make_item(), qty=4)

		self.assertAlmostEqual(get_customer(self.customer)["units"], 7)

	def test_payment_mode_is_the_one_used_most(self):
		make_webshop_order(self.customer, self.item_code, payment_mode="COD")
		make_webshop_order(self.customer, self.item_code, payment_mode="COD")
		make_webshop_order(self.customer, self.item_code, payment_mode="Stripe")

		self.assertEqual(get_customer(self.customer)["payment_mode"], "COD")

	def test_spend_by_month_is_a_full_year_oldest_first(self):
		make_webshop_order(self.customer, self.item_code)

		spend_by_month = get_customer(self.customer)["spend_by_month"]

		self.assertEqual(len(spend_by_month), SPEND_CHART_MONTHS)
		expected_labels = [
			formatdate(add_months(getdate(), -offset), "MMM")
			for offset in reversed(range(SPEND_CHART_MONTHS))
		]
		self.assertEqual([row["label"] for row in spend_by_month], expected_labels)
		self.assertAlmostEqual(spend_by_month[-1]["spend"], ITEM_RATE)
		self.assertEqual([row["spend"] for row in spend_by_month[:-1]], [0.0] * (SPEND_CHART_MONTHS - 1))

	def test_an_order_older_than_the_chart_window_still_counts_towards_spend(self):
		make_webshop_order(self.customer, self.item_code, placed_on=add_months(getdate(), -18))

		profile = get_customer(self.customer)

		self.assertAlmostEqual(profile["spend"], ITEM_RATE)
		self.assertEqual([row["spend"] for row in profile["spend_by_month"]], [0.0] * SPEND_CHART_MONTHS)

	def test_acquisition_is_none_without_an_analytics_event(self):
		make_webshop_order(self.customer, self.item_code)

		self.assertIsNone(get_customer(self.customer)["acquisition"])

	def test_acquisition_comes_off_the_first_order(self):
		first_order = make_webshop_order(self.customer, self.item_code, placed_on=add_days(getdate(), -5))
		latest_order = make_webshop_order(self.customer, self.item_code)
		self.make_analytics_event(first_order.name, "newsletter", "spring")
		self.make_analytics_event(latest_order.name, "instagram", "summer")

		self.assertEqual(
			get_customer(self.customer)["acquisition"], {"source": "newsletter", "campaign": "spring"}
		)

	def test_an_untagged_analytics_event_is_not_an_acquisition(self):
		order = make_webshop_order(self.customer, self.item_code)
		self.make_analytics_event(order.name, None, None)

		self.assertIsNone(get_customer(self.customer)["acquisition"])

	def test_the_default_address_is_returned_as_lines(self):
		self.make_address(city="Bengaluru", is_primary_address=0, address_line1="12 Side Street")
		self.make_address(city="Mumbai", is_primary_address=1, address_line1="7 Main Street")

		profile = get_customer(self.customer)

		self.assertEqual(profile["city"], "Mumbai")
		self.assertEqual(profile["address"], "7 Main Street\nMumbai\nIndia")

	def test_a_customer_without_an_address_reports_none(self):
		profile = get_customer(self.customer)

		self.assertIsNone(profile["city"])
		self.assertIsNone(profile["address"])

	def make_analytics_event(self, order_id, utm_source, utm_campaign):
		return frappe.get_doc(
			{
				"doctype": "Storefront Analytics Event",
				"event": "purchase",
				"session_id": frappe.generate_hash(length=10),
				"order_id": order_id,
				"utm_source": utm_source,
				"utm_campaign": utm_campaign,
			}
		).insert(ignore_permissions=True)

	def make_address(self, city, is_primary_address, address_line1):
		address = frappe.get_doc(
			{
				"doctype": "Address",
				"address_title": f"ZZ Profile {frappe.generate_hash(length=6)}",
				"address_type": "Billing",
				"address_line1": address_line1,
				"city": city,
				"country": "India",
				"is_primary_address": is_primary_address,
				"links": [{"link_doctype": "Customer", "link_name": self.customer}],
			}
		)
		address.flags.ignore_permissions = True
		return address.insert()


class TestCustomerNote(IntegrationTestCase):
	def setUp(self):
		self.addCleanup(frappe.db.rollback)
		self.addCleanup(frappe.set_user, "Administrator")
		self.customer = make_customer()

	def test_a_note_round_trips_through_the_profile(self):
		saved = save_customer_note(self.customer, "Prefers a call before delivery.")

		self.assertEqual(saved, "Prefers a call before delivery.")
		self.assertEqual(get_customer(self.customer)["note"], "Prefers a call before delivery.")

	def test_an_unwritten_note_reads_as_an_empty_string(self):
		self.assertEqual(get_customer(self.customer)["note"], "")

	def test_a_website_user_cannot_write_a_note(self):
		frappe.set_user(make_website_user())

		with self.assertRaises(frappe.PermissionError):
			save_customer_note(self.customer, "tampered")
