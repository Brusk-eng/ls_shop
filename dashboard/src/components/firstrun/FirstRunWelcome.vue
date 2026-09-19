<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Button } from 'frappe-ui'
import { stepsWithProgress } from '../../data/firstRun'
import { forgetWelcomeSeen, hasSeenWelcome, markWelcomeSeen } from '../../ia/firstRun'
import SetupPanel from './SetupPanel.vue'
import WelcomeGreeting from './WelcomeGreeting.vue'

// First run, in two beats: the wordmark writes itself once, clears the screen,
// and hands over to the setup panel. Neither survives a finished setup.
const route = useRoute()

// Until an endpoint reports what the store has actually configured, `?done=` is
// the only source of step state — and with no state there is nothing to claim,
// so the surface stays away rather than inventing progress.
const doneCount = computed(() => {
  const done = Number(route.query.done)
  return Number.isInteger(done) ? done : null
})

const steps = computed(() => (doneCount.value === null ? [] : stepsWithProgress(doneCount.value)))
const settingUp = computed(() => steps.value.length > 0 && steps.value.some((step) => !step.done))

// `?replay` overrides the seen-once rule, so the greeting can be watched again
// without digging the key out of localStorage. Preview-only, like `?done=`.
const forced = 'replay' in route.query

// The greeting belongs to setting up, and it belongs to it once.
const greetingDone = ref(forced ? false : hasSeenWelcome())

// The panel starts while the greeting is still clearing, so the handover is one
// motion rather than two with a pause between them.
const handedOver = ref(greetingDone.value)

// Remounting is what replays the draw, so the key carries a counter.
const replayCount = ref(0)

function finishGreeting() {
  markWelcomeSeen()
  greetingDone.value = true
}

function replay() {
  forgetWelcomeSeen()
  greetingDone.value = false
  handedOver.value = false
  replayCount.value += 1
}
</script>

<template>
  <WelcomeGreeting
    v-if="settingUp && !greetingDone"
    :key="`greeting-${replayCount}`"
    @exiting="handedOver = true"
    @dismiss="finishGreeting"
  />
  <SetupPanel v-if="settingUp && handedOver" :key="`panel-${replayCount}`" :steps="steps" />

  <!-- Rides on `?done=`, so it exists only while step state is being faked and
       leaves with it. It is never on a real load. -->
  <div v-if="settingUp && greetingDone" class="fixed bottom-5 left-5 z-[60] flex items-center gap-2">
    <Button icon-left="lucide-rotate-ccw" label="Replay" class="shadow-lg" @click="replay" />
  </div>
</template>
