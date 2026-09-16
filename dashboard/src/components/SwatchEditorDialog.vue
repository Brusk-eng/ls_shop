<script setup>
/**
 * Give an attribute's values their swatches. Store-wide, so it is set here once and every
 * product that carries the colour picks it up — a swatch is never edited from a product.
 */
import { ref, watch } from 'vue'
import { Button, Dialog, TextInput, toast, useFileUpload } from 'frappe-ui'
import SwatchDot from './SwatchDot.vue'
import { useAdminAction } from '../data/api'

const props = defineProps({
  attribute: { type: Object, default: null },
})

const open = defineModel('open', { type: Boolean, default: false })
const emit = defineEmits(['saved'])

const { upload, isUploading } = useFileUpload()
const setAction = useAdminAction('catalog.set_swatch')
const clearAction = useAdminAction('catalog.clear_swatch')

// Edited in place so a row shows its new colour the moment it is picked, rather than after a
// round trip through the Attributes list.
const rows = ref([])
const fileInputs = ref({})
const savingValue = ref('')

watch(
  () => props.attribute,
  (attribute) => {
    rows.value = (attribute?.values ?? []).map((entry) => ({ ...entry }))
  },
  { immediate: true },
)

async function save(row, changes) {
  savingValue.value = row.value
  const next = { ...row, ...changes }
  await setAction.submit({
    attribute: props.attribute.name,
    value: row.value,
    color: next.color ?? '',
    image: next.image ?? '',
  })
  savingValue.value = ''
  if (setAction.error) return
  Object.assign(row, changes)
  emit('saved')
}

async function clear(row) {
  savingValue.value = row.value
  await clearAction.submit({ attribute: props.attribute.name, value: row.value })
  savingValue.value = ''
  if (clearAction.error) return
  row.color = null
  row.image = null
  emit('saved')
}

async function uploadImage(row, event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  try {
    const uploaded = await upload(file, { private: false })
    await save(row, { image: uploaded.file_url })
  } catch {
    toast.error(`Could not upload ${file.name}`)
  }
}
</script>

<template>
  <Dialog v-model:open="open" size="2xl" :title="attribute ? `${attribute.name} swatches` : 'Swatches'">
    <div v-if="attribute" class="space-y-4">
      <p class="text-p-sm text-ink-gray-5">
        A shopper sees these instead of the words. Upload an image for a pattern a flat colour
        cannot show — denim, floral, marble.
      </p>

      <div v-if="rows.length" class="divide-y divide-outline-gray-1 border-y border-outline-gray-1">
        <div v-for="row in rows" :key="row.value" class="flex items-center gap-3 py-3">
          <SwatchDot :color="row.color" :image="row.image" :label="row.value" size="lg" />

          <span class="min-w-0 flex-1 truncate text-base text-ink-gray-8">{{ row.value }}</span>

          <input
            :value="row.color || '#000000'"
            type="color"
            class="size-7 shrink-0 cursor-pointer rounded-4 border border-outline-gray-2 bg-surface-base"
            :aria-label="`${row.value} colour`"
            @change="save(row, { color: $event.target.value })"
          />

          <TextInput
            :model-value="row.color ?? ''"
            class="w-28 shrink-0"
            placeholder="#000000"
            :aria-label="`${row.value} hex`"
            @change="save(row, { color: $event })"
          />

          <input
            :ref="(element) => (fileInputs[row.value] = element)"
            type="file"
            accept="image/*"
            class="hidden"
            @change="uploadImage(row, $event)"
          />
          <Button
            :loading="isUploading && savingValue === row.value"
            icon-left="lucide-image"
            :label="row.image ? 'Replace' : 'Image'"
            variant="subtle"
            @click="fileInputs[row.value]?.click()"
          />

          <Button
            :disabled="!row.color && !row.image"
            :loading="savingValue === row.value && !isUploading"
            icon="lucide-x"
            :aria-label="`Clear ${row.value} swatch`"
            variant="ghost"
            @click="clear(row)"
          />
        </div>
      </div>

      <p v-else class="text-base text-ink-gray-5">
        {{ attribute.name }} has no values yet. Add one first.
      </p>
    </div>
  </Dialog>
</template>
