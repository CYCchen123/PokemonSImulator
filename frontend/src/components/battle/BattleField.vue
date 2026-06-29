<template>
  <div class="battle-bg rounded-xl p-6 border border-gray-700">
    <!-- Weather & Field indicators -->
    <div class="flex justify-center gap-4 mb-4">
      <span v-if="weatherText" class="text-xs px-3 py-1 rounded-full bg-gray-700/80 text-gray-300">
        {{ weatherText }}
      </span>
      <span v-if="fieldText" class="text-xs px-3 py-1 rounded-full bg-gray-700/80 text-gray-300">
        {{ fieldText }}
      </span>
      <span class="text-xs px-3 py-1 rounded-full bg-gray-700/80 text-gray-400">
        Turn {{ turn }}
      </span>
    </div>

    <!-- Two sides: opponent (top), player (bottom) -->
    <div class="grid grid-cols-2 gap-8 max-w-3xl mx-auto">
      <SidePanel :side="sideB" :show-bench="true" />
      <SidePanel :side="sideA" :show-bench="true" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import SidePanel from './SidePanel.vue'
import { getWeatherInfo, getFieldInfo } from '../../utils/enums'

const props = defineProps({
  sideA: { type: Object, default: null },
  sideB: { type: Object, default: null },
  weather: { type: Object, default: () => ({ type: 0 }) },
  field: { type: Object, default: () => ({ type: 0 }) },
  turn: { type: Number, default: 0 },
})

const weatherInfo = computed(() => getWeatherInfo(props.weather?.type || 0))
const weatherText = computed(() => {
  if (props.weather?.type === 0) return null
  return `${weatherInfo.value.icon} ${weatherInfo.value.label}`
})
const fieldInfo = computed(() => getFieldInfo(props.field?.type || 0))
const fieldText = computed(() => {
  if (props.field?.type === 0) return null
  return `${fieldInfo.value.label}`
})
</script>
