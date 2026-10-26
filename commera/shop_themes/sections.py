import json
import os

import frappe
from frappe import _
from frappe.utils.data import cint, flt
from jinja2 import pass_context
from markupsafe import Markup, escape

import commera.sdk
from commera.shop_themes.doctype.shop_theme.shop_theme import get_render_theme_context
from commera.shop_themes.theme_resolver import find_theme_file

LAYOUT_CACHE_PREFIX = "commera:theme_layout:"
TEXT_TYPES = frozenset({"text", "textarea", "url", "image"})
DEFAULT_MAX_BLOCKS = 50

theme_json_files = {}


def get_theme_json(theme_dirs, relative_path):
	path = find_theme_file(theme_dirs, relative_path)
	if not path:
		return None

	modified_time = os.path.getmtime(path)
	cached = theme_json_files.get(path)
	if cached and cached[0] == modified_time:
		return cached[1]

	# nosemgrep: frappe-semgrep-rules.rules.security.frappe-security-file-traversal
	with open(path) as json_file:
		data = json.load(json_file)
	theme_json_files[path] = (modified_time, data)
	return data


def get_section_schema(theme_dirs, section_type):
	if not isinstance(section_type, str) or not section_type.replace("_", "").isalnum():
		return None
	return get_theme_json(theme_dirs, f"sections/{section_type}.json")


def get_page_layout(theme_name, theme_dirs, page):
	cache_key = f"{LAYOUT_CACHE_PREFIX}{theme_name}:{page}"
	cached = frappe.cache.get_value(cache_key)
	if cached is None:
		published_layout = frappe.db.get_value(
			"Theme Layout", {"theme": theme_name, "page": page}, "published_layout"
		)
		cached = {"layout": frappe.parse_json(published_layout) if published_layout else None}
		frappe.cache.set_value(cache_key, cached)

	return cached["layout"] or get_theme_json(theme_dirs, f"layouts/{page}.json") or {"sections": []}


def clear_layout_cache(theme_name, page):
	frappe.cache.delete_value(f"{LAYOUT_CACHE_PREFIX}{theme_name}:{page}")


def get_text(value):
	if not isinstance(value, dict):
		return value
	return value.get(frappe.local.lang) or value.get("en") or next(iter(value.values()), "")


def get_setting_value(setting, value):
	setting_type = setting.get("type")
	if setting_type in TEXT_TYPES:
		return escape(get_text(value) or "")
	if setting_type == "number":
		return flt(value)
	if setting_type == "checkbox":
		return bool(cint(value))
	if setting_type == "products":
		return [str(code) for code in value or []]
	return value


def get_settings(schema_settings, saved_settings):
	saved_settings = saved_settings if isinstance(saved_settings, dict) else {}
	return frappe._dict(
		{
			setting["id"]: get_setting_value(
				setting, saved_settings.get(setting["id"], setting.get("default"))
			)
			for setting in schema_settings or []
		}
	)


def get_section(schema, saved_section):
	block_schemas = schema.get("blocks") or {}
	blocks = [
		frappe._dict(
			id=block.get("id"),
			type=block.get("type"),
			settings=get_settings(block_schemas[block.get("type")].get("settings"), block.get("settings")),
		)
		for block in saved_section.get("blocks") or []
		if isinstance(block, dict) and block.get("type") in block_schemas
	]
	return frappe._dict(
		id=saved_section.get("id"),
		type=saved_section.get("type"),
		settings=get_settings(schema.get("settings"), saved_section.get("settings")),
		blocks=blocks[: cint(schema.get("max_blocks")) or DEFAULT_MAX_BLOCKS],
	)


@pass_context
def render_layout(context, page):
	theme_context = get_render_theme_context()
	theme_dirs = theme_context["dirs"]
	if not theme_dirs:
		return ""

	layout = get_page_layout(theme_context["theme_name"], theme_dirs, page)
	section_context = {**context.get_all(), "commera": commera.sdk}
	html = [
		render_section(context.environment, theme_dirs, saved_section, section_context)
		for saved_section in layout.get("sections") or []
		if isinstance(saved_section, dict) and not saved_section.get("hidden")
	]
	return Markup("\n".join(html))


def render_section(environment, theme_dirs, saved_section, section_context):
	schema = get_section_schema(theme_dirs, saved_section.get("type"))
	if not schema:
		return ""

	try:
		section = get_section(schema, saved_section)
		template = environment.get_template(f"theme://sections/{section.type}.html")
		return template.render({**section_context, "section": section})
	except Exception:
		frappe.log_error(title=_("Theme section {0} failed to render").format(saved_section.get("type")))
		return ""


def validate_layout(theme_dirs, layout):
	if not isinstance(layout, dict) or not isinstance(layout.get("sections"), list):
		frappe.throw(_('A layout must be an object with a "sections" list.'))

	section_ids = set()
	for section in layout["sections"]:
		validate_entry(section, section_ids, _("Section"))
		schema = get_section_schema(theme_dirs, section["type"])
		if not schema:
			frappe.throw(_("Section type {0} does not exist in this theme.").format(section["type"]))
		if not isinstance(section.get("hidden", False), bool):
			frappe.throw(_("Section {0}: hidden must be true or false.").format(section["id"]))
		validate_settings(schema.get("settings"), section.get("settings"), section["id"])
		validate_blocks(schema, section)


def validate_blocks(schema, section):
	blocks = section.get("blocks") or []
	if not isinstance(blocks, list):
		frappe.throw(_("Section {0}: blocks must be a list.").format(section["id"]))

	max_blocks = cint(schema.get("max_blocks")) or DEFAULT_MAX_BLOCKS
	if len(blocks) > max_blocks:
		frappe.throw(_("Section {0} allows at most {1} blocks.").format(section["id"], max_blocks))

	block_schemas = schema.get("blocks") or {}
	block_ids = set()
	for block in blocks:
		validate_entry(block, block_ids, _("Block"))
		if block["type"] not in block_schemas:
			frappe.throw(
				_("Section {0} does not allow blocks of type {1}.").format(section["id"], block["type"])
			)
		validate_settings(block_schemas[block["type"]].get("settings"), block.get("settings"), block["id"])


def validate_entry(entry, seen_ids, label):
	if not isinstance(entry, dict) or not entry.get("id") or not entry.get("type"):
		frappe.throw(_("{0} entries need an id and a type.").format(label))
	if entry["id"] in seen_ids:
		frappe.throw(_("{0} id {1} is used twice.").format(label, entry["id"]))
	seen_ids.add(entry["id"])


def validate_settings(schema_settings, saved_settings, owner_id):
	saved_settings = saved_settings or {}
	if not isinstance(saved_settings, dict):
		frappe.throw(_("{0}: settings must be an object.").format(owner_id))

	settings_by_id = {setting["id"]: setting for setting in schema_settings or []}
	for setting_id, value in saved_settings.items():
		setting = settings_by_id.get(setting_id)
		if not setting:
			frappe.throw(_("{0}: unknown setting {1}.").format(owner_id, setting_id))
		if not is_valid_value(setting.get("type"), value):
			frappe.throw(_("{0}: setting {1} has the wrong type.").format(owner_id, setting_id))


def is_valid_value(setting_type, value):
	if value is None:
		return True
	if setting_type in TEXT_TYPES:
		if isinstance(value, dict):
			return all(isinstance(text, str) for text in value.values())
		return isinstance(value, str)
	if setting_type == "number":
		return isinstance(value, int | float) and not isinstance(value, bool)
	if setting_type == "checkbox":
		return isinstance(value, bool)
	if setting_type == "products":
		return isinstance(value, list) and all(isinstance(code, str) for code in value)
	return False
