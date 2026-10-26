# $theme_name

## Theme settings

Theme settings are the values a merchant can change without code: colours, fonts, corner radius, logo, social links.
They live in one Settings doctype per theme.

1. Open the Shop Theme record for $theme_name in Desk and click **Scaffold Theme Settings**.
   This creates the Single doctype `$theme_name Settings`.
2. Add fields to that doctype. The merchant edits them on the Theme screen in `/commera`.

A theme without its own Settings doctype uses its parent's.

### Read a setting in a template

Every page, section and block gets the settings as `theme`:

```jinja
<h1>{{ theme.tagline }}</h1>
{% for link in theme.social_links %}<a href="{{ link.url }}">{{ link.label }}</a>{% endfor %}
```

A field that has no value is `None`.

### Colours, fonts and radius become CSS variables

`{{ format_shop_theme_css() }}` in `<head>` writes these fields as variables on `:root`.
The name is `--theme-` plus the fieldname, with `_` changed to `-`.

| Field | Example | Variable |
| --- | --- | --- |
| Any field of type Color | `primary_color` = `#0f766e` | `--theme-primary-color: #0f766e` |
| Data, Select or Autocomplete field whose name ends in `_font` | `body_font` = `Inter` | `--theme-body-font: "Inter"` |
| Int or Float field named `radius` or ending in `_radius` | `button_radius` = `8` | `--theme-button-radius: 8px` |
| Data field named `radius` or ending in `_radius` | `card_radius` = `1.5rem` | `--theme-card-radius: 1.5rem` |

A Data field named `accent_color` is not a colour: only the Color field type counts.
An empty or invalid value writes no variable. A colour must be a hex value, a font
name may only contain letters, digits, spaces, `-` and `_`, and a radius must be zero or more, in `px`, `rem`, `em` or `%`.
Give each variable a fallback in your CSS:

```css
.button { background: var(--theme-primary-color, #111827); border-radius: var(--theme-button-radius, 6px); }
body { font-family: var(--theme-body-font), system-ui, sans-serif; }
```
