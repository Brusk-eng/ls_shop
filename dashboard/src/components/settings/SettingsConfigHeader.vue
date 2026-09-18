<script setup>
/**
 * The header of a settings screen that takes the whole panel over — one gateway's keys, one
 * warehouse's pickup address.
 *
 * It is SettingsPanelHeader — same heading, same tail gap as every other screen in the dialog —
 * plus the Back button that returns to the list behind it, which only a takeover screen has.
 */
import { Button } from 'frappe-ui'
import SettingsPanelHeader from './SettingsPanelHeader.vue'

defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' },
})

const emit = defineEmits(['back'])
</script>

<template>
  <SettingsPanelHeader :title="title" :description="description">
    <template #actions>
      <Button label="Back" icon-left="lucide-arrow-left" @click="emit('back')" />
      <!-- Saving differs per screen — one emits, one submits a form — so the screen keeps
           its own button and only the shape around it is shared. -->
      <slot name="actions" />
    </template>
  </SettingsPanelHeader>
</template>
