<template>
  <div class="flex gap-4 h-[calc(100vh-80px)]">
    <!-- LEFT: Team slots -->
    <div class="w-64 shrink-0 space-y-1.5 overflow-y-auto">
      <input v-model="teamName" placeholder="队伍名称" class="bg-white/70 border border-gray-200 rounded-xl px-3 py-1.5 text-sm text-gray-800 w-full mb-2" />
      <button @click="saveTeam" class="w-full py-2 bg-rose-400 hover:bg-rose-500 text-white rounded-full text-xs font-bold">💾 保存</button>
      <div v-if="savedTeams.length" class="mt-3 pt-3 border-t border-gray-200">
        <div class="text-xs text-gray-400 mb-2">已保存</div>
        <div v-for="t in savedTeams" :key="t.name" class="text-xs px-2 py-1.5 rounded-lg cursor-pointer hover:bg-gray-100 text-gray-600 mb-0.5 flex items-center">
          <span class="flex-1" @click="loadTeam(t)">{{ t.name }} ({{ t.pokemon?.length||0 }})</span>
          <button @click.stop="deleteTeam(t.name)" class="text-gray-400 hover:text-red-400">✕</button>
        </div>
      </div>
      <div v-for="(slot,idx) in slots" :key="idx" @click="selectSlot(idx)"
        class="rounded-xl p-2.5 cursor-pointer border-2 transition-all"
        :class="activeIdx===idx ? 'border-rose-300 shadow-sm' : 'border-transparent hover:border-gray-200'">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 flex items-center justify-center shrink-0">
            <IconSprite v-if="slot.pkm" :species-id="slot.pkm.speciesID" size="md" />
            <span v-else class="text-gray-400 text-lg">+</span>
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-xs text-gray-800 font-bold truncate">{{ slot._name||'空位 #'+(idx+1) }}</div>
            <div v-if="slot._types?.length" class="flex gap-0.5 mt-0.5">
              <img v-for="t in slot._types.filter(isValidType)" :key="t" :src="'/sprites/types/'+capitalize(t)+'.png'" class="h-3 w-auto" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- RIGHT: Editor -->
    <div class="flex-1 bg-white rounded-2xl border border-gray-200 shadow-sm flex flex-col overflow-hidden">
      <!-- Pokemon summary bar (when selected) -->
      <div v-if="activeSlot.pkm" class="px-4 py-3 border-b border-gray-100 shrink-0 flex items-start gap-3 flex-wrap bg-gradient-to-b from-white to-gray-50/50">
        <!-- Left: name + sprite (stacked) -->
        <div class="flex flex-col items-center shrink-0 w-[72px]">
          <div class="text-xs font-bold text-gray-800 text-center truncate w-full">{{ activeSlot._name }}</div>
          <div class="text-[10px] text-gray-400">#{{ activeSlot.pkm.speciesID }}</div>
          <img :src="'/sprites/'+activeSlot.pkm.speciesID+'.gif'" class="w-20 h-20 drop-shadow-md mt-0.5" />
          <div class="flex gap-0.5 mt-0.5">
            <img v-for="t in (activeSlot._types||[]).filter(isValidType)" :key="t" :src="'/sprites/types/'+capitalize(t)+'.png'" class="h-4 w-auto" />
          </div>
        </div>

        <!-- Center: 2x2 move grid (larger) -->
        <div class="grid grid-cols-2 gap-2 flex-1 max-w-[340px]">
          <button v-for="i in 4" :key="'m'+i" @click="editMoveSlot=i-1; activeTab='moves'"
            class="text-sm rounded-xl border-2 transition-all duration-150 p-2.5 min-h-[56px] text-left"
            :class="activeSlot.pkm.moves[i-1]
              ? (editMoveSlot===i-1 ? 'bg-blue-100 border-blue-400 shadow-md ring-1 ring-blue-300' : 'bg-white border-blue-200 hover:border-blue-400 hover:shadow-md')
              : (editMoveSlot===i-1 ? 'bg-blue-50 border-blue-300 border-dashed' : 'bg-white/50 border-dashed border-gray-250 text-gray-400 hover:border-gray-350 hover:bg-white')">
            <template v-if="activeSlot.pkm.moves[i-1]">
              <div class="flex items-center gap-1.5 mb-1">
                <img :src="'/sprites/types/'+capitalize(moveType(activeSlot.pkm.moves[i-1]))+'.png'" class="h-4 w-auto" />
                <img :src="'/sprites/categories/'+moveCat(activeSlot.pkm.moves[i-1])+'.png'" class="h-4 w-auto" />
                <span class="ml-auto text-[10px] text-gray-400 font-mono">{{ movePower(activeSlot.pkm.moves[i-1])||'-' }}·{{ movePP(activeSlot.pkm.moves[i-1])||'-' }}</span>
              </div>
              <div class="text-gray-700 font-semibold text-xs truncate">{{ moveNamesCache[activeSlot.pkm.moves[i-1]]||'...' }}</div>
            </template>
            <template v-else>
              <div class="flex items-center justify-center h-full text-gray-350 text-sm">招式 {{ i }}</div>
            </template>
          </button>
        </div>

        <!-- Right: Item + Nature (stacked, larger) -->
        <div class="flex flex-col gap-2 shrink-0 w-[140px]">
          <button @click="activeTab='items'"
            class="text-sm rounded-xl border-2 transition-all duration-150 p-2.5 text-left min-h-[56px]"
            :class="activeSlot.pkm.item
              ? (activeTab==='items' ? 'bg-amber-100 border-amber-400 shadow-md' : 'bg-white border-amber-200 hover:border-amber-400 hover:shadow-md')
              : (activeTab==='items' ? 'bg-amber-50 border-amber-300 border-dashed' : 'bg-white/50 border-dashed border-gray-250 text-gray-400 hover:border-gray-350')">
            <template v-if="activeSlot._itemName">
              <div class="flex items-center gap-2">
                <div :style="itemSpriteStyle(itemImgName(activeSlot.pkm.item))" class="w-6 h-6 shrink-0 rounded" />
                <span class="text-amber-700 font-semibold text-xs truncate">{{ activeSlot._itemName }}</span>
              </div>
            </template>
            <template v-else>
              <div class="flex items-center justify-center h-full text-gray-350 text-sm">🎒 道具</div>
            </template>
          </button>
          <button @click="activeTab='details'"
            class="text-sm rounded-xl border-2 transition-all duration-150 p-2.5 text-left min-h-[56px]"
            :class="activeSlot.pkm.nature !== undefined
              ? (activeTab==='details' ? 'bg-purple-50 border-purple-300 shadow-md' : 'bg-white border-gray-200 hover:border-purple-300 hover:shadow-md')
              : (activeTab==='details' ? 'bg-purple-50 border-purple-300 border-dashed' : 'bg-white/50 border-dashed border-gray-250 text-gray-400')">
            <div class="text-gray-700 font-semibold text-xs">{{ natureName(activeSlot.pkm.nature) }}</div>
            <div class="text-gray-400 text-[11px] mt-0.5">{{ natureDesc(activeSlot.pkm.nature) }}</div>
          </button>
        </div>

        <button @click="removePokemon" class="text-gray-400 hover:text-red-400 text-xs shrink-0 mt-1">✕</button>
      </div>

      <!-- Tab bar -->
      <div class="flex border-b border-gray-200 shrink-0">
        <button v-for="tab in tabs" :key="tab.key" @click="activeTab=tab.key"
          class="flex-1 py-2.5 text-sm font-medium transition-all border-b-2"
          :class="activeTab===tab.key ? 'text-rose-400 border-rose-400 bg-rose-50/50' : 'text-gray-400 border-transparent hover:text-gray-600'">
          {{ tab.label }}
        </button>
      </div>

      <!-- Search + List -->
      <div class="flex-1 flex flex-col overflow-hidden">
        <div class="p-3 shrink-0">
          <input v-if="activeTab==='species'" v-model="speciesSearch" @input="onSpeciesSearch" placeholder="搜索宝可梦..." class="w-full bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 text-sm" />
          <input v-if="activeTab==='moves'" v-model="moveSearch" @input="onMoveSearch" placeholder="搜索招式..." class="w-full bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 text-sm" />
          <input v-if="activeTab==='items'" v-model="itemSearch" @input="onItemSearch" placeholder="搜索道具..." class="w-full bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 text-sm" />
        </div>

        <div class="flex-1 overflow-y-auto px-3 pb-3">
          <!-- Species list -->
          <div v-if="activeTab==='species'">
            <div v-for="sp in speciesResults" :key="sp.id" @click="pickSpecies(sp)"
              class="flex items-center gap-3 px-3 py-2 hover:bg-rose-50 cursor-pointer rounded-xl border-b border-gray-50"
              :class="{'bg-rose-100': activeSlot.pkm?.speciesID===sp.id}">
              <IconSprite :species-id="sp.id" size="lg" />
              <div class="flex-1"><span class="text-sm text-gray-800 font-medium">{{ sp.name }}</span><span class="text-gray-400 text-xs ml-1">#{{ sp.id }}</span></div>
              <img v-for="t in (sp.types||[]).filter(isValidType)" :key="t" :src="'/sprites/types/'+capitalize(t)+'.png'" class="h-4 w-auto" />
              <span class="text-gray-400 text-xs ml-2">{{ (sp.baseStats||[0]*6).reduce((a,b)=>a+b,0) }}</span>
            </div>
          </div>

          <!-- Moves list -->
          <div v-if="activeTab==='moves' && activeSlot.pkm">
            <div v-for="mv in mvResults" :key="mv.id" @click="toggleMove(mv)"
              class="flex items-center gap-3 px-3 py-2 hover:bg-gray-50 cursor-pointer rounded-xl border-b border-gray-50 text-sm"
              :class="{'bg-rose-50': activeSlot.pkm.moves.includes(mv.id)}">
              <img :src="'/sprites/types/'+capitalize(mv.type)+'.png'" class="h-4 w-auto shrink-0" />
              <span class="font-medium" :style="{color: typeColor(mv.type)}">{{ mv.name }}</span>
              <span class="text-gray-400 text-xs ml-auto shrink-0">{{ mv.power||'-' }}pwr · {{ mv.accuracy||'-' }}%</span>
              <span v-if="activeSlot.pkm.moves.includes(mv.id)" class="text-rose-400 font-bold shrink-0">✓</span>
            </div>
          </div>

          <!-- Items -->
          <div v-if="activeTab==='items' && activeSlot.pkm">
            <div v-for="it in itemResults" :key="it.id" @click="selectItem(it)"
              class="flex items-center gap-3 px-3 py-2 hover:bg-gray-50 cursor-pointer rounded-xl border-b border-gray-50 text-sm"
              :class="{'bg-rose-50': activeSlot.pkm.item===it.id}">
              <div :style="itemSpriteStyle(it.name)" class="w-6 h-6 shrink-0 rounded" />
              <div class="flex-1">
                <span class="text-gray-700 font-medium">{{ it.name }}</span>
                <p class="text-gray-400 text-xs truncate">{{ it.description||'' }}</p>
              </div>
              <span v-if="activeSlot.pkm.item===it.id" class="text-rose-400 font-bold shrink-0">✓</span>
            </div>
          </div>

          <!-- Details -->
          <div v-if="activeTab==='details' && activeSlot.pkm" class="space-y-4">
            <div>
              <label class="text-xs text-gray-400 mb-1 block">特性</label>
              <select v-model.number="activeSlot.pkm.ability" class="w-full bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 text-sm">
                <option :value="0">选择特性</option>
                <option v-for="aid in (activeSlot._species?.abilities||[])" :key="aid" :value="aid">{{ abilityNamesCache[aid]||'#'+aid }}</option>
                <option v-if="activeSlot._species?.hiddenAbilityID" :value="activeSlot._species.hiddenAbilityID">{{ abilityNamesCache[activeSlot._species.hiddenAbilityID]||'...' }} (隐)</option>
              </select>
            </div>
            <div>
              <label class="text-xs text-gray-400 mb-1 block">性格</label>
              <div class="grid grid-cols-2 gap-1">
                <div v-for="n in NATURES" :key="n.v" @click="activeSlot.pkm.nature=n.v"
                  class="px-2 py-1 rounded-lg cursor-pointer text-xs" :class="activeSlot.pkm.nature===n.v ? 'bg-rose-100 text-rose-600' : 'text-gray-500 hover:bg-gray-50'">{{ n.name }} {{ n.desc }}</div>
              </div>
            </div>
            <div>
              <label class="text-xs text-gray-400 mb-1 block">EVs (剩余 {{ 508 - evTotal }})</label>
              <div class="grid grid-cols-6 gap-1 text-xs">
                <div v-for="s in EVS" :key="s.k" class="text-center">
                  <div class="text-gray-400">{{ s.n }}</div>
                  <input v-model.number="activeSlot.pkm.evs[s.k]" type="number" min="0" max="252" class="w-full bg-gray-50 border border-gray-200 rounded px-1 py-0.5 text-gray-700 text-center" />
                </div>
              </div>
            </div>
            <div class="bg-gray-50 rounded-xl p-3">
              <div class="text-xs text-gray-400 mb-1">能力值 (Lv.50)</div>
              <div class="grid grid-cols-6 gap-1 text-center text-xs">
                <div v-for="s in EVS" :key="s.k"><div class="text-gray-400">{{ s.n }}</div><div class="text-gray-700 font-mono font-bold">{{ calcStat(s.k) }}</div></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { TYPES } from '../utils/enums'
import { connect, request, send, getPlayerId } from '../api/wsClient'
import IconSprite from '../components/shared/IconSprite.vue'
import { ITEM_SHEET } from '../utils/itemSheet'

const teamName = ref('Team')
const activeIdx = ref(0)
const activeTab = ref('species')
const speciesSearch = ref(''); const speciesResults = ref([])
const moveSearch = ref(''); const mvResults = ref([]); const editMoveSlot = ref(-1)
const itemSearch = ref(''); const itemResults = ref([])
const moveNamesCache = ref({}); const itemNamesCache = ref({}); const abilityNamesCache = ref({})
const savedTeams = ref([])
let timers = {}

const EVS = [{k:'hp',n:'HP'},{k:'atk',n:'Atk'},{k:'def',n:'Def'},{k:'spa',n:'SpA'},{k:'spd',n:'SpD'},{k:'spe',n:'Spe'}]
const NATURES = [{v:3,name:'Adamant',desc:'+Atk -SpA'},{v:10,name:'Timid',desc:'+Spe -Atk'},{v:13,name:'Jolly',desc:'+Spe -SpA'},{v:15,name:'Modest',desc:'+SpA -Atk'},{v:23,name:'Careful',desc:'+SpD -SpA'},{v:5,name:'Bold',desc:'+Def -Atk'},{v:8,name:'Impish',desc:'+Def -SpA'},{v:0,name:'Hardy',desc:'修正なし'},{v:1,name:'Lonely',desc:'+Atk -Def'},{v:2,name:'Brave',desc:'+Atk -Spe'},{v:4,name:'Naughty',desc:'+Atk -SpD'},{v:7,name:'Relaxed',desc:'+Def -Spe'},{v:9,name:'Lax',desc:'+Def -SpD'},{v:11,name:'Hasty',desc:'+Spe -Def'},{v:14,name:'Naive',desc:'+Spe -SpD'},{v:16,name:'Mild',desc:'+SpA -Def'},{v:17,name:'Quiet',desc:'+SpA -Spe'},{v:19,name:'Rash',desc:'+SpA -SpD'},{v:20,name:'Calm',desc:'+SpD -Atk'},{v:21,name:'Gentle',desc:'+SpD -Def'},{v:22,name:'Sassy',desc:'+SpD -Spe'}]
const tabs = [{key:'species',label:'🔍 宝可梦'},{key:'moves',label:'⚔️ 技能'},{key:'items',label:'🎒 道具'},{key:'details',label:'📊 详情'}]

const slots = reactive(Array.from({length:6}, () => ({ pkm: null, _name: '', _types: [], _species: null, _moveNames: [], _itemName: '' })))
const activeSlot = computed(() => slots[activeIdx.value])
const evTotal = computed(() => activeSlot.value.pkm?.evs ? Object.values(activeSlot.value.pkm.evs).reduce((a,b)=>a+b,0) : 0)

function capitalize(s) { return s ? s.charAt(0).toUpperCase()+s.slice(1).toLowerCase() : '' }
function moveType(mid) {
  const mv = mvResults.value.find(m=>m.id===mid); return mv?.type||'Normal'
}
function moveCat(mid) {
  const mv = mvResults.value.find(m=>m.id===mid)
  const c = mv?.category||'status'
  return c.charAt(0).toUpperCase()+c.slice(1)
}
function movePower(mid) { const mv = mvResults.value.find(m=>m.id===mid); return mv?.power||0 }
function movePP(mid) { const mv = mvResults.value.find(m=>m.id===mid); return mv?.pp||0 }
function isValidType(t) { return t !== undefined && t !== null && t !== '' && TYPES[t] !== undefined }
function typeColor(n) {
  if (!n) return '#666'
  const nl = String(n).toLowerCase()
  for (const t of Object.values(TYPES)) { if (t.name.toLowerCase()===nl) return t.color }
  return '#666'
}
function natureName(v) { const n = NATURES.find(x=>x.v===v); return n ? n.name : '性格' }
function natureDesc(v) { const n = NATURES.find(x=>x.v===v); return n ? n.desc : '' }
function catColor(c) { if (c==='Physical') return '#E05D3B'; if (c==='Special') return '#4A7EB5'; return '#8B8B8B' }
function itemImgName(id) { const it = itemResults.value.find(x=>x.id===id); return it?.name||'' }
function itemDesc(id) { const it = itemResults.value.find(x=>x.id===id); return it?.description||'' }
function itemSpriteStyle(name) {
  const pos = ITEM_SHEET.mapping[name]
  if (!pos) return { background: '#f3f4f6', borderRadius: '4px' }
  return {
    backgroundImage: `url(${ITEM_SHEET.url})`,
    backgroundPosition: pos,
    backgroundSize: `${ITEM_SHEET.cols * ITEM_SHEET.size}px auto`,
    imageRendering: 'pixelated',
  }
}

function selectSlot(idx) {
  activeIdx.value = idx
  if (slots[idx].pkm) { activeTab.value = 'moves'; loadSlotData() }
  else { activeTab.value = 'species' }
}
function removePokemon() {
  const s = slots[activeIdx.value]; s.pkm = null; s._name = ''; s._types = []; s._species = null; s._moveNames = []; s._itemName = ''
  activeTab.value = 'species'
}

watch(activeIdx, () => { loadSlotData() }, { immediate: true })
watch(activeTab, (tab) => {
  if (tab === 'items' && !itemResults.value.length) loadItems()
})
function loadSlotData() {
  let sp = activeSlot.value._species
  // Try to find species from results if _species is null
  if (!sp && activeSlot.value.pkm?.speciesID) {
    sp = speciesResults.value.find(s => s.id === activeSlot.value.pkm.speciesID)
    if (sp) activeSlot.value._species = sp
  }
  if (sp && (sp.learnableMoves||[]).length > 0) {
    request('get_moves',{learnset:sp.learnableMoves,limit:200}).then(r=>{mvResults.value=r})
  } else {
    mvResults.value = []
  }
}
function loadItems() {
  request('get_items',{search:'',limit:200}).then(r=>{itemResults.value=r})
}

onMounted(async () => {
  await connect('TeamBuilder')
  speciesResults.value = await request('get_species',{search:'',limit:1100}).catch(()=>[])
  await loadSavedTeams()
  // Preload items for all slots
  request('get_items',{search:'',limit:200}).then(r=>{itemResults.value=r})
})

async function onSpeciesSearch() {
  clearTimeout(timers.sp); timers.sp = setTimeout(async () => {
    try { speciesResults.value = await request('get_species',{search:speciesSearch.value,limit:200}) } catch { speciesResults.value = [] }
  }, 150)
}
function pickSpecies(sp) {
  const s = slots[activeIdx.value]
  s.pkm = { speciesID: sp.id, level: 50, ability: (sp.abilities && sp.abilities[0]) || 0, nature: 3, moves: [], item: 0, evs: {hp:0,atk:0,def:0,spa:0,spd:0,spe:0} }
  s._name = sp.name; s._types = sp.types||[]; s._species = sp; s._moveNames = []; s._itemName = ''
  activeTab.value = 'moves'
  const ls = sp.learnableMoves||[]
  if (ls.length) request('get_moves',{learnset:ls,limit:200}).then(r=>{mvResults.value=r})
  const allAb = [...(sp.abilities||[]), sp.hiddenAbilityID].filter(Boolean)
  allAb.forEach(aid => request('get_ability',{id:aid}).then(r=>{abilityNamesCache.value[aid]=r?.name||'#'+aid}))
  request('get_items',{search:'',limit:200}).then(r=>{itemResults.value=r})
}

async function onMoveSearch() {
  clearTimeout(timers.mv); timers.mv = setTimeout(async () => {
    const ls = activeSlot.value._species?.learnableMoves||[]
    try { mvResults.value = await request('get_moves',{search:moveSearch.value,learnset:ls,limit:200}) } catch { mvResults.value = [] }
  }, 150)
}
function toggleMove(mv) {
  const slot = slots[activeIdx.value]
  if (!slot.pkm) return
  moveNamesCache.value[mv.id] = mv.name
  const idx = editMoveSlot.value
  if (idx >= 0) {
    // Replace specific slot
    const m = [...slot.pkm.moves]
    // Remove if already in another slot
    const existing = m.indexOf(mv.id)
    if (existing >= 0) m.splice(existing, 1)
    m[idx] = mv.id
    slot.pkm.moves = m.filter(Boolean)
    editMoveSlot.value = -1
  } else {
    const m = [...slot.pkm.moves]
    if (m.includes(mv.id)) {
      slot.pkm.moves = m.filter(x=>x!==mv.id)
    } else if (m.length >= 4) {
      return
    } else {
      slot.pkm.moves = [...m, mv.id]
    }
  }
  slot._moveNames = slot.pkm.moves.map(mid => moveNamesCache.value[mid]||'')
}

async function onItemSearch() {
  clearTimeout(timers.it); timers.it = setTimeout(async () => {
    try { itemResults.value = await request('get_items',{search:itemSearch.value,limit:200}) } catch { itemResults.value = [] }
  }, 150)
}
function selectItem(it) {
  if (activeSlot.value.pkm.item === it.id) {
    activeSlot.value.pkm.item = 0; activeSlot.value._itemName = ''
  } else {
    activeSlot.value.pkm.item = it.id; activeSlot.value._itemName = it.name
  }
  itemNamesCache.value[it.id] = it.name
}

function calcStat(k) {
  const p = activeSlot.value.pkm; const sp = activeSlot.value._species
  if (!p||!sp) return '?'
  const b = ['hp','atk','def','spa','spd','spe'].indexOf(k)
  const base = sp.baseStats?.[b]||0; const iv=31; const ev=p.evs?.[k]||0
  let s
  if (k==='hp') s = Math.floor((2*base+iv+Math.floor(ev/4))*50/100)+60
  else { s = Math.floor((2*base+iv+Math.floor(ev/4))*50/100)+5
    const nm = {3:{atk:1.1,spa:0.9},10:{spe:1.1,atk:0.9},13:{spe:1.1,spa:0.9},15:{spa:1.1,atk:0.9},23:{spd:1.1,spa:0.9},5:{def:1.1,atk:0.9},8:{def:1.1,spa:0.9}}[p.nature||3]
    if (nm) { if (nm[k]===1.1) s=Math.floor(s*1.1); else if (nm[k]===0.9) s=Math.floor(s*0.9) }
  }
  return s
}

async function loadSavedTeams() {
  const uid = getPlayerId(); if (!uid) return
  try { savedTeams.value = await request('get_user_teams',{user_id:uid}) } catch { savedTeams.value = [] }
}
async function deleteTeam(name) { send('delete_team',{username:getPlayerId(),team_name:name}); loadSavedTeams() }
async function loadTeam(t) {
  teamName.value = t.name
  slots.forEach(s => { s.pkm = null; s._name = ''; s._types = []; s._species = null; s._moveNames = []; s._itemName = '' })
  const promises = []
  t.pokemon.forEach((p,i) => {
    if (i>=6) return
    const sp = speciesResults.value.find(s=>s.id===p.speciesID)
    slots[i].pkm = { speciesID: p.speciesID, level: 50, ability: p.ability||0, nature: p.nature||3, moves: p.moves||[], item: p.item||0, evs: p.evs||{hp:0,atk:0,def:0,spa:0,spd:0,spe:0} }
    slots[i]._name = sp?.name||'#'+p.speciesID; slots[i]._types = sp?.types||[]; slots[i]._species = sp||null
    if (p.moves) p.moves.forEach(mid => {
      if (mid) promises.push(request('get_move',{id:mid}).then(r=>{ moveNamesCache.value[mid] = r?.name||'#'+mid; slots[i]._moveNames = (slots[i].pkm.moves||[]).map(mid=>moveNamesCache.value[mid]||'?') }))
    })
    if (p.item) promises.push(request('get_items',{search:''}).then(r=>{ const it = r.find(x=>x.id===p.item); if (it) { slots[i]._itemName = it.name; itemNamesCache.value[p.item] = it.name } }))
    if (sp) {
      const allAb = [...(sp.abilities||[]), sp.hiddenAbilityID].filter(Boolean)
      allAb.forEach(aid => promises.push(request('get_ability',{id:aid}).then(r=>{abilityNamesCache.value[aid]=r?.name||'#'+aid})))
    }
  })
  await Promise.all(promises)
  activeIdx.value = 0; activeTab.value = 'moves'
  // Load learnset for the active slot only (not all slots)
  loadSlotData()
}
function saveTeam() {
  const pokemon = slots.filter(s=>s.pkm).map(s=>({speciesID:s.pkm.speciesID,level:50,ability:s.pkm.ability||0,nature:s.pkm.nature||3,moves:(s.pkm.moves||[]).filter(m=>m!==0),item:s.pkm.item||0}))
  if (!pokemon.length) return
  send('save_team',{user_id:getPlayerId(),name:teamName.value,pokemon})
  setTimeout(loadSavedTeams, 500)
}
</script>
