<template>
  <div class="w-full bg-gray-700 rounded-full h-4 overflow-hidden border border-gray-600">
    <div
      class="hp-bar-fill h-full rounded-full"
      :class="barColor"
      :style="{ width: pct + '%' }"
    ></div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatHP, hpBarColor } from '../../utils/formatters'

const props = defineProps({ current: Number, max: Number })
const pct = computed(() => formatHP(props.current, props.max).pct)
const barColor = computed(() => hpBarColor(pct.value))
</script>
