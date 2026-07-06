<template>
  <div>
    <!-- Hero Banner -->
    <div class="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-800 via-indigo-900 to-slate-900 p-8 mb-8 text-white">
      <div class="absolute inset-0 opacity-10">
        <div class="absolute top-0 right-0 w-64 h-64 bg-blue-400 rounded-full blur-3xl" />
        <div class="absolute bottom-0 left-0 w-48 h-48 bg-indigo-400 rounded-full blur-3xl" />
      </div>
      <div class="relative">
        <div class="flex items-center justify-between flex-wrap gap-4 mb-4">
          <div>
            <h1 class="text-3xl font-bold mb-2">📊 深度数据洞察</h1>
            <p class="text-blue-200/80 text-sm">基于 Spark 分析的宝可梦对战大数据平台</p>
            <div class="flex gap-4 mt-3 text-xs text-blue-200/60">
              <span v-if="summaryData.elapsed">⚡ 分析耗时 {{ summaryData.elapsed }}s</span>
              <span v-if="summaryData.battles">⚔️ {{ summaryData.battles }} 场对战</span>
              <span v-if="summaryData.species">🐾 {{ summaryData.species }} 种精灵</span>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <!-- Battle Selector -->
            <div v-if="battleIds.length > 0" class="flex items-center gap-2">
              <span class="text-xs text-blue-200/60">对战选择</span>
              <select v-model="selectedBattle" @change="onBattleChange"
                class="text-sm px-4 py-2 rounded-full bg-white/10 border border-white/20 text-white cursor-pointer
                       hover:bg-white/20 focus:outline-none focus:ring-2 focus:ring-blue-400 transition-all
                       appearance-none bg-[url('data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20fill%3D%22white%22%20viewBox%3D%220%200%2020%2020%22%3E%3Cpath%20d%3D%22M6%208l4%204%204-4%22/%3E%3C/svg%3E')] bg-[length:16px] bg-[right_8px_center] bg-no-repeat pr-10">
                <option value="all" class="text-gray-900">全部对战</option>
                <option v-for="bid in battleIds" :key="bid" :value="bid" class="text-gray-900">
                  对战 #{{ bid }}
                </option>
              </select>
            </div>
            <div class="flex items-center gap-2">
              <!-- Auto-refresh toggle -->
              <div class="flex items-center gap-1.5">
                <button @click="autoRefresh = !autoRefresh"
                  class="relative w-10 h-5 rounded-full transition-colors duration-200"
                  :class="autoRefresh ? 'bg-emerald-400' : 'bg-white/20'">
                  <span class="absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-all duration-200"
                    :class="autoRefresh ? 'left-5' : 'left-0.5'" />
                </button>
                <span class="text-xs" :class="autoRefresh ? 'text-emerald-300' : 'text-blue-200/50'">
                  {{ autoRefresh ? `⏱ ${countdown}` : '定时' }}
                </span>
              </div>
              <!-- Live streaming toggle -->
              <div class="flex items-center gap-1.5">
                <button @click="liveMode = !liveMode"
                  class="relative w-10 h-5 rounded-full transition-colors duration-200"
                  :class="liveConnected ? 'bg-rose-400' : 'bg-white/20'">
                  <span class="absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-all duration-200"
                    :class="liveConnected ? 'left-5' : 'left-0.5'" />
                </button>
                <span class="flex items-center gap-1 text-xs" :class="liveConnected ? 'text-rose-300' : 'text-blue-200/50'">
                  <span v-if="liveConnected" class="relative flex h-2 w-2">
                    <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                    <span class="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span>
                  </span>
                  {{ liveConnected ? '📡 实时' : '📡 实时' }}
                </span>
              </div>
              <!-- Data gen toggle -->
              <div class="flex items-center gap-1.5">
                <button @click="toggleGen"
                  class="relative w-10 h-5 rounded-full transition-colors duration-200"
                  :class="genRunning ? 'bg-emerald-400' : 'bg-white/20'">
                  <span class="absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-all duration-200"
                    :class="genRunning ? 'left-5' : 'left-0.5'" />
                </button>
                <span class="text-xs" :class="genRunning ? 'text-emerald-300' : 'text-blue-200/50'">
                  {{ genRunning ? '⚡ 产数中' : '⚡ 产数' }}
                </span>
              </div>
              <button @click="doRefresh" :disabled="refreshing"
                class="px-6 py-3 rounded-full font-bold text-sm transition-all duration-300 flex items-center gap-2"
                :class="refreshing
                  ? 'bg-white/20 cursor-wait'
                  : 'bg-white/15 hover:bg-white/25 backdrop-blur shadow-lg hover:shadow-xl active:scale-95'">
                <span :class="refreshing ? 'animate-spin inline-block' : ''">🔄</span>
                {{ refreshing ? '分析中...' : '刷新分析' }}
              </button>
            </div>
          </div>
        </div>
        <!-- Battle info bar -->
        <div v-if="selectedBattle !== 'all'" class="flex gap-4 mt-2 text-xs">
          <span class="bg-white/10 px-3 py-1 rounded-full">🔍 查看对战 #{{ selectedBattle }} 详情</span>
          <button @click="selectedBattle = 'all'; onBattleChange()" class="bg-white/5 px-3 py-1 rounded-full hover:bg-white/15 transition-colors">✕ 显示全部</button>
        </div>
      </div>
    </div>

    <!-- Quick Stats -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
      <div v-for="card in quickCards" :key="card.label"
        class="glass-card p-5 text-center hover:shadow-lg hover:-translate-y-0.5 transition-all duration-300 cursor-default group">
        <div class="text-3xl mb-2 group-hover:scale-110 transition-transform duration-300">{{ card.icon }}</div>
        <div class="text-2xl font-bold" :class="card.color">{{ card.value }}</div>
        <div class="text-xs text-gray-400 mt-1">{{ card.label }}</div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="flex gap-1.5 mb-6 p-1 bg-gray-100/80 rounded-full w-fit">
      <button v-for="tab in tabs" :key="tab.key" @click="activeTab = tab.key"
        class="px-5 py-2 rounded-full text-sm font-medium transition-all duration-200"
        :class="activeTab === tab.key
          ? 'bg-white text-gray-900 shadow-sm'
          : 'text-gray-500 hover:text-gray-700'">
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab: Overview -->
    <div v-if="activeTab === 'overview'" class="space-y-6">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DataTable title="🐾 宝可梦使用率 Top 10" :columns="speciesCols" :rows="top10Rows" :loading="loading"
          search-placeholder="搜索精灵名称..." id-key="species_id" defaultSort="appearances"
          :stableHeight="true" :stableHeightPx="500" :clickable="true" @row-click="handleSpeciesRowClick" />
        <TypePieChart :loading="loading" />
      </div>
      <HpCurveLine :loading="loading" :battle-id="selectedBattle" />
    </div>

    <!-- Tab: Rankings -->
    <div v-if="activeTab === 'rankings'" class="space-y-6">
      <DataTable title="🐾 宝可梦排行" :columns="speciesCols" :rows="speciesRows" :loading="loading"
        search-placeholder="搜索精灵名称..." id-key="species_id" defaultSort="appearances"
        :stableHeight="true" :stableHeightPx="550"
        :clickable="true" :selectedId="selectedSpecies?.id" @row-click="handleSpeciesRowClick" />
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DataTable title="⚡ 招式使用排行" :columns="moveCols" :rows="moveRows" :loading="loading"
          search-placeholder="搜索招式..." id-key="move_id" defaultSort="times_seen"
          :stableHeight="true" :stableHeightPx="430" />
        <DataTable title="🎒 道具使用排行" :columns="itemCols" :rows="itemRows" :loading="loading"
          search-placeholder="搜索道具..." id-key="item_id" defaultSort="uses"
          :stableHeight="true" :stableHeightPx="400" />
      </div>
      <DataTable title="🌟 特性使用排行" :columns="abilityCols" :rows="abilityRows" :loading="loading"
        search-placeholder="搜索特性..." id-key="ability_id" defaultSort="uses"
        :stableHeight="true" :stableHeightPx="500" />
    </div>

    <!-- Tab: Battle Data -->
    <div v-if="activeTab === 'battle'" class="space-y-6">
      <HeadToHeadChart :loading="loading" />
      <TeamSynergyChart :loading="loading" />
    </div>

    <!-- Tab: Types -->
    <div v-if="activeTab === 'types'" class="space-y-6">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="lg:col-span-2"><TypePieChart :loading="loading" /></div>
        <DataTable title="🎨 属性分布" :columns="typeCols" :rows="typeRows" :loading="loading"
          search-placeholder="搜索属性..." id-key="type_id" defaultSort="appearances" />
      </div>
    </div>

    <!-- Tab: Scout -->
    <div v-if="activeTab === 'scout'">
      <ScoutReport />
    </div>

    <!-- Refresh toast -->
    <Transition name="toast">
      <div v-if="showToast" class="fixed bottom-6 right-6 bg-emerald-500 text-white px-5 py-3 rounded-xl shadow-lg text-sm font-medium flex items-center gap-2 z-50">
        ✅ {{ toastMsg }}
        <button @click="showToast = false" class="ml-2 opacity-60 hover:opacity-100">✕</button>
      </div>
    </Transition>

    <!-- Pokemon Detail Modal -->
    <PokemonDetailModal
      :visible="showDetailModal"
      :speciesId="selectedSpecies?.id"
      :speciesName="selectedSpecies?.name"
      @close="showDetailModal = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import { statsAPI } from '../api/stats'
import { connect, on, disconnect } from '../api/wsClient'

import TypePieChart from '../components/charts/TypePieChart.vue'
import TeamSynergyChart from '../components/charts/TeamSynergyChart.vue'
import HeadToHeadChart from '../components/charts/HeadToHeadChart.vue'
import HpCurveLine from '../components/charts/HpCurveLine.vue'
import EventBarChart from '../components/charts/EventBarChart.vue'
import DataTable from '../components/charts/DataTable.vue'
import ScoutReport from '../components/charts/ScoutReport.vue'
import PokemonDetailModal from '../components/pokemon/PokemonDetailModal.vue'

const loading = ref(true)
const refreshing = ref(false)
const activeTab = ref('overview')
const autoRefresh = ref(false)
const countdown = ref(300)
const liveMode = ref(true)  // default on for real-time monitoring
const liveConnected = ref(false)
const genRunning = ref(false)
let _unsubStats = null

let _timer = null
function startAutoRefresh() {
  stopAutoRefresh()
  _timer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      doRefresh()
      countdown.value = 300
    }
  }, 1000)
}
function stopAutoRefresh() {
  if (_timer) { clearInterval(_timer); _timer = null }
}

watch(autoRefresh, (val) => {
  if (val) { countdown.value = 300; startAutoRefresh() }
  else { stopAutoRefresh(); countdown.value = 300 }
})

// ── Live streaming mode ──────────────────────────────────────
async function startLiveMode() {
  try {
    const name = localStorage.getItem('trainer_name') || 'stats-viewer'
    await connect(name)
    liveConnected.value = true
    _unsubStats = on('stats_updated', () => {
      loadStreaming()
    })
  } catch (e) {
    console.error('Live mode connect failed:', e)
    liveMode.value = false
    liveConnected.value = false
  }
}
function stopLiveMode() {
  if (_unsubStats) { _unsubStats(); _unsubStats = null }
  liveConnected.value = false
}
watch(liveMode, (val) => {
  if (val) startLiveMode()
  else stopLiveMode()
})
onUnmounted(() => {
  stopAutoRefresh()
  stopLiveMode()
})
const showToast = ref(false)
const toastMsg = ref('')
const selectedBattle = ref('all')
const selectedSpecies = ref(null)
const showDetailModal = ref(false)

const stats = ref({})
const speciesRows = ref([])
const moveRows = ref([])
const itemRows = ref([])
const abilityRows = ref([])
const typeRows = ref([])
const top10Rows = computed(() => speciesRows.value.slice(0, 10))
const summaryData = ref({})
const _battleRows = ref([])
const _eventRows = ref([])

const battleIds = computed(() => {
  const ids = [...new Set(_battleRows.value.map(r => r.battle_id))]
  return ids.filter(Boolean).sort()
})

const tabs = [
  { key: 'overview', label: '📊 总览' },
  { key: 'rankings', label: '🏆 排行' },
  { key: 'battle', label: '⚔️ 对战数据' },
  { key: 'types', label: '🔥 属性分析' },
  { key: 'scout', label: '🔍 侦察对手' },
]

const quickCards = computed(() => [
  { icon: '⚡', value: stats.value.total_battles || summaryData.value.battles || '-', label: '总对战', color: 'text-amber-500' },
  { icon: '👤', value: stats.value.total_players || '-', label: '训练家', color: 'text-rose-500' },
  { icon: '🐾', value: summaryData.value.species || '-', label: '精灵种类', color: 'text-blue-500' },
  { icon: '🔄', value: summaryData.value.turns || '-', label: '总回合', color: 'text-emerald-500' },
])

const speciesCols = [
  { key: 'species_name', label: '精灵', sortable: true, image: 'sprite_url' },
  { key: 'appearances', label: '出场', sortable: true, spark: true, class: 'text-right' },
]
const moveCols = [
  { key: 'move_name', label: '招式', sortable: true },
  { key: 'times_seen', label: '使用次数', sortable: true, spark: true, class: 'text-right' },
]
const itemCols = [
  { key: 'item_name', label: '道具', sortable: true },
  { key: 'uses', label: '携带次数', sortable: true, spark: true, class: 'text-right' },
]
const abilityCols = [
  { key: 'ability_name', label: '特性', sortable: true },
  { key: 'uses', label: '携带次数', sortable: true, spark: true, class: 'text-right' },
]
const typeCols = [
  { key: 'type_name', label: '属性', sortable: true },
  { key: 'appearances', label: '出现次数', sortable: true, spark: true, class: 'text-right' },
]

function onBattleChange() {
  // Trigger chart re-render by forcing reactivity
  _battleRows.value = [..._battleRows.value]
  _eventRows.value = [..._eventRows.value]
}

function handleSpeciesRowClick(row) {
  selectedSpecies.value = { id: row.species_id, name: row.species_name || '???' }
  showDetailModal.value = true
}

async function loadAllData() {
  loading.value = true
  try {
    const [summary, meta, moves, items, abilities, types, survival, battle, events, global] = await Promise.all([
      statsAPI.deepSummary().catch(() => ({ data: {} })),
      statsAPI.deepMeta().catch(() => ({ data: [] })),
      statsAPI.deepMoves().catch(() => ({ data: [] })),
      statsAPI.deepItems().catch(() => ({ data: [] })),
      statsAPI.deepAbilities().catch(() => ({ data: [] })),
      statsAPI.deepTypes().catch(() => ({ data: [] })),
      statsAPI.deepSurvival().catch(() => ({ data: [] })),
      statsAPI.deepBattle().catch(() => ({ data: [] })),
      statsAPI.deepEvents().catch(() => ({ data: [] })),
      statsAPI.global().catch(() => ({ data: {} })),
    ])
    const s = (summary.data || summary) || {}
    const sm = s.summaries || {}
    summaryData.value = {
      elapsed: s.elapsed_seconds, modules: s.modules,
      battles: sm.battle?.total_battles, turns: sm.battle?.total_turns,
      species: sm.meta?.total_species_seen, eventTypes: sm.events?.unique_event_types,
      topType: sm.types?.most_common_type, bdataSpecies: sm.bdata?.total_bdata_species,
    }
    stats.value = global.data || {}
    const rawSpecies = (meta.data || meta || [])
    rawSpecies.sort((a, b) =>
      (b.appearances || 0) - (a.appearances || 0) ||
      String(a.species_name || '').localeCompare(String(b.species_name || ''))
    )
    speciesRows.value = rawSpecies
    moveRows.value = moves.data || moves || []
    itemRows.value = items.data || items || []
    abilityRows.value = abilities.data || abilities || []
    console.log('loadAllData done:', {species: speciesRows.value.length, moves: moveRows.value.length, items: itemRows.value.length, abilities: abilityRows.value.length})
    typeRows.value = types.data || types || []
    _battleRows.value = battle.data || battle || []
    _eventRows.value = events.data || events || []
  } catch (e) {
    console.error('Failed to load data:', e)
  } finally {
    loading.value = false
  }
}

// Staggered streaming refresh — updates roll in one by one
const _staggerTimer = ref(null)
async function loadStreaming() {
  // Single request for live mode — instant update
  try {
    const pkg = await statsAPI.deepLive().catch(() => ({ data: null }))
    const d = (pkg.data || pkg) || {}
    if (!d.species_usage) return
    const sm = (d.summary && d.summary.summaries) || {}
    stats.value = {}  // clear stale stats so quick cards use summaryData fallback
    summaryData.value = {
      battles: sm.battle?.total_battles, turns: sm.battle?.total_turns,
      species: sm.meta?.total_species_seen,
    }
    const rawSpecies = d.species_usage || []
    rawSpecies.sort((a, b) => (b.appearances || 0) - (a.appearances || 0) ||
      String(a.species_name || '').localeCompare(String(b.species_name || '')))
    speciesRows.value = rawSpecies
    moveRows.value = d.move_usage || []
    itemRows.value = d.item_usage || []
    abilityRows.value = d.ability_usage || []
    typeRows.value = d.type_distribution || []
    _battleRows.value = d.hp_curve || []
    _eventRows.value = d.event_distribution || []
  } catch (e) { console.error('Stream update failed:', e) }
}

async function doRefresh() {
  refreshing.value = true
  if (autoRefresh.value) {
    toastMsg.value = '⏱ 自动刷新中...'
  } else {
    toastMsg.value = '正在重新分析对战数据...'
  }
  showToast.value = true
  try {
    await statsAPI.deepRefresh()
    await loadAllData()
    selectedBattle.value = 'all'
    countdown.value = 300
    toastMsg.value = autoRefresh.value ? '⏱ 下次刷新: 5分钟后' : '分析完成！数据已刷新'
  } catch {
    toastMsg.value = '分析完成'
  }
  refreshing.value = false
  setTimeout(() => { showToast.value = false }, 3000)
}

async function toggleGen() {
  const api = genRunning.value ? '/api/v1/cluster/gen/stop' : '/api/v1/cluster/gen/start'
  try {
    const resp = await fetch(api, { method: 'POST' })
    const d = await resp.json()
    if (d.ok) genRunning.value = !genRunning.value
  } catch { /* cluster only */ }
}

async function checkGenStatus() {
  try {
    const resp = await fetch('/api/v1/cluster/gen/status')
    const d = await resp.json()
    genRunning.value = d.running
  } catch {}
}

onMounted(async () => {
  await loadAllData()
  if (liveMode.value) startLiveMode()
  checkGenStatus()
})
</script>

<style scoped>
.toast-enter-active { transition: all 0.3s ease; }
.toast-leave-active { transition: all 0.2s ease; }
.toast-enter-from { opacity: 0; transform: translateY(20px); }
.toast-leave-to { opacity: 0; transform: translateY(10px); }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.animate-spin { animation: spin 1s linear infinite; }
</style>
