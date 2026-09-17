<script setup>
/**
 * The store's warehouses, and which of them shoppers can collect an order from.
 *
 * Every write answers with the whole screen, which is adopted as-is — the server decides what a
 * warehouse's pickup address is, so nothing here patches a row by hand.
 */
import { computed, ref, watch } from 'vue'
import {
  Badge,
  Button,
  SettingsBody,
  SettingsHeader,
  SettingsRow,
  Switch,
  toast,
} from 'frappe-ui'
import EmptyState from '../EmptyState.vue'
import PickupAddressDialog from './PickupAddressDialog.vue'
import SettingsSkeleton from './SettingsSkeleton.vue'
import { createAdminCaller } from '../../data/adminCaller'
import { useAdminRead } from '../../data/api'

const props = defineProps({
  active: { type: Boolean, default: false },
})

const locations = useAdminRead('settings.get_locations', { immediate: false })
const { call, loading: saving } = createAdminCaller('settings.')

const screen = ref(null)
const editing = ref(null)
const editorOpen = ref(false)

watch(
  () => locations.data,
  (data) => data && (screen.value = data),
  { immediate: true },
)

watch(
  () => props.active,
  (isActive) => isActive && !locations.isFinished && locations.reload(),
  { immediate: true },
)

// Frappe answers 1/0, and a Switch handed a number never reads it as its starting state.
const pickupEnabled = computed(() => Boolean(screen.value?.store_pickup_enabled))
const warehouses = computed(() => screen.value?.warehouses ?? [])

async function mutate(method, params) {
  const data = await call(method, params)
  if (data) screen.value = data
  return data
}

async function toggleStorePickup(enabled) {
  if (!(await mutate('save_store_pickup', { enabled: enabled ? 1 : 0 }))) return
  toast.success(enabled ? 'Store pickup is on' : 'Store pickup is off')
}

async function toggleWarehouse(warehouse, allowPickup) {
  const saved = await mutate('save_warehouse_pickup', {
    warehouse: warehouse.name,
    allow_pickup: allowPickup ? 1 : 0,
  })
  if (!saved) return
  toast.success(`Pickup ${allowPickup ? 'allowed' : 'stopped'} at ${warehouse.warehouse_name}`)
}

function editAddress(warehouse) {
  editing.value = warehouse
  editorOpen.value = true
}

async function saveAddress(values) {
  return await mutate('save_pickup_address', { warehouse: editing.value.name, values })
}
</script>

<template>
  <SettingsHeader
    title="Locations"
    description="Your warehouses, and where shoppers can collect their order."
  />

  <SettingsBody>
    <EmptyState
      v-if="locations.error && !screen"
      compact
      icon="lucide-triangle-alert"
      title="These could not be loaded"
      description="Checkout still offers whatever is stored — this panel just cannot say what."
    >
      <Button label="Try again" variant="subtle" theme="gray" @click="locations.reload()" />
    </EmptyState>

    <SettingsSkeleton v-else-if="!screen" :rows="3" />

    <template v-else>
      <SettingsRow
        title="Store pickup"
        description="Let shoppers collect their order from a warehouse instead of having it delivered."
      >
        <Switch
          size="sm"
          :model-value="pickupEnabled"
          :disabled="saving"
          @update:model-value="toggleStorePickup"
        />
      </SettingsRow>

      <EmptyState
        v-if="!warehouses.length"
        compact
        icon="lucide-warehouse"
        title="No warehouses yet"
        description="Add a warehouse in your books, and it shows up here."
      />

      <div
        v-else
        class="divide-y divide-outline-gray-1 border-t border-outline-gray-1"
        :class="{ 'pointer-events-none opacity-60': !pickupEnabled }"
        :aria-disabled="!pickupEnabled"
      >
        <div
          v-for="warehouse in warehouses"
          :key="warehouse.name"
          class="flex items-start gap-3 py-3"
        >
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2">
              <p class="truncate text-base text-ink-gray-8">{{ warehouse.warehouse_name }}</p>
              <Badge
                v-if="warehouse.is_ecommerce_warehouse"
                label="Online orders"
                theme="gray"
                variant="subtle"
              />
            </div>
            <p class="mt-1 truncate text-sm text-ink-gray-5">{{ warehouse.company }}</p>

            <template v-if="warehouse.allow_pickup">
              <p v-if="warehouse.address" class="mt-1 text-sm text-ink-gray-6">
                {{ warehouse.address.display }}
                <span
                  v-if="!warehouse.address.custom_store_location"
                  class="text-ink-gray-5"
                > · No map pin</span>
              </p>
              <!-- Checkout skips a pickup warehouse it has nowhere to send the shopper to, so this
                   is the only place the owner learns why it is missing. -->
              <Badge
                v-else
                class="mt-1.5"
                label="Needs an address — hidden at checkout"
                theme="orange"
                variant="subtle"
              />
            </template>
          </div>

          <div class="flex shrink-0 items-center gap-2">
            <Button
              v-if="warehouse.allow_pickup"
              :label="warehouse.address ? 'Edit address' : 'Add address'"
              :disabled="!pickupEnabled"
              @click="editAddress(warehouse)"
            />
            <Switch
              size="sm"
              :model-value="Boolean(warehouse.allow_pickup)"
              :disabled="!pickupEnabled || saving"
              @update:model-value="toggleWarehouse(warehouse, $event)"
            />
          </div>
        </div>
      </div>
    </template>
  </SettingsBody>

  <PickupAddressDialog v-model:open="editorOpen" :warehouse="editing" :submit="saveAddress" />
</template>
