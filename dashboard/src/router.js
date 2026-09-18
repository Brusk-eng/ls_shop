import { createRouter, createWebHistory } from 'vue-router'
import { SETTINGS_TABS } from './ia/settings'
import { attachSettingsRouter, DEFAULT_SETTINGS_TAB, SETTINGS_ROUTE_NAME } from './ia/settingsRoute'

const routes = [
  { path: '/', name: 'Dashboard', component: () => import('./pages/Dashboard.vue') },
  { path: '/orders', name: 'Orders', component: () => import('./pages/Orders.vue') },
  { path: '/orders/:id', name: 'OrderDetail', component: () => import('./pages/OrderDetail.vue'), meta: { split: true } },
  { path: '/products', name: 'Products', component: () => import('./pages/Products.vue') },
  // `split`: the page owns its own scroll — a form pane and a summary pane
  // side by side, the way Helpdesk's ticket screen does it.
  { path: '/products/:id', name: 'ProductDetail', component: () => import('./pages/ProductDetail.vue'), meta: { split: true } },
  { path: '/products/:id/variants/:variantId', name: 'VariantDetail', component: () => import('./pages/VariantDetail.vue') },
  { path: '/collections', name: 'Collections', component: () => import('./pages/Collections.vue') },
  { path: '/attributes', name: 'Attributes', component: () => import('./pages/Attributes.vue') },
  { path: '/inventory', name: 'Inventory', component: () => import('./pages/Inventory.vue') },
  { path: '/inventory/adjustments', name: 'Adjustments', component: () => import('./pages/Adjustments.vue') },
  { path: '/pricing', name: 'Pricing', component: () => import('./pages/Pricing.vue') },
  { path: '/customers', name: 'Customers', component: () => import('./pages/Customers.vue') },
  { path: '/customers/:id', name: 'CustomerDetail', component: () => import('./pages/CustomerDetail.vue') },
  { path: '/reviews', name: 'Reviews', component: () => import('./pages/Reviews.vue') },
  { path: '/reviews/:id', name: 'ReviewDetail', component: () => import('./pages/ReviewDetail.vue') },
  // Overview is the dashboard, so /analytics itself holds nothing: it opens
  // the first report.
  { path: '/analytics', redirect: '/analytics/revenue' },
  { path: '/analytics/revenue', name: 'RevenueReport', component: () => import('./pages/analytics/Revenue.vue') },
  { path: '/analytics/inventory', name: 'InventoryReport', component: () => import('./pages/analytics/Inventory.vue') },
  { path: '/analytics/storefront', name: 'StorefrontReport', component: () => import('./pages/analytics/Storefront.vue') },
  { path: '/storefront/theme', name: 'StorefrontTheme', component: () => import('./pages/storefront/Theme.vue') },
  { path: '/storefront/navigation', name: 'StorefrontNavigation', component: () => import('./pages/storefront/Navigation.vue') },
  { path: '/storefront/pages', name: 'StorefrontPages', component: () => import('./pages/storefront/Pages.vue') },
  // A Shop Web Page is named by its title, so the create path shadows a page
  // literally titled "new" — rare enough to live with, and the editor is still
  // reachable from the list row.
  { path: '/storefront/pages/new', name: 'StorefrontPageNew', component: () => import('./pages/storefront/PageDetail.vue') },
  { path: '/storefront/pages/:name', name: 'StorefrontPageDetail', component: () => import('./pages/storefront/PageDetail.vue') },
  // Settings is a dialog with a URL. These two records carry no component on
  // purpose: vue-router accepts a record with no component as long as it is
  // named, and RouterView skips a matched record that has no `components` and
  // renders nothing — which is what we want, because App.vue hands RouterView
  // the location the dialog was opened over so that page stays mounted behind
  // the modal. Giving this route a component would tear that page down.
  { path: '/settings', redirect: `/settings/${DEFAULT_SETTINGS_TAB}` },
  {
    path: '/settings/:tab',
    name: SETTINGS_ROUTE_NAME,
    // A tab the dialog does not render would leave the panel column blank with
    // nothing lit in the sidebar, so a typo'd or stale link lands on the first
    // tab instead. beforeEnter rather than `redirect`: a redirect function must
    // always return a location, and this one only sometimes redirects.
    beforeEnter: (to) => {
      const known = SETTINGS_TABS.some((settingsTab) => settingsTab.value === to.params.tab)
      return known ? true : { path: `/settings/${DEFAULT_SETTINGS_TAB}`, replace: true }
    },
  },
  // Last, so it only catches what nothing above claimed: without it an unknown path rendered the
  // shell with an empty content area, which reads as a screen that failed to load.
  { path: '/:pathMatch(.*)*', name: 'NotFound', component: () => import('./pages/NotFound.vue') },
]

export const router = createRouter({
  history: createWebHistory('/commera'),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

// ia/settingsRoute derives the dialog's open/tab state from the URL, and needs the
// instance to push and to remember the page the dialog was opened over.
attachSettingsRouter(router)
