<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-800 mb-6">📊 数据统计</h1>

    <!-- Global Stats Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-5 mb-8">
      <div class="glass-card glass-card-hover p-6 text-center animate-slide-up animate-slide-up-1">
        <div class="text-4xl mb-3">👤</div>
        <div class="text-3xl font-bold text-pokeball-red">{{ stats.total_players || 0 }}</div>
        <div class="text-sm text-gray-500 mt-1">注册训练家</div>
      </div>
      <div class="glass-card glass-card-hover p-6 text-center animate-slide-up animate-slide-up-2">
        <div class="text-4xl mb-3">⚡</div>
        <div class="text-3xl font-bold text-pokedex-blue">{{ stats.total_battles || 0 }}</div>
        <div class="text-sm text-gray-500 mt-1">总对战数</div>
      </div>
      <div class="glass-card glass-card-hover p-6 text-center animate-slide-up animate-slide-up-3">
        <div class="text-4xl mb-3">🎒</div>
        <div class="text-3xl font-bold text-green-500">{{ stats.total_teams || 0 }}</div>
        <div class="text-sm text-gray-500 mt-1">总队伍数</div>
      </div>
    </div>

    <!-- Coming soon -->
    <div class="glass-card p-8 text-center">
      <div class="text-5xl mb-4 animate-float">🔬</div>
      <h3 class="text-lg font-bold text-gray-800 mb-2">深度分析即将上线</h3>
      <p class="text-sm text-gray-500 max-w-md mx-auto">
        宝可梦使用率、招式统计、属性相性等深度分析功能正在开发中 ✨
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { statsAPI } from '../api/stats'

const stats = ref({})

onMounted(async () => {
  try {
    const result = await statsAPI.global()
    stats.value = result.data || {}
  } catch (e) {
    console.error('Failed to load stats:', e)
  }
})
</script>
