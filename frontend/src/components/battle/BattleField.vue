<template>
  <div class="battle-arena relative w-full overflow-hidden rounded-2xl border-2 border-gray-800 shadow-2xl"
       style="aspect-ratio:4/3;max-height:100%">

    <!-- Background (very dark) -->
    <div class="absolute inset-0 battle-bg-dark"></div>

    <!-- Platforms -->
    <div class="absolute bottom-[32%] left-[20%] w-[35%] h-[10%] rounded-[50%] bg-white/5 -translate-x-1/2 blur-sm z-0"></div>
    <div class="absolute top-[15%] right-[15%] w-[26%] h-[7%] rounded-[50%] bg-white/5 blur-sm z-0"></div>

    <!-- Enemy Pokemon -->
    <div v-if="opponent" class="absolute z-10 flex flex-col items-center"
         style="top:5%; right:6%; width:26%; height:38%">
      <div class="w-full mb-1">
        <div class="text-[1.8vw] text-gray-300 mb-0 px-2 leading-tight font-semibold truncate drop-shadow">
          {{ opponent._speciesName || '#'+opponent.speciesId }}
        </div>
        <div class="w-full bg-gray-800 rounded-full overflow-hidden border border-gray-700 relative"
             style="height:clamp(7px,1.5vw,12px)">
          <div class="h-full rounded-full hp-bar" :class="oppHpFlash"
               :style="{width: opponentHpPct+'%', backgroundColor: hpBarColor(opponentHpPct)}"></div>
          <span v-if="oppDmgNum" class="absolute -right-1 -top-1 text-red-400 font-bold drop-shadow"
                style="font-size:clamp(9px,1.3vw,14px);animation: dmgPop .8s ease-out forwards;pointer-events:none">-{{ oppDmgNum }}</span>
          <span v-if="oppHealNum" class="absolute -left-1 -top-1 text-green-400 font-bold drop-shadow"
                style="font-size:clamp(9px,1.3vw,14px);animation: healPop .8s ease-out forwards;pointer-events:none">+{{ oppHealNum }}</span>
        </div>
        <div class="flex justify-between items-center mt-0.5">
          <div v-if="fmtStages(opponent?.statStages).length" class="flex gap-0.5 flex-wrap">
            <span v-for="s in fmtStages(opponent?.statStages)" :key="'opp'+s.name"
                  class="px-1 rounded text-[1.1vw] leading-tight"
                  :class="s.val > 0 ? 'bg-green-700/80 text-green-200' : 'bg-red-700/80 text-red-200'">
              {{ s.name }}{{ s.val > 0 ? '+' : '' }}{{ s.val }}
            </span>
          </div>
          <div v-if="fmtStatus(opponent?.inBattleStatus)" class="text-[1.2vw] text-orange-400">
            {{ fmtStatus(opponent?.inBattleStatus) }}
          </div>
          <div class="text-right text-[2vw] text-gray-400 font-mono leading-tight">
            {{ opponent.hp||0 }}/{{ opponent.maxHp||1 }}
          </div>
        </div>
      </div>
      <div class="sprite-wrap" :class="animOpp">
        <img v-if="opponent.speciesId && !oppGifFailed" :src="'/sprites/'+opponent.speciesId+'.gif'"
          class="object-contain drop-shadow-xl" style="width:80%;height:75%;image-rendering:pixelated"
          :class="{ 'fainted-overlay': opponentHpPct <= 0 }"
          @error="onOppGifError" />
        <IconSprite v-if="opponent.speciesId && oppGifFailed" :species-id="opponent.speciesId" size="xl"
          :class="{ 'fainted-overlay': opponentHpPct <= 0 }" />
        <div v-if="healArrow.show && healArrow.side === 'b'" class="heal-arrow">+</div>
      </div>
    </div>

    <!-- Player Pokemon -->
    <div v-if="player" class="absolute z-10 flex flex-col items-center"
         style="bottom:26%; left:5%; width:33.33%; height:48%">
      <div class="w-[85%] mb-1">
        <div class="text-[2vw] text-gray-300 mb-0 px-2 leading-tight font-semibold truncate drop-shadow">
          {{ player._speciesName || '#'+player.speciesId }}
        </div>
        <div class="w-full bg-gray-800 rounded-full overflow-hidden border border-gray-700 relative"
             style="height:clamp(8px,1.8vw,14px)">
          <div class="h-full rounded-full hp-bar" :class="playerHpFlash"
               :style="{width: playerHpPct+'%', backgroundColor: hpBarColor(playerHpPct)}"></div>
          <span v-if="playerDmgNum" class="absolute -right-1 -top-1 text-red-400 font-bold drop-shadow"
                style="font-size:clamp(10px,1.4vw,15px);animation: dmgPop .8s ease-out forwards;pointer-events:none">-{{ playerDmgNum }}</span>
          <span v-if="playerHealNum" class="absolute -left-1 -top-1 text-green-400 font-bold drop-shadow"
                style="font-size:clamp(10px,1.4vw,15px);animation: healPop .8s ease-out forwards;pointer-events:none">+{{ playerHealNum }}</span>
        </div>
        <div class="flex justify-between items-center mt-0.5">
          <div class="text-left flex items-center gap-1">
            <span v-if="fmtStatus(player?.inBattleStatus)" class="text-[1.4vw] text-orange-400">
              {{ fmtStatus(player?.inBattleStatus) }}
            </span>
          </div>
          <div class="text-right text-[2.2vw] text-gray-400 font-mono leading-tight">
            {{ player.hp||0 }}/{{ player.maxHp||1 }}
          </div>
        </div>
        <!-- Stat stage chips for player -->
        <div v-if="fmtStages(player?.statStages).length" class="flex gap-0.5 mt-0.5 flex-wrap justify-center">
          <span v-for="s in fmtStages(player?.statStages)" :key="'pl'+s.name"
                class="px-1.5 py-0.5 rounded-full text-[1.3vw] leading-tight font-bold"
                :class="s.val > 0 ? 'bg-green-600/80 text-green-200' : 'bg-red-600/80 text-red-200'">
            {{ s.name }}{{ s.val > 0 ? '+' : '' }}{{ s.val }}
          </span>
        </div>
      </div>
      <div class="sprite-wrap" :class="animPlayer">
        <img v-if="player.speciesId" :src="'/sprites/back/'+player.speciesId+'.gif'"
          class="object-contain drop-shadow-xl" style="width:90%;height:78%;image-rendering:pixelated"
          :class="{ 'fainted-overlay': playerHpPct <= 0 }"
          @error="e => { if(e.target.src.endsWith('.gif')) e.target.src='/sprites/back/'+player.speciesId+'.png'; else e.target.src='/sprites/'+player.speciesId+'.gif' }" />
        <div v-if="healArrow.show && healArrow.side === 'a'" class="heal-arrow">+</div>
      </div>
    </div>

    <!-- Bench circles + Switch (vertical column, left side) -->
    <div class="absolute z-20 flex flex-col items-center gap-1.5" style="bottom:29%; left:1.5%">
      <button @click="localShowSwitch = !localShowSwitch"
              class="rounded-full border-2 flex items-center justify-center transition-all font-bold shadow-lg"
              :class="localShowSwitch ? 'border-amber-400 bg-amber-500/40 text-amber-200' : 'border-gray-600 bg-gray-900/80 text-gray-400 hover:border-gray-400'"
              style="width:clamp(34px,5.4vw,53px);height:clamp(34px,5.4vw,53px);font-size:clamp(14px,2.2vw,24px)"
              title="切换宝可梦">↔</button>
      <div v-for="p in playerBench" :key="'pb'+p._slot"
           class="rounded-full flex items-center justify-center shrink-0 overflow-hidden cursor-pointer hover:scale-110 transition-transform shadow-md"
           :class="p.fainted ? 'border-red-500 bg-red-900/60' : 'border-green-500'"
           :style="benchStyle(p)"
           style="width:clamp(34px,5.4vw,53px);height:clamp(34px,5.4vw,53px);background:rgba(0,0,0,0.6)"
           @click="localShowSwitch = true; localSwitchTarget = p._slot">
        <IconSprite v-if="!p.fainted" :species-id="p.speciesId" size="md" />
        <span v-else style="font-size:clamp(10px,1.5vw,16px)">💀</span>
      </div>
    </div>

    <!-- Bottom Bar: Left=moves/switch, Right=confirm -->
    <div class="absolute bottom-0 left-0 right-0 z-10 flex"
         style="height:24%; background:#111118; border-top:1px solid #2a2a35">

      <!-- LEFT: Move buttons or Switch cards -->
      <div class="flex-1 flex gap-2 p-2.5 h-full items-stretch min-w-0">
        <!-- MOVE mode -->
        <template v-if="!localShowSwitch">
          <button v-for="(m,i) in moves" :key="'mv'+i"
                  @click="selectedMoveIdx = i"
                  :disabled="m._disabled"
                  class="flex-1 rounded-lg border-2 transition-all duration-150 flex flex-col min-w-0 relative"
                  :class="m._disabled
                    ? 'bg-gray-800 border-gray-700 text-gray-600 cursor-not-allowed'
                    : selectedMoveIdx === i
                      ? 'bg-blue-900/60 border-blue-400 text-white shadow-md'
                      : 'bg-gray-800 border-gray-600 text-gray-200 hover:border-gray-400 hover:bg-gray-750'">
            <!-- Type icon top-left, Category icon top-right -->
            <div class="flex justify-between px-1.5 pt-1">
              <img v-if="m._type" :src="iconUrl('types', m._type)" style="height:clamp(10px,1.7vw,20px);width:auto" />
              <img v-if="m._category" :src="iconUrl('categories', m._category)" style="height:clamp(10px,1.7vw,20px);width:auto" />
            </div>
            <!-- Move name + charging indicator -->
            <div class="flex-1 flex items-center justify-center px-1">
              <div class="font-bold truncate text-center" style="font-size:clamp(12px,1.8vw,18px)">
                {{ m._name || '#'+m.id }}
                <span v-if="m._disabled && m.pp > 0" class="text-yellow-400" style="font-size:clamp(8px,1vw,11px)">🔒充能中</span>
              </div>
            </div>
            <!-- Bottom row: effectiveness (left) + PP (right) -->
            <div class="flex justify-between items-end px-1.5 pb-1">
              <span v-if="m._eff >= 2" class="font-bold text-green-400" style="font-size:clamp(7px,1vw,11px)">
                {{ m._eff === 4 ? '效果绝佳' : '效果拔群' }}
              </span>
              <span v-else-if="m._eff > 0 && m._eff < 1" class="font-bold text-orange-400" style="font-size:clamp(7px,1vw,11px)">
                {{ m._eff === 0.5 ? '不理想' : '很不理想' }}
              </span>
              <span v-else-if="m._eff === 0" class="font-bold text-gray-500" style="font-size:clamp(7px,1vw,11px)">无效</span>
              <span v-else></span>
              <span class="font-mono" :class="m._disabled?'text-gray-600':'text-gray-400'" style="font-size:clamp(7px,1vw,11px)">PP {{ m.pp }}/{{ m.maxPp }}</span>
            </div>
          </button>
        </template>

        <!-- SWITCH mode -->
        <template v-else>
          <button v-for="(p,i) in bench" :key="'sw'+p._slot"
                  @click="p._canSwitch ? localSwitchTarget = p._slot : null"
                  :disabled="!p._canSwitch"
                  class="flex-1 rounded-lg border-2 transition-all duration-150 flex flex-col justify-center items-center px-2 min-w-0"
                  :class="p._isActive
                    ? 'bg-green-900/50 border-green-500 text-green-300 cursor-default'
                    : p.fainted
                      ? 'bg-red-950/60 border-red-700 text-red-300/60 cursor-not-allowed'
                      : localSwitchTarget === p._slot
                        ? 'bg-blue-900/60 border-blue-400 text-white shadow-md'
                        : 'bg-gray-800 border-gray-600 text-gray-200 hover:border-gray-400 cursor-pointer'">
            <IconSprite v-if="!p.fainted" :species-id="p.speciesId" size="md" />
            <span v-else style="font-size:clamp(12px,1.8vw,20px)">💀</span>
            <div class="w-[80%] bg-gray-800 rounded-full overflow-hidden mt-1" style="height:clamp(4px,0.7vw,8px)">
              <div class="h-full rounded-full" :style="{width:p._hpPct+'%', backgroundColor: hpBarColor(p._hpPct)}"></div>
            </div>
            <div class="text-gray-500 font-mono mt-0.5" style="font-size:clamp(7px,1vw,10px)">{{ p.hp||0 }}/{{ p.maxHp||1 }}</div>
            <div class="font-bold truncate mt-0.5" style="font-size:clamp(9px,1.2vw,13px)">{{ p._speciesName || '#'+p.speciesId }}</div>
          </button>
        </template>
      </div>

      <!-- RIGHT: Confirm + Leave (same for both modes) -->
      <div class="shrink-0 flex flex-col gap-1.5 justify-center px-2" style="width:clamp(56px,9vw,100px)">
        <button v-if="battleStatus==='active'" @click="doConfirm"
                :disabled="submitting || eventsBusy || (!localShowSwitch && selectedMoveIdx < 0) || (localShowSwitch && localSwitchTarget < 0)"
                class="flex-1 rounded-xl font-bold text-white transition-all duration-200 shadow-md text-center"
                :class="submitting || eventsBusy || (!localShowSwitch && selectedMoveIdx < 0) || (localShowSwitch && localSwitchTarget < 0)
                  ? 'bg-gray-700 cursor-not-allowed text-gray-500'
                  : 'bg-red-600 hover:bg-red-500'"
                style="font-size:clamp(10px,1.5vw,16px)">
          {{ submitting ? '⏳' : '确认' }}
        </button>
        <button v-if="battleStatus==='active'" @click="$emit('leave')"
                class="flex-1 rounded-lg font-medium text-red-400 bg-gray-800 hover:bg-red-900/30 border border-red-800/50 transition-all text-center"
                style="font-size:clamp(8px,1.1vw,12px)">离开</button>
        <button v-if="battleStatus==='completed'" @click="$emit('reset')"
                class="flex-1 rounded-xl font-bold text-white bg-amber-600 hover:bg-amber-500 transition-all text-center"
                style="font-size:clamp(10px,1.5vw,16px)">退出</button>
      </div>
    </div>

    <!-- Animated Battle Events -->
    <BattleEvents :events="messages" :trigger="turn" @animate="onAnimate" @busy="onEventsBusy" />
    <!-- Weather + Field Banner -->
    <WeatherField :weather="weather" :field="field" />

    <!-- Turn counter -->
    <div class="absolute top-2 right-2 z-30">
      <span class="px-3 py-1 rounded-full text-gray-400 font-mono font-bold bg-black/80 backdrop-blur shadow"
            style="font-size:clamp(10px,1.3vw,15px)">Turn {{ turn }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import IconSprite from '../shared/IconSprite.vue'
import WeatherField from './WeatherField.vue'
import BattleEvents from './BattleEvents.vue'

// ---- Sprite animation state ----
const animPlayer = ref('')
const animOpp = ref('')
const playerHpFlash = ref('')
const oppHpFlash = ref('')
const playerDmgNum = ref(0)
const oppDmgNum = ref(0)
const playerHealNum = ref(0)
const oppHealNum = ref(0)
const healArrow = ref({ side: '', show: false })
const eventsBusy = ref(false)

function onAnimate(ev) {
  const side = ev.side
  const target = side === 'a' ? animPlayer : animOpp
  const hpTarget = side === 'a' ? playerHpFlash : oppHpFlash
  const dmgRef = side === 'a' ? playerDmgNum : oppDmgNum
  const healRef = side === 'a' ? playerHealNum : oppHealNum
  const type = ev.event_type
  if (type === 'switch_in') { target.value = 'grow'; setTimeout(() => target.value = '', 600) }
  else if (type === 'faint') { target.value = 'death'; setTimeout(() => target.value = '', 1200) }
  else if (type === 'damage') {
    target.value = 'shake flash-red'; hpTarget.value = 'dmg-flash'
    dmgRef.value = ev.value || 0; setTimeout(() => { target.value = ''; hpTarget.value = ''; dmgRef.value = 0 }, 800)
  }
  else if (type === 'heal') {
    target.value = 'flash-green'; hpTarget.value = 'heal-flash'
    healRef.value = ev.value || 0; setTimeout(() => { target.value = ''; hpTarget.value = ''; healRef.value = 0 }, 900)
  }
}

function onEventsBusy(v) { eventsBusy.value = v }

const props = defineProps({
  sideA: { type: Object, default: null },
  sideB: { type: Object, default: null },
  turn: { type: Number, default: 0 },
  messages: { type: Array, default: () => [] },
  moves: { type: Array, default: () => [] },
  bench: { type: Array, default: () => [] },
  submitting: { type: Boolean, default: false },
  battleStatus: { type: String, default: 'active' },
  weather: { type: Object, default: null },
  field: { type: Object, default: null },
  oppSide: { type: Object, default: null },
})

// Entry animation: play grow when battle starts
watch(() => props.turn, (t) => {
  if (t === 1) { animPlayer.value = 'grow'; animOpp.value = 'grow'; setTimeout(() => { animPlayer.value = ''; animOpp.value = '' }, 600) }
})

const emit = defineEmits(['confirm', 'leave', 'switchPokemon', 'reset'])

// Local selection state (no parent needed for highlighting)
const selectedMoveIdx = ref(-1)
const localShowSwitch = ref(false)
const localSwitchTarget = ref(-1)

const STAT_NAMES = ['物攻','物防','特攻','特防','速度']
const STATUS_NAMES = { brn:'🔥烧伤', frz:'❄️冻结', par:'⚡麻痹', psn:'☠️中毒', tox:'☠️剧毒', slp:'💤睡眠' }

function fmtStages(stages) {
  return (stages||[]).slice(0,5).map((v,i) => ({ name: STAT_NAMES[i], val: v })).filter(s => s.val !== 0)
}
function fmtStatus(list) {
  return (list||[]).map(s => STATUS_NAMES[s.name] || s.name).join(' ')
}

// Reset selection when moves change (new turn)
watch(() => props.moves, () => { selectedMoveIdx.value = -1 })
watch(() => props.turn, () => { selectedMoveIdx.value = -1; localShowSwitch.value = false; localSwitchTarget.value = -1 })

function doConfirm() {
  if (localShowSwitch.value && localSwitchTarget.value >= 0) {
    emit('switchPokemon', { switch_index: localSwitchTarget.value })
    localShowSwitch.value = false
  } else if (selectedMoveIdx.value >= 0) {
    emit('confirm', { type: 'attack', move_index: selectedMoveIdx.value })
  }
}

const playerSide = computed(() => props.sideA)
const opponentSide = computed(() => props.sideB)
const player = computed(() => { const s = playerSide.value; return s ? (s.pokemons||[])[s.active||0] : null })
const opponent = computed(() => { const s = opponentSide.value; return s ? (s.pokemons||[])[s.active||0] : null })

// Auto-open switch panel when player's active Pokemon faints
watch(() => player.value?.hp, (newHp) => {
  if (newHp !== undefined && newHp <= 0) {
    localShowSwitch.value = true
  }
})
const playerBench = computed(() => {
  const s = playerSide.value
  if (!s) return []
  return (s.pokemons||[]).map((p, i) => ({ ...p, _slot: i })).filter(p => p._slot !== (s.active||0))
})
const opponentBench = computed(() => { const s = opponentSide.value; return s ? (s.pokemons||[]).filter((_,i) => i !== (s.active||0)) : [] })

const playerHpPct = computed(() => { const p = player.value; return p ? Math.round((p.hp||0)/(p.maxHp||1)*100) : 0 })
const opponentHpPct = computed(() => { const p = opponent.value; return p ? Math.round((p.hp||0)/(p.maxHp||1)*100) : 0 })

const oppGifFailed = ref(false)
watch(() => opponent.value?.speciesId, () => { oppGifFailed.value = false })
function onOppGifError() { oppGifFailed.value = true }

function hpBarColor(pct) { if (pct > 50) return '#4ade80'; if (pct > 20) return '#facc15'; return '#ef4444' }
function iconUrl(type, name) {
  if (!name) return ''
  const n = name.toLowerCase()
  return `/sprites/${type}/${n.charAt(0).toUpperCase()+n.slice(1)}.png`
}
function benchStyle(p) {
  const pct = p ? Math.round((p.hp||0)/(p.maxHp||1)*100) : 0
  if (pct <= 0) return { borderColor: '#7f1d1d', borderWidth: '2px' }
  return { borderWidth: Math.max(2, Math.round(pct / 40)) + 'px' }
}

</script>

<style scoped>
.battle-bg-dark {
  background: radial-gradient(ellipse at 50% 60%, #1a1a2e 0%, #0d0d1a 50%, #050510 100%);
}
/* Pokemon sprite animations */
.sprite-wrap { position: relative; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; }
.shake { animation: pokeShake .4s ease-in-out; }
@keyframes pokeShake {
  0%,100% { transform: translateX(0); }
  10%,50%,90% { transform: translateX(-4px); }
  30%,70% { transform: translateX(4px); }
}
.flash-red { filter: brightness(1.4) drop-shadow(0 0 8px rgba(255,60,60,.7)); }
.flash-red img, .flash-red svg { filter: hue-rotate(-10deg) saturate(1.5) brightness(1.2); }
.flash-green { filter: brightness(1.3) drop-shadow(0 0 10px rgba(60,255,100,.7)); }
.flash-green img, .flash-green svg { filter: hue-rotate(30deg) saturate(1.3) brightness(1.15); }
.grow { animation: pokeGrow .5s ease-out; }
@keyframes pokeGrow { from { opacity: 0; filter: brightness(1.5); } to { opacity: 1; filter: brightness(1); } }
.death { animation: pokeDeath 1s ease-in forwards; }
@keyframes pokeDeath {
  0% { opacity: 1; transform: translateY(0); filter: brightness(1); }
  30% { opacity: .6; filter: brightness(2) saturate(.3); }
  100% { opacity: 0; transform: translateY(40px) scale(.7); filter: brightness(.3) saturate(0); }
}
@keyframes dmgPop { 0% { transform: translateY(0); opacity:1; } 100% { transform: translateY(-16px); opacity:0; } }
@keyframes healPop { 0% { transform: translateY(0); opacity:1; } 100% { transform: translateY(-18px); opacity:0; } }

.heal-arrow {
  position: absolute; top: -10px; right: -5px; font-size: 24px; font-weight: 900;
  color: #4ade80; text-shadow: 0 0 8px rgba(74,222,128,.8);
  animation: healFloat .7s ease-out forwards; pointer-events: none; z-index: 5;
}
@keyframes healFloat { 0% { transform: translateY(0); opacity: 1; } 100% { transform: translateY(-30px); opacity: 0; } }

/* HP bar smooth transition */
.hp-bar { transition: width .6s ease-out; }
.hp-bar.dmg-flash { filter: brightness(1.5) drop-shadow(0 0 6px rgba(255,60,60,.8)); }
.hp-bar.heal-flash { filter: brightness(1.5) drop-shadow(0 0 8px rgba(60,255,100,.8)); }

.fainted-overlay {
  filter: brightness(0.6) saturate(0.3);
  opacity: 0.65;
}
</style>
