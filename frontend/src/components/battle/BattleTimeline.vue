<template>
  <div class="bg-gray-800 rounded-lg p-4 border border-gray-700 max-h-80 overflow-y-auto">
    <h3 class="text-sm font-bold text-gray-300 uppercase mb-3">📜 事件时间线</h3>

    <div v-if="events.length === 0" class="text-center text-gray-500 text-sm py-4">
      暂无事件
    </div>

    <div v-else class="space-y-1">
      <div v-for="event in events" :key="event.timeline_index || event.id"
        class="flex gap-3 text-sm py-1.5 border-b border-gray-700/50 last:border-0"
      >
        <span class="text-xs text-gray-500 w-8 shrink-0">#{{ event.timeline_index }}</span>
        <span class="text-xs px-1.5 py-0.5 rounded bg-gray-700 text-gray-400 shrink-0">
          {{ event.event_type || 'event' }}
        </span>
        <span class="text-gray-300 text-xs flex-1">{{ event.description }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  events: { type: Array, default: () => [] },
})
</script>
