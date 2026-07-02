<template>
  <div :style="finalStyle" :title="'#'+speciesId" />
</template>

<script setup>
import { computed } from 'vue'
import { ICON_SHEET } from '../../utils/iconSheet'

const props = defineProps({ speciesId: { type: Number, required: true }, size: { type: String, default: 'md' } })

const sizes = { sm: 32, md: 40, lg: 40 }
const px = sizes[props.size] || ICON_SHEET.cell
const CELL = ICON_SHEET.cell, COLS = ICON_SHEET.cols, SHEET = ICON_SHEET.url

const finalStyle = computed(() => {
  const n = props.speciesId || 0
  const col = n % COLS, row = Math.floor(n / COLS)
  return {
    width: px + 'px', height: px + 'px',
    backgroundImage: `url(${SHEET})`,
    backgroundPosition: `-${col*CELL}px -${row*CELL}px`,
    backgroundSize: `${COLS*CELL}px auto`,
    backgroundRepeat: 'no-repeat',
    imageRendering: 'pixelated',
  }
})
</script>
