<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Button } from 'frappe-ui'
import { stepsWithProgress } from '../../data/firstRun'
import { forgetWelcomeSeen, hasSeenWelcome, markWelcomeSeen } from '../../ia/firstRun'
import SetupPanel from './SetupPanel.vue'
import WelcomeGreeting from './WelcomeGreeting.vue'

const route = useRoute()

// No endpoint reports what the store has configured yet, so `?done=` is the only
// source of step state and a real load renders nothing.
const doneCount = computed(() => {
  const done = Number(route.query.done)
  return Number.isInteger(done) ? done : null
})

const steps = computed(() => (doneCount.value === null ? [] : stepsWithProgress(doneCount.value)))
const settingUp = computed(() => steps.value.length > 0 && steps.value.some((step) => !step.done))

// Preview-only, like `?done=`: replays the greeting without clearing localStorage.
const forced = 'replay' in route.query

const greetingDone = ref(forced ? false : hasSeenWelcome())
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

  <!-- Rides on `?done=`, so it is never on a real load. -->
  <div v-if="settingUp && greetingDone" class="fixed bottom-5 left-5 z-[60] flex items-center gap-2">
    <Button icon-left="lucide-rotate-ccw" label="Replay" class="shadow-lg" @click="replay" />
  </div>
</template>
