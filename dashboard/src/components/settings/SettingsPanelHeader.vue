<script setup>
import { SettingsHeader } from 'frappe-ui'

defineProps({
  title: { type: String, default: '' },
  description: { type: String, default: '' },
})
</script>

<template>
  <SettingsHeader class="pb-4" :title="title" :description="description">
    <!-- Behind a v-if: an empty default slot suppresses frappe-ui's own title fallback. -->
    <template v-if="$slots.default" #default><slot /></template>
    <template v-if="$slots.actions" #actions><slot name="actions" /></template>
  </SettingsHeader>
</template>
