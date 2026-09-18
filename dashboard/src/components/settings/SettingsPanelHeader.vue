<script setup>
/**
 * Every settings heading in this dialog, and the gap under it.
 *
 * frappe-ui's SettingsHeader ends flush with the scroll viewport below it, so a panel whose
 * body scrolls had its first row slide up hard against the blurb and get sliced through
 * mid-line as it passed under. The tail gap that prevents that belongs to every panel
 * equally, so no screen sets it itself — change it here and the whole dialog moves together.
 */
import { SettingsHeader } from 'frappe-ui'

defineProps({
  title: { type: String, default: '' },
  description: { type: String, default: '' },
})
</script>

<template>
  <SettingsHeader class="pb-4" :title="title" :description="description">
    <!-- Both forwarded behind a v-if: handing frappe-ui an empty default slot would suppress
         its own title/description fallback and render a blank heading. -->
    <template v-if="$slots.default" #default><slot /></template>
    <template v-if="$slots.actions" #actions><slot name="actions" /></template>
  </SettingsHeader>
</template>
