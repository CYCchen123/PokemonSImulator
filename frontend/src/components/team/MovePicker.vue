<template>
  <div class="space-y-2" ref="root">
    <label class="text-xs text-gray-500">招式 (最多4个)</label>
    <div class="relative">
      <input v-model="search" @focus="onFocus" @input="onSearch" placeholder="搜索招式..."
        class="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1.5 text-xs text-gray-300 cursor-pointer" />
      <div v-if="showDropdown && results.length"
        class="absolute z-30 w-full mt-1 bg-gray-800 border border-gray-600 rounded-lg shadow-xl max-h-48 overflow-y-auto">
        <div v-for="mv in results" :key="mv.id" @mousedown.prevent="addMove(mv)"
          class="flex items-center gap-2 px-2 py-1.5 hover:bg-gray-700 cursor-pointer text-xs border-b border-gray-700/50">
          <span class="w-6 text-gray-500">#{{ mv.id }}</span>
          <span class="px-1 py-0.5 rounded text-white text-xs" :style="{ background: typeColor(mv.type) }">{{ mv.type || '???' }}</span>
          <span class="text-white">{{ mv.name }}</span>
          <span class="text-gray-500 ml-auto">{{ mv.power || '-' }}pwr</span>
        </div>
      </div>
    </div>
    <!-- Selected -->
    <div class="grid grid-cols-2 gap-1">
      <div v-for="(m,i) in modelValue" :key="i"
        class="flex items-center gap-1 px-2 py-1 rounded text-xs" :style="moveBg(m.type)">
        <span class="text-white">#{{ m.id }} {{ m.name }}</span>
        <button @click="removeMove(i)" class="text-white/70 hover:text-red-300 ml-auto">✕</button>
      </div>
      <div v-for="i in (4 - modelValue.length)" :key="'e'+i"
        class="px-2 py-1 rounded text-xs text-gray-600 border border-dashed border-gray-600 text-center">空位</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { searchMoves } from '../../api/dataWs'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  learnset: { type: Array, default: () => [] },  // allowed move IDs, empty = all moves
})
const emit = defineEmits(['update:modelValue'])

const search = ref(''); const results = ref([]); const showDropdown = ref(false)
const root = ref(null); let timer = null

const TYPE_COLORS = { Normal:'#A8A878',Fire:'#F08030',Water:'#6890F0',Electric:'#F8D030',Grass:'#78C850',
  Ice:'#98D8D8',Fighting:'#C03028',Poison:'#A040A0',Ground:'#E0C068',Flying:'#A890F0',
  Psychic:'#F85888',Bug:'#A8B820',Rock:'#B8A038',Ghost:'#705898',Dragon:'#7038F8',
  Dark:'#705848',Steel:'#B8B8D0',Fairy:'#EE99AC' }

function typeColor(t) { return TYPE_COLORS[t] || '#999' }
function moveBg(t) { const c = TYPE_COLORS[t]||'#999'; return { background: c+'44', border: '1px solid '+c+'66' } }

onMounted(() => document.addEventListener('click', (e) => {
  if (root.value && !root.value.contains(e.target)) showDropdown.value = false
}))
onUnmounted(() => document.removeEventListener('click', () => {}))

async function onFocus() {
  showDropdown.value = true
  if (results.value.length === 0) {
    try { results.value = await searchMoves('', props.learnset) } catch { results.value = [] }
  }
}
async function onSearch() {
  clearTimeout(timer); showDropdown.value = true
  timer = setTimeout(async () => {
    try { results.value = await searchMoves(search.value, props.learnset) } catch { results.value = [] }
  }, 150)
}
function addMove(mv) {
  if (props.modelValue.length >= 4) return
  if (props.modelValue.find(m => m.id === mv.id)) return
  emit('update:modelValue', [...props.modelValue, { id: mv.id, name: mv.name, type: mv.type }])
  search.value = ''; results.value = []; showDropdown.value = false
}
function removeMove(i) {
  const u = [...props.modelValue]; u.splice(i, 1); emit('update:modelValue', u)
}
</script>
