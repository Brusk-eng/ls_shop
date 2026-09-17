<script setup>
/**
 * The address shoppers are sent to when they collect from one warehouse. It is a plain Address
 * of type Shop linked to the warehouse, so Desk and checkout read the same record this writes.
 */
import { computed, reactive, ref, useId, watch } from 'vue'
import { Button, Dialog, FormControl, FormLabel, toast } from 'frappe-ui'
import LocationMap from '../LocationMap.vue'
import SettingsLinkControl from './SettingsLinkControl.vue'
import { useAdminAction } from '../../data/api'

const props = defineProps({
  warehouse: { type: Object, default: null },
  submit: { type: Function, required: true },
})

const open = defineModel('open', { type: Boolean, required: true })

const COUNTRY_FIELD = { fieldname: 'country', options: 'Country' }
const FIELDNAMES = [
  'address_title',
  'address_line1',
  'address_line2',
  'city',
  'state',
  'pincode',
  'country',
  'phone',
  'custom_store_location',
]

const formId = useId()
const values = reactive({})
const saving = ref(false)
const map = ref(null)

const findLocation = useAdminAction('settings.find_address_location')

const isEdit = computed(() => Boolean(props.warehouse?.address))

const searchText = computed(() =>
  [values.address_line1, values.address_line2, values.city, values.state, values.pincode, values.country]
    .filter(Boolean)
    .join(', '),
)

// Reset on open: the dialog outlives one warehouse, so the next one opened would otherwise
// still hold the last one's answers.
watch(open, (isOpen) => {
  if (!isOpen || !props.warehouse) return

  const address = props.warehouse.address ?? {}
  for (const fieldname of FIELDNAMES) values[fieldname] = address[fieldname] ?? ''
  values.address_title ||= props.warehouse.warehouse_name
  values.country ||= props.warehouse.country
})

async function findOnMap() {
  const location = await findLocation.submit({ query: searchText.value })
  if (findLocation.error) return
  if (!location) {
    toast.info('That address is not on the map. Drop the pin by hand.')
    return
  }
  map.value.moveTo(location.latitude, location.longitude)
}

async function save() {
  saving.value = true
  try {
    const saved = await props.submit({ ...values })
    if (!saved) return

    open.value = false
    toast.success(isEdit.value ? 'Pickup address saved' : 'Pickup address added')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <Dialog
    v-model:open="open"
    size="2xl"
    :title="`${isEdit ? 'Edit' : 'Add'} pickup address · ${warehouse?.warehouse_name ?? ''}`"
  >
    <template #default>
      <form :id="formId" class="flex flex-col gap-4" @submit.prevent="save">
        <FormControl
          v-model="values.address_title"
          label="Name at checkout"
          required
          description="What shoppers read when they pick where to collect."
        />
        <FormControl v-model="values.address_line1" label="Address line 1" required />
        <FormControl v-model="values.address_line2" label="Address line 2" />

        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <FormControl v-model="values.city" label="City" required />
          <FormControl v-model="values.state" label="State" />
          <FormControl v-model="values.pincode" label="Postal code" />
          <SettingsLinkControl
            v-model="values.country"
            :field="COUNTRY_FIELD"
            options-path="settings.get_link_options"
            label="Country"
            required
            class="!w-full"
          />
          <FormControl v-model="values.phone" label="Phone" type="tel" />
        </div>

        <div class="flex flex-col gap-2">
          <div class="flex items-center justify-between gap-2">
            <FormLabel label="Location on the map" size="md" />
            <Button
              label="Find on map"
              icon-left="lucide-search"
              :disabled="!values.address_line1 && !values.city"
              :loading="findLocation.loading"
              @click="findOnMap"
            />
          </div>
          <LocationMap ref="map" v-model="values.custom_store_location" />
        </div>
      </form>
    </template>

    <template #actions>
      <Button
        class="w-full"
        type="submit"
        :form="formId"
        variant="solid"
        theme="gray"
        :loading="saving"
        :disabled="!values.country"
        :label="isEdit ? 'Save' : 'Add'"
      />
    </template>
  </Dialog>
</template>
