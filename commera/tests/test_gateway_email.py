# Copyright (c) 2026, company@bwhstudios.com and Contributors

import frappe
from frappe.tests import IntegrationTestCase

from commera.api.payments import get_gateway_email


class TestGatewayCustomerEmail(IntegrationTestCase):
	def test_a_real_address_on_the_contact_is_used(self):
		self.assertEqual(get_gateway_email("shopper@example.com"), "shopper@example.com")

	def test_a_desk_username_falls_back_to_the_users_own_email(self):
		self.assertEqual(
			get_gateway_email("Administrator"), frappe.db.get_value("User", "Administrator", "email")
		)

	def test_a_guest_sends_no_email_rather_than_the_guest_placeholder(self):
		frappe.set_user("Guest")
		self.addCleanup(frappe.set_user, "Administrator")

		self.assertIsNone(get_gateway_email(""))
