<template>
  <div :style="finalStyle" :title="'#'+speciesId" />
</template>

<script setup>
import { computed } from 'vue'
import { ICON_SHEET } from '../../utils/iconSheet'

const props = defineProps({
  speciesId: { type: Number, required: true },
  size: { type: String, default: 'md' },
})

const CELL = ICON_SHEET.cellW  // 96, square
const COLS = ICON_SHEET.cols
const SHEET = ICON_SHEET.url

function sheetPos(id) {
  const n = (id || 0) - 1
  if (n < 0) return { col: 0, row: 0 }
  return { col: n % COLS, row: Math.floor(n / COLS) }
}

const finalStyle = computed(() => {
  const { col, row } = sheetPos(props.speciesId)
  const px = dispSize.value
  const scale = px / CELL
  const sheetW = COLS * CELL * scale
  return {
    width: px + 'px',
    height: px + 'px',
    backgroundImage: `url(${SHEET})`,
    backgroundPosition: `-${col * px}px -${row * px}px`,
    backgroundSize: `${sheetW}px auto`,
    backgroundRepeat: 'no-repeat',
    imageRendering: 'pixelated',
  }
})

// Display sizes (96x96 source, square cells)
const sizeMap = {
  sm: 32,
  md: 48,
  lg: 96,
  xl: 128,
}
const dispSize = computed(() => sizeMap[props.size] || sizeMap.md)
</script>
