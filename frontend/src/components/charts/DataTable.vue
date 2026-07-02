<template>
  <div class="glass-card p-5">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-base font-bold text-gray-800">{{ title }}</h3>
      <div class="flex gap-2">
        <input v-model="search" @input="applyFilter" :placeholder="searchPlaceholder"
          class="text-xs px-3 py-1.5 rounded-full bg-gray-50 border border-gray-200 focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-300 w-40 transition-all" />
        <select v-model="sortBy" @change="onSortChange"
          class="text-xs px-2 py-1.5 rounded-full bg-gray-50 border border-gray-200 cursor-pointer">
          <option v-for="col in sortableCols" :key="col.key" :value="col.key">{{ col.label }}</option>
        </select>
        <button @click="toggleDir"
          class="text-xs px-2 py-1 rounded-full bg-gray-50 border border-gray-200 hover:bg-gray-100 transition-colors">
          {{ dir === 'desc' ? '↓' : '↑' }}
        </button>
      </div>
    </div>

    <!-- Loading skeleton -->
    <div v-if="loading" class="space-y-2">
      <div v-for="i in 8" :key="i" class="h-8 rounded-lg bg-gradient-to-r from-gray-100 via-gray-50 to-gray-100 animate-shimmer bg-[length:200%_100%]" />
    </div>

    <!-- Empty -->
    <div v-else-if="filtered.length === 0" class="text-center py-16 text-gray-400">
      <div class="text-4xl mb-3">🔍</div>
      <p class="text-sm">{{ emptyText }}</p>
    </div>

    <!-- Table -->
    <div v-else class="overflow-x-auto" :class="{ 'table-wrap': stableHeight }"
      :style="stableHeight ? { height: stableHeightPx + 'px' } : {}">
      <table class="w-full text-sm" :class="{ 'stable-table': stableHeight, 'no-anim': _skip }">
        <thead>
          <tr class="text-left text-gray-400 text-xs border-b border-gray-200">
            <th class="pb-2 w-8 font-normal">#</th>
            <th v-for="col in columns" :key="col.key" class="pb-2 font-normal" :class="col.class || ''">
              {{ col.label }}
            </th>
          </tr>
        </thead>
        <TransitionGroup name="table-row" tag="tbody">
          <tr v-for="(row, i) in pagedData" :key="row[idKey]"
            class="rank-row"
            :class="{
              'cursor-pointer': clickable,
              'rank-row-selected': clickable && selectedId === row[idKey],
              'invisible': row._slot,
            }"
            @click="handleRowClick(row)">
            <td class="rank-num">{{ (page - 1) * perPage + i + 1 }}</td>
            <td v-for="(col, ci) in columns" :key="col.key"
              class="py-2.5 pill-cell"
              :class="[col.class || '', ci === 0 ? 'pill-first' : '', ci === columns.length - 1 ? 'pill-last' : '']"
              v-html="formatCell(row, col, i)" />
          </tr>
        </TransitionGroup>
      </table>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="flex justify-between items-center mt-4 pt-3 border-t border-gray-100">
        <span class="text-xs text-gray-400">{{ filtered.length }} 条结果，第 {{ page }}/{{ totalPages }} 页</span>
        <div class="flex gap-1">
          <button v-for="p in pageButtons" :key="p" @click="page = p"
            :class="p === page ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
            class="w-7 h-7 text-xs rounded-full transition-colors font-medium">
            {{ p }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'

const props = defineProps({
  title: { type: String, default: '数据表' },
  columns: { type: Array, default: () => [] }, // [{key, label, class?, format?}]
  rows: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  searchPlaceholder: { type: String, default: '搜索...' },
  emptyText: { type: String, default: '暂无可显示的数据' },
  idKey: { type: String, default: 'id' },
  clickable: { type: Boolean, default: false },
  selectedId: { type: [String, Number], default: null },
  defaultSort: { type: String, default: '' },
  stableHeight: { type: Boolean, default: false },
  stableHeightPx: { type: Number, default: 500 },
})

const emit = defineEmits(['row-click'])

const search = ref('')
const sortBy = ref('')
const dir = ref('desc')
const page = ref(1)
const perPage = 10

const sortableCols = computed(() =>
  props.columns.filter(c => c.sortable !== false).map(c => ({ key: c.key, label: c.label }))
)

const filtered = ref([])
const _display = ref(null)  // animation display buffer, null = use filtered

function applyFilter() {
  const q = search.value.toLowerCase().trim()
  filtered.value = q
    ? props.rows.filter(r => props.columns.some(c => String(r[c.key] || '').toLowerCase().includes(q)))
    : [...props.rows]
  page.value = 1
  applySort()
}

function onSortChange() {
  _queueId++
  _skip.value = true
  const col = props.columns.find(c => c.key === sortBy.value)
  dir.value = (col && col.spark) ? 'desc' : 'asc'
  const target = [...filtered.value]
  const fn = col?.sortFn || ((a, b) => {
    const va = a[sortBy.value], vb = b[sortBy.value]
    if (typeof va === 'number' && typeof vb === 'number') return va - vb
    return String(va).localeCompare(String(vb))
  })
  target.sort((a, b) => dir.value === 'desc' ? fn(b, a) : fn(a, b))
  filtered.value = target
  setTimeout(() => { _skip.value = false }, 100)
}

// Instant page changes — no animation
watch(page, () => {
  _skip.value = true
  setTimeout(() => { _skip.value = false }, 100)
})

function applySort() {
  if (!sortBy.value) return
  // Pre-sort text columns A-Z for stable tie-breaking (JS sort is stable)
  for (const col of props.columns) {
    if (col.key === sortBy.value) continue
    if (!col.spark && !col.format && col.sortable !== false) {
      filtered.value.sort((a, b) => String(a[col.key] || '').localeCompare(String(b[col.key] || '')))
    }
  }
  // Primary sort with direction
  const col = props.columns.find(c => c.key === sortBy.value)
  const fn = col?.sortFn || ((a, b) => {
    const va = a[sortBy.value], vb = b[sortBy.value]
    if (typeof va === 'number' && typeof vb === 'number') return va - vb
    return String(va).localeCompare(String(vb))
  })
  filtered.value.sort((a, b) => dir.value === 'desc' ? fn(b, a) : fn(a, b))
}

function toggleDir() { dir.value = dir.value === 'desc' ? 'asc' : 'desc'; applySort() }

// ── Rank movement tracking ──────────────────────────
const prevOrder = ref(new Map())
const moveDirs = ref(new Map())

watch(() => props.rows, () => {
  try {
    const rows = pagedData.value || []
    const idKey = props.idKey || 'id'
    const old = prevOrder.value
    const cur = new Map()
    rows.forEach((row, i) => { if (row && row[idKey] != null) cur.set(row[idKey], i) })
    const dirs = new Map()
    cur.forEach((newIdx, id) => {
      if (!old.has(id)) return
      const oldIdx = old.get(id)
      if (newIdx < oldIdx) dirs.set(id, 'up')
      else if (newIdx > oldIdx) dirs.set(id, 'down')
    })
    moveDirs.value = dirs
    prevOrder.value = cur
    if (dirs.size > 0) setTimeout(() => moveDirs.value = new Map(), 10000)
  } catch {}
}, { immediate: true })

function rowMoveClass(row) {
  try { return moveDirs.value.get(row?.[props.idKey || 'id']) || '' } catch { return '' }
}

// ── Row enter animation ──────────────────────────────
function onRowEnter(el, done) {
  // Disable JS enter — let CSS transition handle it for consistent 4s timing
  done()
}

function handleRowClick(row) {
  if (props.clickable) {
    emit('row-click', row)
  }
}

const pagedData = computed(() => {
  const source = _display.value || filtered.value
  const start = (page.value - 1) * perPage
  const items = source.slice(start, start + perPage)
  if (props.stableHeight) {
    while (items.length < perPage) {
      items.push({ _slot: true, [props.idKey || 'id']: `_slot_${items.length}` })
    }
  }
  return items
})

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / perPage)))

const pageButtons = computed(() => {
  if (totalPages.value <= 7) return Array.from({ length: totalPages.value }, (_, i) => i + 1)
  const pages = []
  for (let i = 1; i <= 3; i++) pages.push(i)
  if (page.value > 4) pages.push('...')
  for (let i = Math.max(4, page.value - 1); i <= Math.min(totalPages.value - 3, page.value + 1); i++) pages.push(i)
  if (page.value < totalPages.value - 3) pages.push('...')
  for (let i = totalPages.value - 2; i <= totalPages.value; i++) pages.push(i)
  return [...new Set(pages)]
})

function formatCell(row, col, i) {
  const value = row[col.key]
  if (col.format) return col.format(value, row)
  // Image/sprite column
  if (col.image) {
    const url = row[col.image] || value
    const fallback = col.fallback || ''
    return url
      ? `<div class="flex items-center gap-2"><img src="${url}" alt="" class="w-8 h-8 object-contain rounded-full bg-gray-50" onerror="this.style.display='none'" /><span class="text-gray-700 font-medium">${fallback || row[col.key] || ''}</span></div>`
      : (fallback || value || '')
  }
  // Sparkline bars for numeric values
  if (col.spark && typeof value === 'number') {
    const max = Math.max(...filtered.value.map(r => r[col.key] || 0))
    const pct = max > 0 ? (value / max) * 100 : 0
    return `<div class="flex items-center gap-2"><div class="flex-1 h-2 rounded-full bg-gray-100 overflow-hidden"><div class="h-full rounded-full bg-gradient-to-r from-blue-400 to-blue-500 transition-all duration-500" style="width:${pct}%"></div></div><span class="text-xs text-gray-600 w-12 text-right font-mono">${value}</span></div>`
  }
  return value
}

// ── Sequential row-by-row swap animation ─────────────
let _queueId = 0
const _skip = ref(false)

async function _runSwapQueue(queue, target, idKey, qid) {
  const arr = [...(_display.value || filtered.value)]
  _display.value = arr
  for (const { id, to } of queue) {
    if (qid !== _queueId) { _display.value = null; return }
    const curIdx = arr.findIndex(r => r?.[idKey] === id)
    if (curIdx === -1 || curIdx === to) continue
    const [row] = arr.splice(curIdx, 1)
    arr.splice(to, 0, row)
    _display.value = [...arr]
    await new Promise(r => setTimeout(r, 1000))
  }
  if (qid === _queueId) _display.value = null  // animation done, restore filtered
}

let _tick = 0

async function _tickUpdate(target) {
  const tick = ++_tick
  const idKey = props.idKey || 'id'
  const old = filtered.value
  if (old.length === 0) { filtered.value = target; applySort(); return }

  // Find rows whose rank actually changed, sorted by new rank (top first)
  const moved = []
  old.forEach((row, oldIdx) => {
    const newIdx = target.findIndex(r => r?.[idKey] === row?.[idKey])
    if (newIdx !== -1 && newIdx !== oldIdx) moved.push({ row, oldIdx, newIdx })
  })
  moved.sort((a, b) => a.newIdx - b.newIdx)

  // Update values for ALL rows first (instant)
  const map = new Map(target.map(r => [r?.[idKey], r]).filter(([k]) => k != null))
  for (const row of old) {
    const next = map.get(row?.[idKey])
    if (next) Object.assign(row, next)
  }

  // Move one row per second, top rank first
  for (const { row, oldIdx, newIdx } of moved) {
    if (tick !== _tick) return
    const arr = filtered.value
    const cur = arr.findIndex(r => r?.[idKey] === row[idKey])
    if (cur === -1 || cur === newIdx) continue
    arr.splice(newIdx, 0, arr.splice(cur, 1)[0])
    filtered.value = [...arr]
    await new Promise(r => setTimeout(r, 1000))
  }
  if (tick === _tick) { filtered.value = target; applySort() }
}

watch(() => props.rows, (rows) => {
  page.value = 1
  const target = [...rows]
  if (sortableCols.value.length > 0) {
    if (!sortBy.value) {
      const preferred = props.defaultSort || sortableCols.value[0].key
      sortBy.value = sortableCols.value.find(c => c.key === preferred)?.key || sortableCols.value[0].key
    }
    for (const c of props.columns) {
      if (c.key === sortBy.value) continue
      if (!c.spark && !c.format && c.sortable !== false) {
        target.sort((a, b) => String(a[c.key] || '').localeCompare(String(b[c.key] || '')))
      }
    }
    const col = props.columns.find(c => c.key === sortBy.value)
    const fn = col?.sortFn || ((a, b) => {
      const va = a[sortBy.value], vb = b[sortBy.value]
      if (typeof va === 'number' && typeof vb === 'number') return va - vb
      return String(va).localeCompare(String(vb))
    })
    target.sort((a, b) => dir.value === 'desc' ? fn(b, a) : fn(a, b))
  }
  _tickUpdate(target)
}, { immediate: true })
</script>

<style scoped>
/* ── Rank sliding animation (leaderboard style) ────── */
/* 5s cycle: 0-1s fade → 0-3s slide → 3-5s idle */
.table-row-move,
.table-row-enter-active,
.table-row-leave-active {
  opacity: 0.55;
  transition: opacity 0.5s linear;
}
.table-row-move {
  transition: opacity 0.5s linear, transform 0.5s linear;
  z-index: 0;
}
.table-row-enter-active {
  transition: opacity 1.5s linear, transform 1.5s linear;
}
.stable-table .table-row-enter-active {
  transition: opacity 0.5s linear 0.5s, transform 0.5s linear 0.5s;
}
.stable-table .table-row-leave-active {
  transition: opacity 0.5s linear, transform 0.5s ease;
}
.stable-table .table-row-enter-from {
  opacity: 0;
  transform: translateY(60px) scale(1);
}
.stable-table .table-row-leave-to {
  opacity: 0;
  transform: translateY(60px) scale(1);
}



/* ── Rank number ────────────────────────────────── */
.rank-num {
  font-size: 0.7rem;
  color: #9ca3af;
  font-family: monospace;
  width: 1.5rem;
}

/* ── White pill-shaped rows ──────────────────────── */
.pill-cell {
  background: #fff;
  padding-top: 0.45rem;
  padding-bottom: 0.45rem;
  border: none !important;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.pill-first {
  border-radius: 20px 0 0 20px !important;
  padding-left: 1rem !important;
}
.pill-last {
  border-radius: 0 20px 20px 0 !important;
  padding-right: 1rem !important;
}
.rank-row:hover .pill-cell {
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

/* Stacking: moving rows slide UNDER stationary rows */
tbody {
  position: relative;
  isolation: isolate;
}
.rank-row {
  position: relative;
  z-index: 1;
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
.animate-shimmer { animation: shimmer 1.5s infinite; }

/* Fixed table area — never changes size */
.table-wrap {
  overflow: hidden;
}
.no-anim .table-row-move,
.no-anim .table-row-enter-active,
.no-anim .table-row-leave-active {
  transition: none !important;
  animation: none !important;
}

</style>
