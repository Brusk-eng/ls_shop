import io
from contextlib import redirect_stdout
from pathlib import Path

import click
import frappe
from frappe.modules.export_file import write_document_file
from frappe.utils import strip_html

from commera.scaffold import AppScaffold
from commera.shop_themes.doctype.shop_theme.shop_theme import (
	DEFAULT_THEME_APP,
	DEFAULT_THEME_MODULE,
	get_theme_export_dir,
	scaffold_theme,
	validate_theme_name,
)


class ThemeScaffold(AppScaffold):
	allow_host_app = True

	def get_theme_module(self) -> str:
		if self.app == DEFAULT_THEME_APP:
			return DEFAULT_THEME_MODULE
		return frappe.get_module_list(self.app)[0]

	def get_relative_path(self, path: Path) -> str:
		return str(path.relative_to(Path(frappe.get_app_path(self.app)).parent))

	def is_installed(self) -> bool:
		return self.app in frappe.get_installed_apps()

	def add_theme(self, theme_name: str, theme_type: str, parent_theme: str) -> list[tuple[str, str]]:
		if frappe.db.exists("Shop Theme", theme_name):
			raise click.ClickException(f"Shop Theme {theme_name} already exists; pick another name")

		theme = frappe.new_doc("Shop Theme")
		theme.update(
			{
				"theme_name": theme_name,
				"theme_type": theme_type,
				"parent_theme": parent_theme,
				"module": self.get_theme_module(),
				"is_standard": 1,
			}
		)
		try:
			if self.is_installed():
				self.insert_theme(theme)
			else:
				self.write_theme_files(theme)
		except frappe.ValidationError as error:
			raise click.ClickException(strip_html(str(error)))

		slug = frappe.scrub(theme_name)
		export_path = Path(get_theme_export_dir(theme.module, slug), f"{slug}.json")
		if export_path.exists():
			self.changes.append(("created", self.get_relative_path(export_path)))
		return self.changes

	def insert_theme(self, theme):
		theme.flags.scaffold = True
		theme.insert()
		self.changes.extend(theme.flags.scaffold_changes)

	def write_theme_files(self, theme):
		validate_theme_name(theme.theme_name)
		if not frappe.db.exists("Shop Theme", theme.parent_theme):
			frappe.throw(frappe._("Shop Theme {0} does not exist on this site").format(theme.parent_theme))
		theme.validate_unique_slug()
		theme.validate_parent_theme_type()

		theme.name = theme.theme_name
		self.changes.extend(scaffold_theme(theme.theme_name, theme.module, theme.theme_type, app=self.app))
		with redirect_stdout(io.StringIO()):
			write_document_file(theme, record_module=theme.module)
