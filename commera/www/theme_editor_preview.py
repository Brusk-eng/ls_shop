# Copyright (c) 2026, company@bwhstudios.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import escape_html
from markupsafe import Markup

from commera.shop_themes.chrome_preview import TRACKING_BLANKED_BLOCKS, render_page_preview
from commera.shop_themes.doctype.shop_theme.shop_theme import get_theme_context, resolve_active_theme
from commera.shop_themes.sections import SECTION_GROUPS
from commera.shop_themes.theme_resolver import find_theme_file

no_cache = True

PREVIEW_LANGUAGES = ("en", "ar")
EDITOR_ROLES = ("System Manager", "Website Manager")

EDITOR_HEAD_HTML = Markup(
	"<style>[data-commera-section]{display:contents}</style>"
	'<script defer src="/assets/commera/js/theme_editor_preview.js"></script>'
)


def get_context(context):
	frappe.only_for(EDITOR_ROLES)

	theme = requested_theme()
	page = requested_page(theme)
	layouts = requested_layouts(page)

	lang = frappe.form_dict.get("lang")
	if lang not in PREVIEW_LANGUAGES:
		lang = frappe.local.lang or "en"

	# The themed page reads its language off frappe.lang, so the ?lang switch must move it here.
	frappe.local.lang = lang

	head_html = ""
	if layouts:
		frappe.local.theme_editor_preview = frappe._dict(layouts=layouts)
		head_html = EDITOR_HEAD_HTML

	try:
		rendered = render_page_preview(
			f"pages/{page}.html", TRACKING_BLANKED_BLOCKS, theme_name=theme, head_html=head_html
		)
	finally:
		frappe.local.theme_editor_preview = None

	if rendered:
		context.rendered_html = rendered
		return

	# No theme to render, or one that ships no home page: the pane says so rather than framing a 404.
	context.rendered_html = f"""<!DOCTYPE html>
<html lang="{escape_html(lang)}">
<head>
<meta charset="UTF-8">
<link rel="stylesheet" href="/assets/commera/css/tailwind.css">
</head>
<body class="grid min-h-screen place-items-center bg-gray-50 p-6 text-center text-gray-500">
<p>{escape_html(no_preview_message(theme))}</p>
</body>
</html>"""


def requested_theme():
	"""The installed theme the pane asked for, or None to fall back to the live one."""
	theme = frappe.form_dict.get("theme")
	if not theme or not frappe.db.exists("Shop Theme", theme):
		return None

	return theme


def requested_page(theme):
	page = frappe.form_dict.get("page") or "index"
	if page == "index":
		return page
	if (
		not isinstance(page, str)
		or not page.replace("_", "").replace("-", "").isalnum()
		or not find_theme_file(
			get_theme_context(theme or resolve_active_theme())["dirs"], f"layouts/{page}.json"
		)
	):
		frappe.throw(_("This theme has no {0} page to preview.").format(page), frappe.DoesNotExistError)

	return page


def requested_layouts(page):
	parts = {page: "layout", **{group: f"{group}_layout" for group in SECTION_GROUPS}}
	return {
		part: requested_layout(field)
		for part, field in parts.items()
		if frappe.form_dict.get(field) is not None
	}


def requested_layout(field):
	layout = frappe.parse_json(frappe.form_dict.get(field))
	if not isinstance(layout, dict) or not isinstance(layout.get("sections"), list):
		frappe.throw(_('A layout must be an object with a "sections" list.'))

	return layout


def no_preview_message(theme):
	if theme:
		return frappe._("{0} has no home page to preview.").format(theme)

	return frappe._("The live theme has no home page to preview.")
