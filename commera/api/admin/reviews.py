# Copyright (c) 2026, company@bwhstudios.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils.data import cint, cstr, now_datetime

MAX_REPLY_LENGTH = 2000
PAGE_LENGTH = 20

# Caps the IN lists the batched product/shopper reads build from a page.
MAX_PAGE_LENGTH = 100


@frappe.whitelist()
def get_reviews(
	tab: str = "unpublished", search: str | None = None, start: int = 0, page_length: int = PAGE_LENGTH
):
	"""The moderation queue. `tab` picks Published or Unpublished — approve-first means
	Unpublished is the merchant's normal working queue, not an error state."""
	frappe.has_permission("Product Review", ptype="read", throw=True)

	filters = {"is_published": 1 if tab == "published" else 0}
	or_filters = (
		[
			["review_title", "like", f"%{search}%"],
			["comment", "like", f"%{search}%"],
			["owner", "like", f"%{search}%"],
		]
		if search
		else None
	)

	if or_filters:
		total = len(frappe.get_all("Product Review", filters=filters, or_filters=or_filters, pluck="name"))
	else:
		total = frappe.db.count("Product Review", filters)

	review_rows = frappe.get_all(
		"Product Review",
		filters=filters,
		or_filters=or_filters,
		fields=[
			"name",
			"variant",
			"rating",
			"review_title",
			"comment",
			"verified_purchase",
			"is_published",
			"owner",
			"creation",
		],
		order_by="creation desc",
		start=cint(start),
		page_length=min(cint(page_length) or PAGE_LENGTH, MAX_PAGE_LENGTH),
	)
	if not review_rows:
		return {"reviews": [], "total": total}

	product_by_variant = read_products([row.variant for row in review_rows])
	shopper_by_email = read_shoppers([row.owner for row in review_rows])

	return {
		"reviews": [
			{
				"name": row.name,
				"variant": row.variant,
				"product": product_by_variant.get(row.variant),
				"rating": cint(row.rating),
				"review_title": row.review_title,
				"comment": row.comment,
				"verified_purchase": bool(cint(row.verified_purchase)),
				"shopper": shopper_by_email.get(row.owner, row.owner),
				"is_published": bool(cint(row.is_published)),
				"creation": row.creation,
			}
			for row in review_rows
		],
		"total": total,
	}


def read_products(variant_names: list) -> dict:
	"""One variant's display name + storefront route, batched across a page of reviews."""
	variant_names = list({name for name in variant_names if name})
	if not variant_names:
		return {}
	return {
		row.name: {
			"variant": row.name,
			"item_style": row.item_style,
			"name": row.display_name,
			"route": row.route,
		}
		for row in frappe.get_all(
			"Style Attribute Variant",
			filters={"name": ["in", variant_names]},
			fields=["name", "item_style", "display_name", "route"],
		)
	}


def read_shoppers(emails: list) -> dict:
	"""One reviewer's display name per page, batched — never a get_value per row."""
	emails = list({email for email in emails if email})
	if not emails:
		return {}
	return {
		row.name: row.full_name
		for row in frappe.get_all("User", filters={"name": ["in", emails]}, fields=["name", "full_name"])
	}


def build_review_detail(name: str) -> dict:
	"""The whole review-detail screen in one shape, shared by get_review and the two
	moderation writes so a publish/reply lands the caller straight back on fresh data."""
	review = frappe.get_doc("Product Review", name)

	product = read_products([review.variant]).get(review.variant)
	shopper_name = read_shoppers([review.owner]).get(review.owner, review.owner)

	return {
		"name": review.name,
		"variant": review.variant,
		"product": product,
		"rating": cint(review.rating),
		"review_title": review.review_title,
		"comment": review.comment,
		"verified_purchase": bool(cint(review.verified_purchase)),
		# Read straight off the stored fields — never re-run the S1-3 purchase join here.
		"sales_order": review.sales_order,
		"is_published": bool(cint(review.is_published)),
		"shopper": {"email": review.owner, "name": shopper_name},
		"seller_reply": review.seller_reply,
		"replied_on": review.replied_on,
		"replied_by": review.replied_by,
		"creation": review.creation,
	}


@frappe.whitelist()
def get_review(name: str):
	"""One review's detail screen: the review, its product, its shopper, any existing
	reply, and the order link — all read off the stored record, never recomputed."""
	frappe.has_permission("Product Review", doc=name, ptype="read", throw=True)
	return build_review_detail(name)


@frappe.whitelist()
def set_published(name: str, published: bool | int):
	"""The moderation write. Product Review's own on_update already recomputes the
	variant's average_rating/review_count when is_published flips — nothing to redo here."""
	frappe.has_permission("Product Review", doc=name, ptype="write", throw=True)

	review = frappe.get_doc("Product Review", name)
	review.is_published = cint(published)
	review.save()

	return build_review_detail(name)


@frappe.whitelist()
def save_reply(name: str, reply: str):
	"""Stamps the reply and who/when. get_reviews (S1-6) already returns seller_reply
	unconditionally, so the reply is live on the storefront the moment this saves."""
	frappe.has_permission("Product Review", doc=name, ptype="write", throw=True)

	reply = cstr(reply).strip()
	if not reply:
		frappe.throw(_("Reply cannot be empty"))
	if len(reply) > MAX_REPLY_LENGTH:
		frappe.throw(_("Reply is too long"))

	review = frappe.get_doc("Product Review", name)
	review.seller_reply = reply
	review.replied_on = now_datetime()
	review.replied_by = frappe.session.user
	review.save()

	return build_review_detail(name)
