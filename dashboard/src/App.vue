<script setup>
import { computed, defineAsyncComponent, provide, shallowReactive } from 'vue'
import { START_LOCATION, routeLocationKey } from 'vue-router'
import { FrappeUIProvider } from 'frappe-ui'
import { visibleRoute } from './ia/settingsRoute'
import { useIsMobile } from './utils/useIsMobile'
import AppShell from './components/AppShell.vue'
import AppSettingsDialog from './components/settings/AppSettingsDialog.vue'
import SearchPalette from './components/SearchPalette.vue'
import ImportDialog from './components/import/ImportDialog.vue'
import AddProductDialog from './components/AddProductDialog.vue'

// Mobile and desktop are separate navigation families — frappe-ui ships
// MobileShell alongside DesktopShell rather than as a responsive variant of it —
// so the app picks a layout for the viewport instead of adding breakpoints to
// the sidebar. The phone bundle is lazy so a desktop load never pays for it.
const isMobileViewport = useIsMobile()
const MobileLayout = defineAsyncComponent(() => import('./components/MobileLayout.vue'))
const Layout = computed(() => (isMobileViewport.value ? MobileLayout : AppShell))

// The settings dialog is a route (/settings/:tab) that renders nothing, so
// everything below this point has to keep seeing the page it was opened over:
// the sidebar's active link, and a detail page's own `route.params.id`, which
// would otherwise go undefined mid-flight and refetch behind the modal.
// router-view takes the location as a prop; `useRoute()` reads an injection, so
// the same location is published under vue-router's own key. Getters over the
// computed rather than a copy, because the route object is replaced wholesale on
// every navigation — this is the shape vue-router itself provides.
const shellRoute = {}
for (const key in START_LOCATION) {
  Object.defineProperty(shellRoute, key, { get: () => visibleRoute.value[key], enumerable: true })
}
provide(routeLocationKey, shallowReactive(shellRoute))
</script>

<template>
  <FrappeUIProvider>
    <component :is="Layout">
      <router-view :route="visibleRoute" />
    </component>

    <!-- One instance for the whole app, outside the layout so both shells reach
         them; opened from the workspace menu and the sidebar footer. -->
    <AppSettingsDialog />
    <SearchPalette />
    <ImportDialog />
    <AddProductDialog />
  </FrappeUIProvider>
</template>

