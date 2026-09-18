<script setup>
import { ref } from 'vue'
import IntegrationsPanel from './IntegrationsPanel.vue'

defineProps({
  store: { type: Object, required: true },
  title: { type: String, required: true },
  description: { type: String, required: true },
  // Opening the dialog should fetch; switching away and back should not.
  active: { type: Boolean, default: false },
})

const configuring = ref(null)
const sectionTakeover = ref(false)
</script>

<template>
  <div
    v-if="!sectionTakeover"
    class="flex flex-col"
    :class="
      configuring
        ? 'min-h-0 flex-1'
        : 'shrink-0 [&_[data-slot=scroll-area-viewport]]:pb-0'
    "
  >
    <!-- Drops the 4rem of tail padding a whole panel ends on, through frappe-ui's own
         data-slot, so IntegrationsPanel itself stays generic. -->
    <IntegrationsPanel
      v-model:configuring="configuring"
      :store="store"
      :active="active"
      :title="title"
      :description="description"
    />
  </div>

  <!-- A section that cannot open a screen of its own simply ignores `setTakeover`. -->
  <slot v-if="!configuring" :takeover="sectionTakeover" :set-takeover="(open) => (sectionTakeover = open)" />
</template>
