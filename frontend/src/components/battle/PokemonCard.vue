<template>
  <div class="text-center">
    <div class="flex justify-center mb-2">
      <img v-if="safePkm.speciesId" :src="spriteUrl" class="w-24 h-24 object-contain" @error="e=>e.target.style.display='none'" />
    </div>
    <div :class="['text-sm font-bold', sideColor]">{{ safePkm._speciesName || ('#'+safePkm.speciesId) }}</div>
    <div class="flex justify-center gap-1 my-1">
      <img v-if="safePkm.types?.[0]" :src="'/sprites/types/'+typeName(safePkm.types[0])+'.png'" class="h-4 w-auto" />
      <img v-if="safePkm.types?.[1]" :src="'/sprites/types/'+typeName(safePkm.types[1])+'.png'" class="h-4 w-auto" />
    </div>
    <div class="text-xs text-gray-500 mt-1">特性: {{ abilityName || '...' }}</div>
    <div class="flex justify-center gap-2 my-1">
      <StatusBadge v-for="s in (safePkm.inBattleStatus||[]).filter(x=>x?.id!==0)" :key="s.id" :status="s" />
    </div>
    <div class="max-w-[180px] mx-auto mt-2">
      <div class="flex justify-between text-xs text-gray-400 mb-0.5">
        <span>HP</span>
        <span :class="safePkm.fainted?'text-red-400':''">{{ safePkm.hp||0 }}/{{ safePkm.maxHp||1 }}</span>
      </div>
      <div class="w-full bg-gray-700 rounded-full h-3 overflow-hidden border border-gray-600">
        <div class="h-full rounded-full transition-all duration-500" :class="hpBarColor" :style="{width:hpPct+'%'}"></div>
      </div>
    </div>
    <div class="grid grid-cols-2 gap-1 mt-2">
      <div v-for="(m,i) in (safePkm.moves||[])" :key="i"
        class="text-xs px-2 py-1 rounded bg-gray-700/50 text-gray-300 flex justify-between">
        <span>{{ moveNames[m.id]||'#'+m.id }}</span>
        <span class="text-gray-500">{{ m.pp }}/{{ m.maxPp }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import TypeBadge from '../shared/TypeBadge.vue'
import StatusBadge from './StatusBadge.vue'
import { getMoveName, getAbilityName, getSpriteUrl } from '../../api/dataWs'

const TYPE_NAMES = ['Normal','Fire','Water','Electric','Grass','Ice','Fighting','Poison','Ground','Flying','Psychic','Bug','Rock','Ghost','Dragon','Dark','Steel','Fairy']
function typeName(id) { return TYPE_NAMES[id] || '' }

const props = defineProps({
  pokemon: { type: Object, default: () => ({}) },
  sideColor: { type: String, default: 'text-gray-300' },
})
const moveNames = ref({})
const abilityName = ref('')
const spriteUrl = ref('')
const safePkm = computed(() => props.pokemon || {})

const hpPct = computed(() => {
  const hp = safePkm.value.hp || 0; const mx = safePkm.value.maxHp || 1
  return Math.round(hp / mx * 100)
})
const hpBarColor = computed(() => hpPct.value > 50 ? 'bg-green-500' : hpPct.value > 20 ? 'bg-yellow-500' : 'bg-red-500')

watch(() => safePkm.value.speciesId, (id) => {
  if (id) spriteUrl.value = `/sprites/${id}.gif`
}, { immediate: true })

watch(safePkm, async (p) => {
  if (!p) return
  if (p.abilityId) abilityName.value = await getAbilityName(p.abilityId)
  if (p.moves) {
    for (const m of p.moves) {
      if (m.id && !moveNames.value[m.id]) moveNames.value[m.id] = await getMoveName(m.id)
    }
  }
}, { immediate: true, deep: true })
</script>
