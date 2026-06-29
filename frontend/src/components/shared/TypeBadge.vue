<template>
  <span v-if="info && info.label !== '未知'"
    class="type-badge"
    :style="{ backgroundColor: info.color }"
  >
    {{ info.label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { getTypeInfo } from '../../utils/enums'

const props = defineProps({ typeId: { type: Number, default: -1 } })
const info = computed(() => {
  if (props.typeId == null || props.typeId < 0) return null
  return getTypeInfo(props.typeId)
})
</script>
