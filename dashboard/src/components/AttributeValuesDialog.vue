<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { Button, Dialog, ErrorMessage, TextInput, toast, useFileUpload } from 'frappe-ui'
import { useAdminAction } from '../data/api'

const props = defineProps({
  attribute: { type: Object, default: null },
})

const open = defineModel('open', { type: Boolean, default: false })
const emit = defineEmits(['saved'])

const { upload, isUploading } = useFileUpload()
const setAction = useAdminAction('catalog.set_swatch')
const clearAction = useAdminAction('catalog.clear_swatch')
const renameAction = useAdminAction('catalog.rename_attribute_value')
const addAction = useAdminAction('catalog.add_attribute_value')

const rows = ref([])
const fileInputs = ref({})
const nameInputs = ref({})
const savingValue = ref('')
const editingValue = ref('')
const newValue = ref('')

const isColour = computed(() => Boolean(props.attribute?.is_colour))

watch(
  () => props.attribute,
  (attribute) => {
    rows.value = (attribute?.values ?? []).map((entry) => ({ ...entry }))
    editingValue.value = ''
    newValue.value = ''
  },
  { immediate: true },
)

async function startRename(row) {
  if (row.used_by) return
  editingValue.value = row.value
  await nextTick()
  nameInputs.value[row.value]?.el?.focus?.()
}

async function commitRename(row, typed) {
  const next = (typed ?? '').trim()
  editingValue.value = ''
  if (!next || next === row.value) return

  savingValue.value = row.value
  await renameAction.submit({ attribute: props.attribute.name, value: row.value, new_value: next })
  savingValue.value = ''
  if (renameAction.error) return
  row.value = next
  emit('saved')
}

async function save(row, changes) {
  const next = { ...row, ...changes }
  if (!next.color && !next.image) return clear(row)

  savingValue.value = row.value
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

async function addValue() {
  const value = newValue.value.trim()
  if (!value) return
  await addAction.submit({ attribute: props.attribute.name, value })
  if (addAction.error) return
  rows.value.push({ value, color: null, image: null, used_by: 0 })
  newValue.value = ''
  emit('saved')
}
</script>

<template>
  <Dialog v-model:open="open" size="2xl" :title="attribute ? attribute.name : 'Attribute'">
    <div v-if="attribute" class="space-y-4">
      <p class="text-p-sm text-ink-gray-5">
        <template v-if="isColour">
          A shopper sees these instead of the words. Upload an image for a pattern a flat colour
          cannot show — denim, floral, marble.
        </template>
        <template v-else>
          The choices a shopper picks from. Click a name to rename one.
        </template>
      </p>

      <div v-if="rows.length" class="divide-y divide-outline-gray-1 border-y border-outline-gray-1">
        <div v-for="row in rows" :key="row.value" class="flex items-center gap-3 py-3">
          <TextInput
            v-if="editingValue === row.value"
            :ref="(element) => (nameInputs[row.value] = element)"
            :model-value="row.value"
            class="min-w-0 flex-1"
            :aria-label="`Rename ${row.value}`"
            @update:model-value="commitRename(row, $event)"
            @keydown.escape="editingValue = ''"
          />
          <button
            v-else
            type="button"
            class="min-w-0 flex-1 truncate rounded-4 px-1 py-0.5 text-start text-base"
            :class="
              row.used_by
                ? 'cursor-default text-ink-gray-5'
                : 'text-ink-gray-8 hover:bg-surface-gray-2'
            "
            :title="
              row.used_by
                ? `Used by ${row.used_by} products — renaming would leave their SKUs and links saying ${row.value}.`
                : `Rename ${row.value}`
            "
            @click="startRename(row)"
          >
            {{ row.value }}
          </button>

          <template v-if="isColour">
            <input
              :value="row.color || '#000000'"
              type="color"
              class="size-7 shrink-0 cursor-pointer rounded-4 border border-outline-gray-2 bg-surface-base"
              :aria-label="`${row.value} colour`"
              @change="save(row, { color: $event.target.value })"
            />

            <!-- TextInput emits update:modelValue on the settled value and has no change event of
                 its own; a @change here would fall through to the native input and hand us a DOM
                 Event instead of the hex. -->
            <TextInput
              :model-value="row.color ?? ''"
              class="w-28 shrink-0"
              placeholder="#000000"
              :aria-label="`${row.value} hex`"
              @update:model-value="save(row, { color: $event })"
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
              icon="lucide-x"
              :aria-label="`Clear ${row.value} swatch`"
              variant="ghost"
              @click="clear(row)"
            />
          </template>
        </div>
      </div>

      <div class="flex items-end gap-2">
        <TextInput
          v-model="newValue"
          class="min-w-0 flex-1"
          :label="`Add a value to ${attribute.name}`"
          placeholder="Type a new one"
          @keydown.enter="addValue"
        />
        <Button label="Add" :loading="addAction.loading" @click="addValue" />
      </div>
      <ErrorMessage :message="addAction.error?.message" />
    </div>
  </Dialog>
</template>
