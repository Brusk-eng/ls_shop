<script setup>
/**
 * Editing one warehouse's pickup address takes over the panel, the way configuring a payment
 * provider does, so Settings never stacks a second dialog on top of itself.
 *
 * The address is a plain Address of type Shop linked to the warehouse, so Desk and checkout read
 * the same record this writes.
 */
import { computed, reactive, ref, useId } from 'vue'
import { Button, FormControl, FormLabel, SettingsBody, SettingsHeader, toast } from 'frappe-ui'
import LocationMap from '../LocationMap.vue'
import SettingsLinkControl from './SettingsLinkControl.vue'
import { useAdminAction } from '../../data/api'

const props = defineProps({
  warehouse: { type: Object, required: true },
  saving: { type: Boolean, default: false },
})

const emit = defineEmits(['back', 'save'])

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

// The Save button sits in the header, outside the form, so `form` is what makes the browser run
// each field's `required` check before anything is sent.
const formId = useId()
const map = ref(null)

const address = props.warehouse.address ?? {}
const values = reactive(
  Object.fromEntries(FIELDNAMES.map((fieldname) => [fieldname, address[fieldname] ?? ''])),
)
values.address_title ||= props.warehouse.warehouse_name
values.country ||= props.warehouse.country

const findLocation = useAdminAction('settings.find_address_location')

const searchText = computed(() =>
  [values.address_line1, values.address_line2, values.city, values.state, values.pincode, values.country]
    .filter(Boolean)
    .join(', '),
)

async function findOnMap() {
  const location = await findLocation.submit({ query: searchText.value })
  if (findLocation.error) return
  if (!location) {
    toast.info('That address is not on the map. Drop the pin by hand.')
    return
  }
  map.value.moveTo(location.latitude, location.longitude)
}
</script>

<template>
  <SettingsHeader :title="warehouse.warehouse_name" description="Pickup address">
    <template #actions>
      <Button label="Back" icon-left="lucide-arrow-left" @click="emit('back')" />
      <Button
        label="Save"
        type="submit"
        :form="formId"
        variant="solid"
        theme="gray"
        :loading="saving"
        :disabled="!values.country"
      />
    </template>
  </SettingsHeader>

  <SettingsBody>
    <form :id="formId" class="flex flex-col gap-4 pt-4" @submit.prevent="emit('save', { ...values })">
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
  </SettingsBody>
</template>
