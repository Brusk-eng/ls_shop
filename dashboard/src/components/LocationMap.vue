<script setup>
/**
 * One pin on an OpenStreetMap map, held as the GeoJSON a Frappe Geolocation field stores — so a
 * pin dropped here is the same pin Desk draws on the Address form, and the other way round.
 */
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Button } from 'frappe-ui'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'

const props = defineProps({
  modelValue: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

const WORLD_ZOOM = 2
const STREET_ZOOM = 16

// Leaflet finds its default marker by reading a CSS url at runtime, which Vite has already
// rewritten — so the default icon renders as a broken image unless it is handed over directly.
const icon = L.icon({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  shadowSize: [41, 41],
})

const container = ref(null)
let map = null
let marker = null
let resizeObserver = null

function readPoint(geojson) {
  try {
    const feature = JSON.parse(geojson).features?.find((item) => item.geometry?.type === 'Point')
    const [longitude, latitude] = feature?.geometry?.coordinates ?? []
    return Number.isFinite(latitude) && Number.isFinite(longitude) ? [latitude, longitude] : null
  } catch {
    return null
  }
}

function formatGeojson([latitude, longitude]) {
  return JSON.stringify({
    type: 'FeatureCollection',
    features: [
      { type: 'Feature', properties: {}, geometry: { type: 'Point', coordinates: [longitude, latitude] } },
    ],
  })
}

function placeMarker(point) {
  if (marker) {
    marker.setLatLng(point)
    return
  }

  marker = L.marker(point, { icon, draggable: true }).addTo(map)
  marker.on('dragend', () => savePin(marker.getLatLng()))
}

function savePin({ lat, lng }) {
  placeMarker([lat, lng])
  emit('update:modelValue', formatGeojson([lat, lng]))
}

function clearPin() {
  emit('update:modelValue', '')
}

// Moves the map and the pin together, for a search that found the address.
function moveTo(latitude, longitude) {
  map.setView([latitude, longitude], STREET_ZOOM)
  savePin({ lat: latitude, lng: longitude })
}

defineExpose({ moveTo })

onMounted(() => {
  const point = readPoint(props.modelValue)
  map = L.map(container.value).setView(point ?? [20, 0], point ? STREET_ZOOM : WORLD_ZOOM)
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors',
  }).addTo(map)

  if (point) placeMarker(point)
  map.on('click', (event) => savePin(event.latlng))

  // A map measured while its dialog is still animating open draws as a grey strip; it has to be
  // told once the box has its real size.
  resizeObserver = new ResizeObserver(() => map?.invalidateSize())
  resizeObserver.observe(container.value)
})

watch(
  () => props.modelValue,
  (geojson) => {
    const point = readPoint(geojson)
    if (!map) return
    if (!point) {
      marker?.remove()
      marker = null
      return
    }
    const current = marker?.getLatLng()
    if (current?.lat !== point[0] || current?.lng !== point[1]) placeMarker(point)
  },
)

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  map?.remove()
  map = null
  marker = null
})
</script>

<template>
  <div class="flex flex-col gap-2">
    <div ref="container" class="isolate h-64 w-full overflow-hidden rounded border border-outline-gray-2" />
    <div class="flex items-center justify-between gap-2">
      <p class="text-sm text-ink-gray-5">Click the map to drop the pin, then drag it to adjust.</p>
      <Button v-if="modelValue" label="Remove pin" variant="ghost" @click="clearPin" />
    </div>
  </div>
</template>
