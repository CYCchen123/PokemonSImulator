<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-800 mb-6">▶️ 对战回放</h1>

    <div v-if="!battleId" class="text-center text-gray-400 py-16">
      <p>请从 <router-link to="/history" class="text-pokeball-red font-medium">对战历史</router-link> 中选择一场对战进行回放</p>
    </div>

    <div v-else class="space-y-6">
      <!-- Replay Controls -->
      <div class="glass-card p-4 flex items-center gap-4 flex-wrap">
        <button @click="prevEvent" class="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-600 rounded-full text-sm font-medium transition-colors">
          ⏮ 上一步
        </button>
        <button @click="nextEvent" class="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-600 rounded-full text-sm font-medium transition-colors">
          下一步 ⏭
        </button>
        <span class="text-sm text-gray-500 font-medium">
          Event {{ currentEventIndex + 1 }} / {{ events.length }}
          <span v-if="currentEvent" class="ml-2 text-gray-400">
            Turn {{ currentEvent.turn_index }} · {{ currentEvent.event_type }}
          </span>
        </span>
      </div>

      <!-- Battle Field (snapshot at current event) -->
      <BattleField
        v-if="battleStore.battleState"
        :side-a="battleStore.sideA"
        :side-b="battleStore.sideB"
        :turn="currentTurn"
      />

      <!-- Event Timeline -->
      <BattleTimeline :events="events.slice(0, currentEventIndex + 1)" />

      <LoadingSpinner v-if="loading" text="加载回放数据..." />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useBattleStore } from '../stores/battleStore'
import BattleField from '../components/battle/BattleField.vue'
import BattleTimeline from '../components/battle/BattleTimeline.vue'
import LoadingSpinner from '../components/shared/LoadingSpinner.vue'

const route = useRoute()
const battleStore = useBattleStore()
const battleId = computed(() => route.params.id)
const loading = ref(false)
const currentEventIndex = ref(0)
const events = ref([])
const currentTurn = ref(0)

const currentEvent = computed(() => events.value[currentEventIndex.value])

function nextEvent() {
  if (currentEventIndex.value < events.value.length - 1) {
    currentEventIndex.value++
    if (currentEvent.value) {
      currentTurn.value = currentEvent.value.turn_index
    }
  }
}

function prevEvent() {
  if (currentEventIndex.value > 0) {
    currentEventIndex.value--
    if (currentEvent.value) {
      currentTurn.value = currentEvent.value.turn_index
    }
  }
}

onMounted(async () => {
  if (!battleId.value) return
  loading.value = true
  try {
    await battleStore.loadBattle(battleId.value)
    events.value = battleStore.events
  } catch (e) {
    console.error('Failed to load replay:', e)
  } finally {
    loading.value = false
  }
})
</script>
