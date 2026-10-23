from urllib.parse import urlencode

import frappe
from frappe import _
from frappe.utils.data import cstr

from commera.guest import is_guest

no_cache = True


def get_context(context):
	"""A signed-in browser confirms before a storefront's guest cart merges into its account cart."""
	code = cstr(frappe.form_dict.get("code"))
	if is_guest():
		frappe.local.flags.redirect_location = (
			f"/api/method/commera.api.storefront.cart.open_checkout?{urlencode({'code': code})}"
		)
		raise frappe.Redirect

	context.code = code
	context.signed_in_user = frappe.session.user
	context.cart_url = f"/{frappe.local.lang}/cart"
	context.title = _("Add to Your Cart")
	context.show_breadcrumb = False
