<template>
  <div class="space-y-2" ref="root">
    <label class="text-xs text-gray-500">特性</label>
    <div class="relative">
      <input v-model="search" @focus="onFocus" @input="onSearch" placeholder="搜索特性..."
        class="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1.5 text-xs text-gray-300 cursor-pointer" />
      <div v-if="showDropdown && results.length"
        class="absolute z-30 w-full mt-1 bg-gray-800 border border-gray-600 rounded-lg shadow-xl max-h-40 overflow-y-auto">
        <div v-for="ab in results" :key="ab.id" @mousedown.prevent="select(ab)"
          class="flex items-center gap-2 px-2 py-1.5 hover:bg-gray-700 cursor-pointer text-xs border-b border-gray-700/50">
          <span class="w-6 text-gray-500">#{{ ab.id }}</span>
          <span class="text-white">{{ ab.name }}</span>
        </div>
      </div>
    </div>
    <div v-if="modelValue" class="text-xs px-2 py-1 rounded bg-purple-900/30 text-purple-300 border border-purple-700/50">
      #{{ modelValue.id }} {{ modelValue.name }}
      <button @click="emit('update:modelValue',null)" class="text-purple-400 hover:text-red-300 ml-2">✕</button>
    </div>
    <div v-else class="text-xs text-gray-600">未选择</div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { searchAbilities } from '../../api/dataWs'

const props = defineProps({ modelValue: { type: Object, default: null } })
const emit = defineEmits(['update:modelValue'])

const search = ref(''); const results = ref([]); const showDropdown = ref(false)
const root = ref(null); let timer = null

onMounted(() => document.addEventListener('click', (e) => {
  if (root.value && !root.value.contains(e.target)) showDropdown.value = false
}))
onUnmounted(() => document.removeEventListener('click', () => {}))

async function onFocus() {
  showDropdown.value = true
  if (results.value.length === 0) {
    try { results.value = await searchAbilities('') } catch { results.value = [] }
  }
}
async function onSearch() {
  clearTimeout(timer); showDropdown.value = true
  timer = setTimeout(async () => {
    try { results.value = await searchAbilities(search.value) } catch { results.value = [] }
  }, 150)
}
function select(ab) {
  emit('update:modelValue', { id: ab.id, name: ab.name })
  search.value = ''; results.value = []; showDropdown.value = false
}
</script>
