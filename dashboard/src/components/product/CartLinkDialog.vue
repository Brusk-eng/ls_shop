<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { Button, Dialog, TextInput } from 'frappe-ui'
import { MAX_CART_LINES, cartLinkSizes, cartLinkUrl, storefrontUrl } from '../../data/product'
import { copyLink } from '../../utils/copyLink'

const props = defineProps({ product: { type: Object, required: true } })

const open = defineModel('open', { type: Boolean, required: true })

const sizes = computed(() => cartLinkSizes(props.product))
const quantities = reactive({})
const discountCode = ref('')

// Reset on every open: a link built for one shopper must not carry into the next.
watch(open, (isOpen) => {
  if (!isOpen) return
  const firstInStock = sizes.value.find((size) => size.available > 0)
  for (const key of Object.keys(quantities)) delete quantities[key]
  for (const size of sizes.value) quantities[size.itemCode] = size === firstInStock ? '1' : '0'
  discountCode.value = ''
})

const lines = computed(() =>
  sizes.value
    .map((size) => ({
      itemCode: size.itemCode,
      quantity: Math.trunc(Number(quantities[size.itemCode]) || 0),
    }))
    .filter((line) => line.quantity > 0),
)
const tooManyLines = computed(() => lines.value.length > MAX_CART_LINES)

const url = computed(() =>
  tooManyLines.value ? null : cartLinkUrl(storefrontUrl(props.product), lines.value, discountCode.value),
)
</script>

<template>
  <Dialog v-model:open="open" title="Create cart link" size="xl">
    <template #default>
      <p class="text-p-sm text-ink-gray-5">
        The link fills a shopper's cart with these sizes and takes them straight to checkout. It
        replaces whatever is already in their cart.
      </p>

      <div class="mt-4 space-y-3">
        <div
          v-for="size in sizes"
          :key="size.itemCode"
          class="flex items-center gap-3 border-b border-outline-gray-1 pb-3 last:border-0"
        >
          <div class="min-w-0 flex-1">
            <p class="truncate text-base text-ink-gray-8">{{ size.label }}</p>
            <p class="truncate text-sm text-ink-gray-5">{{ size.itemCode }} · {{ size.available }} available</p>
          </div>
          <TextInput
            v-model="quantities[size.itemCode]"
            type="number"
            min="0"
            step="1"
            size="sm"
            class="w-20 shrink-0"
            :aria-label="`Quantity of ${size.label}`"
          />
        </div>
      </div>

      <div class="mt-4 space-y-4">
        <TextInput
          v-model="discountCode"
          label="Discount code"
          description="Optional. Applied at checkout; a code that does not apply is reported there."
        />
        <div>
          <p class="text-sm text-ink-gray-5">Cart link</p>
          <div v-if="url" class="mt-2 flex items-center gap-2">
            <code class="min-w-0 flex-1 truncate rounded bg-surface-gray-2 px-2 py-1 text-sm text-ink-gray-7">
              {{ url }}
            </code>
            <Button label="Copy" icon-left="lucide-copy" @click="copyLink(url)" />
          </div>
          <p v-else-if="tooManyLines" class="mt-2 text-sm text-ink-red-6">
            A cart link holds at most {{ MAX_CART_LINES }} sizes. Clear the quantity on
            {{ lines.length - MAX_CART_LINES }} of them.
          </p>
          <p v-else class="mt-2 text-sm text-ink-gray-5">Set a quantity on at least one size.</p>
        </div>
      </div>
    </template>

    <template #actions>
      <div class="flex justify-end">
        <Button class="w-full sm:w-auto" label="Close" @click="open = false" />
      </div>
    </template>
  </Dialog>
</template>
