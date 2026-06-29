<template>
  <span
    v-if="status && status.id !== 0"
    class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold"
    :class="bgClass"
    :title="info.label"
  >
    {{ info.icon }} {{ info.label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { getStatusInfo } from '../../utils/enums'

const props = defineProps({ status: Object })
const info = computed(() => getStatusInfo(props.status?.id || 0))

const bgClass = computed(() => {
  const id = props.status?.id
  if (id === 1) return 'bg-orange-700 text-orange-200'
  if (id === 2) return 'bg-blue-700 text-blue-200'
  if (id === 3) return 'bg-yellow-600 text-yellow-200'
  if (id === 4 || id === 7) return 'bg-purple-700 text-purple-200'
  if (id === 5) return 'bg-gray-600 text-gray-200'
  return 'bg-gray-600 text-gray-300'
})
</script>
