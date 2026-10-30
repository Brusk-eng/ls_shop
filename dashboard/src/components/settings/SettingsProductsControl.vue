<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { refDebounced } from '@vueuse/core'
import { MultiSelect } from 'frappe-ui'
import { useMethodRead } from '../../data/api'

const SEARCH_DEBOUNCE_MS = 300

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

const query = ref('')
const searchText = refDebounced(query, SEARCH_DEBOUNCE_MS)

const results = useMethodRead('commera.api.storefront.products.get_products', {
  params: () => ({ query: searchText.value, page_size: 20 }),
  refetch: true,
})

const titles = reactive({})
watch(
  () => results.data,
  (page) => {
    for (const product of page?.products ?? []) titles[product.id] = product.title
  },
)

const options = computed(() => {
  const merged = new Map(
    (results.data?.products ?? []).map((product) => [product.id, { label: product.title, value: product.id }]),
  )
  for (const code of props.modelValue) {
    if (!merged.has(code)) merged.set(code, { label: titles[code] ?? code, value: code })
  }
  return [...merged.values()]
})
</script>

<template>
  <div class="w-full sm:w-72">
    <MultiSelect
      v-model:query="query"
      class="w-full"
      :model-value="modelValue"
      :options="options"
      :loading="results.loading"
      :filterable="false"
      :disabled="disabled"
      placeholder="Pick products"
      @update:model-value="emit('update:modelValue', $event)"
    />
  </div>
</template>
