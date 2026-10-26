from pathlib import Path

import click
import frappe
from frappe.utils import strip_html

from commera.scaffold import AppScaffold
from commera.shop_themes.doctype.shop_theme.shop_theme import get_theme_export_dir


class ThemeScaffold(AppScaffold):
	def add_theme(self, theme_name: str, theme_type: str, parent_theme: str) -> list[tuple[str, str]]:
		if frappe.db.exists("Shop Theme", theme_name):
			raise click.ClickException(f"Shop Theme {theme_name} already exists; pick another name")

		theme = frappe.new_doc("Shop Theme")
		theme.update(
			{
				"theme_name": theme_name,
				"theme_type": theme_type,
				"parent_theme": parent_theme,
				"module": frappe.get_module_list(self.app)[0],
				"is_standard": 1,
			}
		)
		theme.flags.scaffold = True
		try:
			theme.insert()
		except frappe.ValidationError as error:
			raise click.ClickException(strip_html(str(error)))

		self.changes.extend(theme.flags.scaffold_changes)
		slug = frappe.scrub(theme_name)
		export_path = Path(get_theme_export_dir(theme.module, slug), f"{slug}.json")
		if export_path.exists():
			self.changes.append(("created", self.get_relative_path(export_path)))
		return self.changes
