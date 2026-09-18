<script setup>
/**
 * Creating or editing one delivery option, as a screen that takes the panel over — the same
 * shape as a gateway's keys or a warehouse's pickup address. Settings never opens a dialog on
 * top of the settings dialog.
 *
 * Every field below the title is the server's description of the doctype, rendered by the
 * same meta-driven rows as the carrier keys and the advanced tab — so a docfield added to
 * the shipping service reaches this form without a line changing here.
 */
import { computed, reactive, ref, useId } from 'vue'
import { Button, FormControl, SettingsBody, SettingsRow, toast } from 'frappe-ui'
import SettingsConfigHeader from './SettingsConfigHeader.vue'
import SettingsFieldRows from './SettingsFieldRows.vue'

const props = defineProps({
  // Null while creating; the row being edited otherwise.
  option: { type: Object, default: null },
  groups: { type: Array, default: () => [] },
  // Set only where the server offers a picker for this doctype's Link fields. Without one a
  // Link stays a plain box rather than a combobox that can never fill itself.
  linkOptionsPath: { type: String, default: '' },
  submit: { type: Function, required: true },
})

const emit = defineEmits(['back'])

// The submit button sits in the header, outside the form, so `form` is what makes the browser
// run each field's `required` check.
const formId = useId()

const isEdit = computed(() => Boolean(props.option))

// The title is what an order stores against its shipment, so renaming it after the fact
// would rewrite history the shopper already agreed to. It is set once, then read.
const editableGroups = computed(() =>
  props.groups
    .map((group) => ({
      ...group,
      fields: group.fields.filter((field) => field.fieldname !== 'title'),
    }))
    .filter((group) => group.fields.length),
)

const title = ref(props.option?.title ?? '')
const saving = ref(false)

// Built once here rather than reset on open: the screen is mounted when the row is picked and
// torn down on Back, so it cannot carry the previous row's answers the way the dialog could.
const values = reactive(
  Object.fromEntries(
    props.groups.flatMap((group) =>
      group.fields
        .filter((field) => field.fieldname !== 'title')
        // An existing row carries its own stored answer; `field.value` is the doctype's
        // default, which is what a new option should start from.
        .map((field) => [
          field.fieldname,
          props.option ? (props.option[field.fieldname] ?? '') : (field.value ?? ''),
        ]),
    ),
  ),
)

async function save() {
  saving.value = true
  try {
    // The title is only sent while creating — the server treats it as read-only after,
    // and sending it back would invite a refusal on an otherwise valid edit.
    const payload = isEdit.value ? { ...values } : { ...values, title: title.value.trim() }
    const saved = await props.submit(payload)
    if (!saved) return

    toast.success(isEdit.value ? 'Delivery option saved' : 'Delivery option added')
    emit('back')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <SettingsConfigHeader
    :title="isEdit ? option.title : 'Add a delivery option'"
    description="What shoppers pick at checkout, and what it costs them."
    @back="emit('back')"
  >
    <template #actions>
      <Button
        type="submit"
        :form="formId"
        variant="solid"
        theme="gray"
        :loading="saving"
        :label="isEdit ? 'Save' : 'Add'"
      />
    </template>
  </SettingsConfigHeader>

  <SettingsBody>
    <form :id="formId" @submit.prevent="save">
      <div class="divide-y divide-outline-gray-1">
        <SettingsRow
          v-if="isEdit"
          title="Name at checkout"
          description="Orders are stored against this name, so it cannot be changed."
        >
          <p class="w-72 text-base text-ink-gray-7">{{ option.title }}</p>
        </SettingsRow>

        <div v-else class="py-3.5">
          <FormControl
            v-model="title"
            label="Name at checkout"
            required
            placeholder="Standard delivery"
            description="What shoppers read beside the price. It cannot be changed later."
          />
        </div>

        <SettingsFieldRows
          :groups="editableGroups"
          :values="values"
          :link-options-path="linkOptionsPath"
          @update="(fieldname, value) => (values[fieldname] = value)"
        />
      </div>
    </form>
  </SettingsBody>
</template>
