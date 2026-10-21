import secrets

import frappe
from frappe import _
from frappe.utils.data import cint, cstr

from commera.plugin_events import get_handlers, handle_hook_error

MAX_GENERATED_CODES = 5000
# No 0/O or 1/I: a code read off a receipt must not be mistyped.
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def normalize_code(code: str | None) -> str:
	return cstr(code).strip().upper()


def get_code_discount(code: str) -> str | None:
	return frappe.get_cached_value("Commera Discount Code", normalize_code(code), "discount")


def add_code(discount: str, code: str, is_generated: bool = False) -> str:
	code = normalize_code(code)
	if not code or len(code) > 64 or any(character.isspace() for character in code):
		frappe.throw(_("A code needs 1 to 64 characters and no spaces."))
	if frappe.db.exists("Commera Discount Code", code):
		frappe.throw(_("The code {0} is already in use.").format(code), frappe.DuplicateEntryError)
	frappe.get_doc(
		{"doctype": "Commera Discount Code", "code": code, "discount": discount, "is_generated": is_generated}
	).insert(ignore_permissions=True)
	return code


def generate_codes(discount: str, count: int, prefix: str = "") -> list[str]:
	count = cint(count)
	if not 0 < count <= MAX_GENERATED_CODES:
		frappe.throw(_("Generate between 1 and {0} codes at a time.").format(MAX_GENERATED_CODES))

	prefix = normalize_code(prefix)
	codes = []
	while len(codes) < count:
		code = prefix + "".join(secrets.choice(CODE_ALPHABET) for _index in range(8))
		if not frappe.db.exists("Commera Discount Code", code):
			codes.append(add_code(discount, code, is_generated=True))
	return codes


def get_discount_code_refusal(quotation, code: str) -> str | None:
	for handler in get_handlers("commera_hooks", "validate_discount_code"):
		reason = None
		with handle_hook_error(
			"validate_discount_code", handler, quotation, bool(quotation.flags.strict_plugin_fees)
		):
			reason = frappe.get_attr(handler)(quotation, code)
			if reason and not isinstance(reason, str):
				raise TypeError(
					f'commera_hooks["validate_discount_code"] must return a str or None, got {reason!r}'
				)
		if reason:
			return reason
	return None
