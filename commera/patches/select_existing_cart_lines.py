import frappe


def execute():
	cart_line = frappe.qb.DocType("Commera Cart Line")
	frappe.qb.update(cart_line).set(cart_line.selected, 1).run()
