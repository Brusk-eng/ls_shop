<script setup>
/**
 * A settings tab built as a provider list over a second section: Payments over cash on
 * delivery, Shipping over delivery options. Both tabs are this same screen with a different
 * registry and a different section below, so the arrangement lives here once.
 *
 * The arrangement is all about height. The provider list is short and fixed, so it takes only
 * the height it needs and the section below gets the rest of the scroll — but either half can
 * open a screen that takes the whole tab over (a provider's keys, a delivery option's form),
 * and a takeover screen is long. So whichever half is showing one is given `min-h-0 flex-1`
 * and the other is unmounted; without that the screen keeps its content height, cannot
 * scroll, and its overflow is clipped by the dialog.
 */
import { ref } from 'vue'
import IntegrationsPanel from './IntegrationsPanel.vue'

defineProps({
  store: { type: Object, required: true },
  title: { type: String, required: true },
  description: { type: String, required: true },
  // Opening the dialog should fetch; switching away and back should not.
  active: { type: Boolean, default: false },
})

// The provider whose keys are open, and whether the section below has opened a screen of its
// own. Two values rather than one: they are opened from different halves of the tab.
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
    <!-- The list is the first of two sections rather than a whole panel, so its body drops the
         4rem of tail padding a panel ends on; the section below supplies its own top spacing.
         Reached through frappe-ui's own data-slot, the supported hook, so IntegrationsPanel
         stays generic and untouched. -->
    <IntegrationsPanel
      v-model:configuring="configuring"
      :store="store"
      :active="active"
      :title="title"
      :description="description"
    />
  </div>

  <!-- `setTakeover` is for a section that can open a screen of its own; one that cannot, like
       cash on delivery, simply ignores it. -->
  <slot v-if="!configuring" :takeover="sectionTakeover" :set-takeover="(open) => (sectionTakeover = open)" />
</template>
