<template>
  <div class="bg-gray-800 rounded-lg p-4 border border-gray-700">
    <h3 class="text-sm font-bold text-gray-300 uppercase mb-3">🎮 行动选择</h3>

    <!-- Side selector tabs -->
    <div class="flex gap-2 mb-4">
      <button v-for="s in ['a', 'b']" :key="s"
        @click="activeSide = s"
        class="px-3 py-1.5 rounded text-sm font-medium transition-colors"
        :class="activeSide === s ? 'bg-red-600 text-white' : 'bg-gray-700 text-gray-400 hover:bg-gray-600'"
      >
        Side {{ s.toUpperCase() }}
      </button>
    </div>

    <!-- Action type tabs -->
    <div class="flex gap-2 mb-4 flex-wrap">
      <button v-for="t in actionTypes" :key="t.value"
        @click="actionType = t.value"
        class="px-3 py-1 rounded text-xs font-medium transition-colors"
        :class="actionType === t.value ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-400 hover:bg-gray-600'"
      >
        {{ t.label }}
      </button>
    </div>

    <!-- Move selection -->
    <div v-if="actionType === 'attack'" class="space-y-2">
      <p class="text-xs text-gray-500">选择招式:</p>
      <div class="grid grid-cols-2 gap-2">
        <button v-for="(move, i) in moves" :key="i"
          @click="selectedMove = i"
          class="text-left px-3 py-2 rounded text-sm transition-colors"
          :class="selectedMove === i ? 'bg-blue-600/30 border border-blue-500 text-white' : 'bg-gray-700 text-gray-400 border border-transparent hover:border-gray-500'"
        >
          <div class="font-medium">#{{ move.id }}</div>
          <div class="text-xs text-gray-500">PP: {{ move.pp }}/{{ move.maxPp }}</div>
        </button>
      </div>
    </div>

    <!-- Switch selection -->
    <div v-if="actionType === 'switch'" class="space-y-2">
      <p class="text-xs text-gray-500">选择换上的宝可梦 (slot):</p>
      <div class="grid grid-cols-3 gap-2">
        <button v-for="i in 6" :key="i"
          @click="selectedSwitch = i - 1"
          class="px-3 py-2 rounded text-sm text-center transition-colors"
          :class="selectedSwitch === (i - 1) ? 'bg-green-600/30 border border-green-500 text-white' : 'bg-gray-700 text-gray-400 border border-transparent hover:border-gray-500'"
        >
          Slot {{ i - 1 }}
        </button>
      </div>
    </div>

    <!-- Pass -->
    <div v-if="actionType === 'pass'" class="text-center text-gray-500 text-sm py-4">
      跳过本回合行动
    </div>

    <!-- Submit -->
    <button
      @click="submitAction"
      class="w-full mt-4 py-2 rounded font-bold text-white transition-colors"
      :class="canSubmit ? 'bg-red-600 hover:bg-red-500' : 'bg-gray-600 cursor-not-allowed'"
      :disabled="!canSubmit"
    >
      ⚡ 确认行动
    </button>

    <!-- Queue preview -->
    <div v-if="actionQueue.length > 0" class="mt-3 pt-3 border-t border-gray-700">
      <p class="text-xs text-gray-500 mb-2">待提交队列:</p>
      <div v-for="(a, i) in actionQueue" :key="i"
        class="text-xs px-2 py-1 rounded bg-gray-700 text-gray-400 flex justify-between"
      >
        <span>Side {{ a.side.toUpperCase() }}: {{ a.type }}</span>
        <button @click="removeAction(i)" class="text-red-400 hover:text-red-300">✕</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const emit = defineEmits(['submit'])

const props = defineProps({
  moves: { type: Array, default: () => [] },
})

const activeSide = ref('a')
const actionType = ref('attack')
const selectedMove = ref(0)
const selectedSwitch = ref(0)
const actionQueue = ref([])

const actionTypes = [
  { value: 'attack', label: '⚔️ 攻击' },
  { value: 'switch', label: '🔄 换人' },
  { value: 'pass', label: '⏭️ 跳过' },
]

const canSubmit = computed(() => actionQueue.value.length > 0)

function submitAction() {
  // Build action for current side
  const action = { side: activeSide.value, type: actionType.value }
  if (actionType.value === 'attack') action.move_index = selectedMove.value
  if (actionType.value === 'switch') action.switch_index = selectedSwitch.value

  // Check if this side already has an action in queue
  const existingIdx = actionQueue.value.findIndex(a => a.side === activeSide.value)
  if (existingIdx >= 0) {
    actionQueue.value[existingIdx] = action
  } else {
    actionQueue.value.push(action)
  }

  // If both sides have actions, emit submit
  if (actionQueue.value.length >= 2) {
    emit('submit', [...actionQueue.value])
    actionQueue.value = []
  } else {
    // Auto-switch to other side
    activeSide.value = activeSide.value === 'a' ? 'b' : 'a'
  }
}

function removeAction(i) {
  actionQueue.value.splice(i, 1)
}
</script>
