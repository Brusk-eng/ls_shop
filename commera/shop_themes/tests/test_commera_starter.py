import os
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

import commera.sdk
from commera.shop_themes.doctype.shop_theme.shop_theme import render_theme_context
from commera.shop_themes.sections import get_theme_json, validate_layout
from commera.shop_themes.theme_resolver import ThemePageRenderer, build_base_context

STARTER = "Commera Starter"
STARTER_DIR = os.path.join(frappe.get_app_path("commera"), "themes", "commera_starter")
PRODUCT_CARD = {
	"id": "ZZ-STARTER-CARD",
	"handle": "zz-starter-card",
	"title": "ZZ Starter Linen Shirt",
	"vendor": None,
	"product_type": None,
	"color": None,
	"image": None,
	"hover_image": None,
	"currency": "INR",
	"price": 1999.0,
	"compare_at_price": 2499.0,
	"available": True,
	"rating": {"average": 0, "count": 0},
	"updated_at": None,
}


class IntegrationTestCommeraStarter(IntegrationTestCase):
	def setUp(self):
		self.theme_context = {
			"theme_name": STARTER,
			"theme_type": "Sections",
			"names": [STARTER],
			"dirs": [STARTER_DIR],
			"apps": {STARTER: "commera"},
			"settings_doctype": None,
		}
		frappe.cache.delete_value(f"commera:theme_layout:{STARTER}:index")
		frappe.db.delete("Theme Layout", {"theme": STARTER})

	def render_home(self, products):
		with (
			patch.object(commera.sdk.catalog, "list_products", return_value={"products": products}),
			render_theme_context(self.theme_context),
		):
			renderer = ThemePageRenderer("index")
			renderer.theme_dirs = [STARTER_DIR]
			renderer.template_path = "pages/index.html"
			return renderer.render_with_theme_loader(build_base_context(None))

	def test_the_home_layout_passes_the_layout_checks(self):
		with render_theme_context(self.theme_context):
			validate_layout(self.theme_context, get_theme_json([STARTER_DIR], "layouts/index.json"))

	def test_the_home_page_renders_every_section_from_the_theme_defaults(self):
		html = self.render_home([PRODUCT_CARD])

		for expected in (
			"Clothes made to be lived in.",
			"/assets/commera/themes/commera_starter/images/banner-banner-media2.webp",
			"New arrivals",
			"ZZ Starter Linen Shirt",
			commera.sdk.format.money(1999, "INR"),
			commera.sdk.format.money(2499, "INR"),
			"Basics",
			"Read the journal",
			"Letters from the studio",
		):
			self.assertIn(expected, html)

	def test_featured_products_is_left_out_when_its_source_has_no_products(self):
		html = self.render_home([])

		self.assertNotIn("New arrivals", html)
		self.assertIn("Letters from the studio", html)
