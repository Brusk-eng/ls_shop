# Copyright (c) 2026, company@bwhstudios.com and Contributors

import frappe
from frappe.tests import IntegrationTestCase

from commera.api.payments import refuse_payment


class TestCheckoutRefusalLogging(IntegrationTestCase):
	def setUp(self):
		frappe.cache.delete_value("deferred_insert:Error Log")
		self.addCleanup(frappe.cache.delete_value, "deferred_insert:Error Log")

	def queued_error_logs(self):
		from frappe.deferred_insert import queue_prefix

		return frappe.cache.lrange(f"{queue_prefix}Error Log", 0, -1)

	def test_a_refusal_is_queued_for_the_error_log_and_still_throws(self):
		with self.assertRaises(frappe.ValidationError):
			refuse_payment("Please select a valid payment mode.", "SAL-QTN-ZZ-0001", requested="Razorpay")

		queued = frappe.as_unicode(b"".join(self.queued_error_logs()))
		self.assertIn("Checkout refused: Please select a valid payment mode.", queued)
		self.assertIn("SAL-QTN-ZZ-0001", queued)
		self.assertIn("Razorpay", queued)
