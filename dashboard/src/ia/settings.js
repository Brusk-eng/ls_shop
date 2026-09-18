// Settings is a route, not local state: /commera/settings/payments is a real URL
// (see the record in router.js), so `settings.open` and `settings.tab` are derived
// from it in ia/settingsRoute rather than kept as a second copy that can drift.
// Re-exported here because this is still the door the rest of the app knocks on.
export { openSettings, settings } from './settingsRoute'

// The dialog's sidebar, in its own order, as data — so the search palette can
// offer every tab without a second hand-maintained copy drifting out of sync
// (it already called `apps` "Apps and channels" long after the sidebar renamed
// it). `value` must stay identical to AppSettingsDialog's SettingsNavItem
// values; the labels and icons mirror what that sidebar shows.
//
// `keywords` carries the weight here: the palette matches a plain substring
// per field with no tokenising or stemming, so a merchant who types the
// provider's name rather than ours only lands if that exact word is listed.
export const SETTINGS_TABS = [
  {
    value: 'general',
    label: 'General',
    icon: 'lucide-store',
    keywords: ['store', 'shop', 'name', 'address', 'currency', 'timezone', 'contact'],
  },
  {
    value: 'appearance',
    label: 'Appearance',
    icon: 'lucide-sun-moon',
    keywords: ['theme', 'dark', 'light', 'colour', 'color', 'logo', 'brand'],
  },
  {
    value: 'payments',
    label: 'Payments',
    icon: 'lucide-credit-card',
    keywords: ['stripe', 'razorpay', 'upi', 'card', 'keys', 'gateway', 'checkout', 'cash on delivery', 'cod', 'refund'],
  },
  {
    value: 'shipping',
    label: 'Shipping',
    icon: 'lucide-truck',
    keywords: ['carrier', 'shiprocket', 'aftership', 'rates', 'courier', 'delivery', 'tracking', 'free shipping'],
  },
  {
    value: 'locations',
    label: 'Pickup locations',
    icon: 'lucide-map-pin',
    keywords: ['pickup', 'warehouse', 'collect', 'store pickup', 'branch', 'address'],
  },
  {
    value: 'apps',
    label: 'Analytics',
    icon: 'lucide-chart-line',
    keywords: ['ga4', 'google analytics', 'pixel', 'tracking', 'meta', 'apps', 'integrations'],
  },
  {
    value: 'advanced',
    label: 'Advanced',
    icon: 'lucide-sliders-horizontal',
    keywords: ['developer', 'api', 'reset', 'danger', 'cache', 'debug'],
  },
]
