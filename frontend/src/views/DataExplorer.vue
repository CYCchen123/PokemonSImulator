<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-800 mb-6">📚 数据图鉴</h1>

    <!-- Tab bar -->
    <div class="flex gap-2 mb-6 flex-wrap">
      <button v-for="tab in tabs" :key="tab.key"
        @click="activeTab = tab.key"
        class="px-4 py-2 rounded-full text-sm font-medium transition-all duration-200"
        :class="activeTab === tab.key
          ? 'bg-pokeball-red text-white shadow-md'
          : 'bg-white/60 text-gray-500 hover:bg-white hover:text-gray-700'"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Type Chart -->
    <div v-if="activeTab === 'types'" class="glass-card p-6">
      <h3 class="text-lg font-bold text-gray-800 mb-4">属性相克表</h3>
      <div class="overflow-x-auto">
        <table class="w-full text-xs">
          <thead>
            <tr>
              <th class="p-1 text-gray-400 font-medium">攻\防</th>
              <th v-for="t in types" :key="t.value" class="p-1">
                <span class="px-1.5 py-0.5 rounded-full text-white text-xs font-medium" :style="{ backgroundColor: t.color }">
                  {{ t.label }}
                </span>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="atk in types" :key="atk.value">
              <td class="p-1">
                <span class="px-1.5 py-0.5 rounded-full text-white text-xs font-medium" :style="{ backgroundColor: atk.color }">
                  {{ atk.label }}
                </span>
              </td>
              <td v-for="def in types" :key="def.value" class="p-0.5 text-center">
                <span class="block w-7 h-6 rounded-lg text-xs leading-6 font-bold"
                  :class="effectivenessClass(atk, def)">
                  {{ effectivenessText(atk, def) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="text-xs text-gray-400 mt-3">来源: Pokemon Showdown type chart · 绿=2x 红=½x 灰=无效</p>
    </div>

    <!-- Enums -->
    <div v-if="activeTab === 'enums'" class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div v-for="group in enumGroups" :key="group.name"
        class="glass-card p-5">
        <h3 class="text-sm font-bold text-gray-700 mb-3">{{ group.name }}</h3>
        <div class="space-y-1">
          <div v-for="item in group.items" :key="item.value"
            class="flex justify-between text-xs py-1.5 px-2 rounded-lg border-b border-gray-100 last:border-0 hover:bg-gray-50 transition-colors">
            <span class="text-gray-700 font-medium">{{ item.label }}</span>
            <span class="text-gray-400">{{ item.name }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { TYPES, WEATHER_MAP, FIELD_MAP, STATUS_MAP, CATEGORY_MAP } from '../utils/enums'

const activeTab = ref('types')

const tabs = [
  { key: 'types', label: '🔥 属性相克' },
  { key: 'enums', label: '📋 枚举表' },
]

const types = Object.values(TYPES)

// Simplified type effectiveness (Gen6+)
const TYPE_CHART = {
  // [attacker]: { [defender]: multiplier }
  'Normal': { 'Rock': 0.5, 'Steel': 0.5, 'Ghost': 0 },
  'Fire': { 'Fire': 0.5, 'Water': 0.5, 'Grass': 2, 'Ice': 2, 'Bug': 2, 'Rock': 0.5, 'Dragon': 0.5, 'Steel': 2 },
  'Water': { 'Fire': 2, 'Water': 0.5, 'Grass': 0.5, 'Ground': 2, 'Rock': 2, 'Dragon': 0.5 },
  'Electric': { 'Water': 2, 'Electric': 0.5, 'Grass': 0.5, 'Ground': 0, 'Flying': 2, 'Dragon': 0.5 },
  'Grass': { 'Fire': 0.5, 'Water': 2, 'Grass': 0.5, 'Poison': 0.5, 'Ground': 2, 'Flying': 0.5, 'Bug': 0.5, 'Rock': 2, 'Dragon': 0.5, 'Steel': 0.5 },
  'Ice': { 'Fire': 0.5, 'Water': 0.5, 'Grass': 2, 'Ice': 0.5, 'Ground': 2, 'Flying': 2, 'Dragon': 2, 'Steel': 0.5 },
  'Fighting': { 'Normal': 2, 'Ice': 2, 'Poison': 0.5, 'Flying': 0.5, 'Psychic': 0.5, 'Bug': 0.5, 'Rock': 2, 'Ghost': 0, 'Dark': 2, 'Steel': 2, 'Fairy': 0.5 },
  'Poison': { 'Grass': 2, 'Poison': 0.5, 'Ground': 0.5, 'Rock': 0.5, 'Ghost': 0.5, 'Steel': 0, 'Fairy': 2 },
  'Ground': { 'Fire': 2, 'Electric': 2, 'Grass': 0.5, 'Poison': 2, 'Flying': 0, 'Bug': 0.5, 'Rock': 2, 'Steel': 2 },
  'Flying': { 'Electric': 0.5, 'Grass': 2, 'Fighting': 2, 'Bug': 2, 'Rock': 0.5, 'Steel': 0.5 },
  'Psychic': { 'Fighting': 2, 'Poison': 2, 'Psychic': 0.5, 'Dark': 0, 'Steel': 0.5 },
  'Bug': { 'Fire': 0.5, 'Grass': 2, 'Fighting': 0.5, 'Poison': 0.5, 'Flying': 0.5, 'Psychic': 2, 'Ghost': 0.5, 'Dark': 2, 'Steel': 0.5, 'Fairy': 0.5 },
  'Rock': { 'Fire': 2, 'Ice': 2, 'Fighting': 0.5, 'Ground': 0.5, 'Flying': 2, 'Bug': 2, 'Steel': 0.5 },
  'Ghost': { 'Normal': 0, 'Psychic': 2, 'Ghost': 2, 'Dark': 0.5 },
  'Dragon': { 'Dragon': 2, 'Steel': 0.5, 'Fairy': 0 },
  'Dark': { 'Fighting': 0.5, 'Psychic': 2, 'Ghost': 2, 'Dark': 0.5, 'Fairy': 0.5 },
  'Steel': { 'Fire': 0.5, 'Water': 0.5, 'Electric': 0.5, 'Ice': 2, 'Rock': 2, 'Steel': 0.5, 'Fairy': 2 },
  'Fairy': { 'Fire': 0.5, 'Fighting': 2, 'Poison': 0.5, 'Dragon': 2, 'Dark': 2, 'Steel': 0.5 },
}

function getEffectiveness(atkType, defType) {
  return TYPE_CHART[atkType.name]?.[defType.name] ?? 1
}

function effectivenessClass(atkType, defType) {
  const eff = getEffectiveness(atkType, defType)
  if (eff >= 2) return 'bg-green-100 text-green-700 border border-green-200'
  if (eff === 0.5) return 'bg-red-50 text-red-500 border border-red-200'
  if (eff === 0) return 'bg-gray-100 text-gray-400 border border-gray-200'
  return 'bg-gray-50 text-gray-400 border border-gray-100'
}

function effectivenessText(atkType, defType) {
  const eff = getEffectiveness(atkType, defType)
  if (eff >= 2) return '2'
  if (eff === 0.5) return '½'
  if (eff === 0) return '0'
  return '·'
}

const enumGroups = [
  { name: '属性 (Types)', items: Object.values(TYPES) },
  { name: '天气 (Weather)', items: Object.values(WEATHER_MAP) },
  { name: '场地 (Field)', items: Object.values(FIELD_MAP) },
  { name: '状态 (Status)', items: Object.values(STATUS_MAP) },
  { name: '招式分类 (Category)', items: Object.values(CATEGORY_MAP) },
]
</script>
