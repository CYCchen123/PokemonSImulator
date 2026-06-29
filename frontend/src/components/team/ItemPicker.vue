<template>
  <div class="space-y-2" ref="root">
    <label class="text-xs text-gray-500 font-medium">携带道具</label>
    <div class="relative">
      <input v-model="search" @focus="onFocus" @input="onSearch" placeholder="🔍 搜索道具..."
        class="w-full bg-white/70 border border-gray-200 rounded-xl px-3 py-2 text-xs text-gray-700 focus:outline-none focus:ring-2 focus:ring-pokeball-red/30 transition-all" />
      <div v-if="showDropdown && results.length"
        class="absolute z-30 w-full mt-1 glass-card shadow-xl max-h-40 overflow-y-auto rounded-xl">
        <div v-for="it in results" :key="it.id" @mousedown.prevent="select(it)"
          class="flex items-center gap-3 px-3 py-2 hover:bg-pokeball-red/5 cursor-pointer text-xs border-b border-gray-100 last:border-0 transition-colors">
          <img :src="itemIconUrl(it.name)" class="w-6 h-6 rounded" @error="e=>e.target.style.display='none'" />
          <span class="text-gray-800 font-medium flex-1">{{ it.name }}</span>
          <span class="text-gray-400">#{{ it.id }}</span>
        </div>
      </div>
    </div>
    <div v-if="modelValue" class="flex items-center gap-2 text-xs px-3 py-2 rounded-xl bg-pokeball-red/5 border border-pokeball-red/20">
      <img :src="itemIconUrl(modelValue.name)" class="w-5 h-5 rounded" @error="e=>e.target.style.display='none'" />
      <span class="text-pokeball-red font-medium">{{ modelValue.name }}</span>
      <span class="text-gray-400">#{{ modelValue.id }}</span>
      <button @click="emit('update:modelValue',null)" class="ml-auto text-gray-400 hover:text-red-500 transition-colors">✕</button>
    </div>
    <div v-else class="text-xs text-gray-400 px-1">未选择道具</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { request, connect } from '../../api/wsClient'

const props = defineProps({ modelValue: { type: Object, default: null } })
const emit = defineEmits(['update:modelValue'])

const search = ref(''); const results = ref([]); const showDropdown = ref(false)
const root = ref(null); let timer = null
let _ready = false

function itemIconUrl(name) {
  if (!name) return ''
  const slug = name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '')
  return `/items/${slug}.png`
}

async function ensure() {
  if (!_ready) { await connect('ItemPicker'); _ready = true }
}

onMounted(() => document.addEventListener('click', (e) => {
  if (root.value && !root.value.contains(e.target)) showDropdown.value = false
}))

async function onFocus() {
  showDropdown.value = true
  if (results.value.length === 0) {
    await ensure()
    try { results.value = await request('get_items', { search: '' }) } catch { results.value = [] }
  }
}
async function onSearch() {
  clearTimeout(timer); showDropdown.value = true
  timer = setTimeout(async () => {
    await ensure()
    try { results.value = await request('get_items', { search: search.value }) } catch { results.value = [] }
  }, 150)
}
function select(it) {
  emit('update:modelValue', { id: it.id, name: it.name })
  search.value = ''; results.value = []; showDropdown.value = false
}
</script>
