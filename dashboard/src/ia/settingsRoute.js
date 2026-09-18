import { computed, shallowRef } from 'vue'

// Settings is a dialog *and* a URL: /commera/settings/payments is a real route,
// so a merchant can send a colleague straight to the screen they mean and the
// browser's Back button closes the dialog. The route renders nothing (see the
// record in router.js) — the page it was opened over stays mounted behind it.
export const SETTINGS_ROUTE_NAME = 'Settings'

export const DEFAULT_SETTINGS_TAB = 'general'

// The router instance, handed over by router.js once it exists, rather than
// imported: router.js needs the two names above to declare the record, and an
// import back the other way would make the pair a cycle whose winner depends on
// which module the bundler happens to evaluate first.
let router = null

// The last location that was not the dialog. App.vue keeps rendering it behind
// the modal, and closing returns to it. It stays null when the URL was pasted
// cold: there is no page behind, and closing falls back to Overview.
const backgroundRoute = shallowRef(null)

export function attachSettingsRouter(instance) {
  router = instance
  router.afterEach((to) => {
    if (to.name !== SETTINGS_ROUTE_NAME) backgroundRoute.value = to
  })
}

function currentTab() {
  const location = router.currentRoute.value
  if (location.name !== SETTINGS_ROUTE_NAME) return DEFAULT_SETTINGS_TAB
  return location.params.tab || DEFAULT_SETTINGS_TAB
}

// Reads as the plain state object it replaces — `settings.open`, `settings.tab` —
// so every panel that gates its fetch on a tab keeps working, but both fields are
// now derived from the URL rather than being a second copy of it that can drift.
// Plain getters, not `reactive()`: they read router.currentRoute, which is a ref,
// so a template or computed that touches them tracks the navigation itself.
export const settings = {
  get open() {
    return router.currentRoute.value.name === SETTINGS_ROUTE_NAME
  },
  set open(shouldBeOpen) {
    if (shouldBeOpen === settings.open) return
    if (shouldBeOpen) openSettings(currentTab())
    else closeSettings()
  },
  get tab() {
    return currentTab()
  },
  set tab(tab) {
    // frappe-ui's SettingsDialog hands its tab model to reka-ui's TabsRoot, which
    // writes the model back as it mounts — before the merchant has touched
    // anything. Without the open guard that write would navigate to
    // /settings/general over a cold link to /settings/payments.
    if (!settings.open || tab === currentTab()) return
    // replace, not push: Back should close the dialog, not walk back through the
    // tabs the merchant skimmed on the way to the one they wanted.
    router.replace({ name: SETTINGS_ROUTE_NAME, params: { tab } })
  },
}

// What the rest of the app should believe it is looking at: while the dialog is
// open the shell's active nav item and a detail page's route params must keep
// coming from the page behind it, not from /settings/*.
export const visibleRoute = computed(() =>
  settings.open && backgroundRoute.value ? backgroundRoute.value : router.currentRoute.value,
)

// An unknown tab is normalised by the route record's beforeEnter, so one place
// decides what a bad tab name means.
export function openSettings(tab = DEFAULT_SETTINGS_TAB) {
  router.push({ name: SETTINGS_ROUTE_NAME, params: { tab } })
}

// push, not router.back(): a merchant who opened the link cold has no history
// inside the app, and back() would walk them out of it entirely.
export function closeSettings() {
  router.push(backgroundRoute.value?.fullPath ?? '/')
}
