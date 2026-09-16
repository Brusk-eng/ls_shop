<script setup>
/**
 * One attribute value's swatch. The fallback chain lives here and nowhere else, so every
 * surface that draws a colour — Attributes, the add-product pickers, the variant grid —
 * degrades the same way when a store has not set one.
 */
import { computed } from 'vue'

const SIZES = {
  xs: 'size-3',
  sm: 'size-4',
  md: 'size-6',
  lg: 'size-8',
}

const props = defineProps({
  color: { type: String, default: '' },
  image: { type: String, default: '' },
  label: { type: String, default: '' },
  size: { type: String, default: 'sm' },
})

const sizeClass = computed(() => SIZES[props.size] ?? SIZES.sm)

// The colour itself is data, not styling, so it cannot come from a Tailwind class.
const fill = computed(() => {
  if (props.image) return { backgroundImage: `url(${props.image})`, backgroundSize: 'cover' }
  if (props.color) return { backgroundColor: props.color }
  return {}
})

const isEmpty = computed(() => !props.image && !props.color)
</script>

<template>
  <span
    class="inline-block shrink-0 rounded-full border border-outline-gray-2 bg-surface-gray-3"
    :class="[sizeClass, isEmpty && 'border-dashed']"
    :style="fill"
    :title="label || undefined"
    :aria-label="label || undefined"
    role="img"
  />
</template>
