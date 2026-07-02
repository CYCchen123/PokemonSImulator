<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-800 mb-6">🔍 匹配对战</h1>
    <div v-if="!inQueue && !activeBattle" class="max-w-lg mx-auto space-y-6">
      <div class="glass-card p-6">
        <h3 class="text-lg font-bold text-gray-800 mb-4">选择队伍</h3>
        <!-- Saved teams -->
        <div v-if="savedTeams.length" class="space-y-2 mb-4">
          <div v-for="t in savedTeams" :key="t.name" @click="selectTeam(t)"
            class="rounded-xl p-3 cursor-pointer border-2 transition-all duration-200"
            :class="selectedTeam?.name===t.name
              ? 'bg-pokedex-blue/10 border-pokedex-blue shadow-sm'
              : 'bg-white/50 border-gray-200 hover:border-gray-400 hover:shadow-sm'">
            <div class="text-sm text-gray-800 font-bold">{{ t.name }}</div>
            <div class="text-xs text-gray-500 mt-1">{{ t.pokemon?.length||0 }} 只宝可梦</div>
          </div>
        </div>
        <div v-else class="text-center text-gray-400 text-sm py-4">
          还没有保存的队伍，去 <router-link to="/teams" class="text-pokedex-blue hover:text-pokedex-light font-medium">组队页面</router-link> 创建
        </div>
        <button @click="joinQueue" :disabled="!canJoin"
          class="w-full mt-4 py-3 rounded-full font-bold text-lg transition-all duration-200 shadow-md"
          :class="canJoin ? 'bg-pokeball-red hover:bg-red-600 text-white hover:shadow-lg' : 'bg-gray-200 text-gray-400 cursor-not-allowed'">
          ⚡ 加入匹配队列
        </button>
        <div class="mt-3 text-xs font-medium" :class="wsConnected ? 'text-green-500' : 'text-red-400'">
          {{ wsConnected ? '🟢 已连接' : '🔴 未连接' }}
        </div>
      </div>
    </div>

    <!-- Queue waiting -->
    <div v-if="inQueue && !activeBattle" class="max-w-lg mx-auto text-center py-16">
      <div class="glass-card p-10">
        <div class="animate-spin rounded-full h-14 w-14 border-3 border-pokeball-red border-t-transparent mx-auto mb-5"></div>
        <h2 class="text-xl font-bold text-gray-800 mb-2">寻找对手中...</h2>
        <p class="text-gray-400 text-sm mb-6">正在为你匹配实力相当的训练家</p>
        <button @click="leaveQueue" class="px-6 py-2 bg-gray-200 hover:bg-gray-300 text-gray-600 rounded-full text-sm font-medium transition-colors">取消匹配</button>
      </div>
    </div>

    <!-- Active Battle -->
    <div v-if="activeBattle" class="space-y-5">
      <div class="flex items-center justify-between">
        <h1 class="text-xl font-bold text-gray-800">⚡ #{{ activeBattle.id }} ({{ mySide.toUpperCase() }})</h1>
        <div class="flex gap-2 text-sm items-center">
          <span class="text-gray-500">Turn {{ turnNumber }}</span>
          <span v-if="activeBattle.status==='completed'" class="text-amber-500 font-bold">🏆 对战结束</span>
          <button @click="reset" class="px-4 py-1.5 bg-gray-200 hover:bg-gray-300 text-gray-600 rounded-full text-xs font-medium transition-colors">退出</button>
        </div>
      </div>

      <!-- Battle field (dark) -->
      <div class="battle-bg rounded-2xl p-6 border border-gray-700 shadow-xl">
        <div class="flex justify-center gap-3 mb-5 text-xs">
          <span class="px-3 py-1.5 rounded-full bg-gray-800/80 text-gray-300 font-medium">Turn {{ turnNumber }}</span>
          <span v-if="weatherLabel" class="px-3 py-1.5 rounded-full bg-gray-800/80 text-gray-300">{{ weatherLabel }}</span>
          <span v-if="fieldLabel" class="px-3 py-1.5 rounded-full bg-gray-800/80 text-gray-300">{{ fieldLabel }}</span>
        </div>
        <div class="grid grid-cols-2 gap-8 max-w-3xl mx-auto">
          <PokemonCard v-if="pokemonA" :pokemon="pokemonA" side-color="text-blue-300" />
          <PokemonCard v-if="pokemonB" :pokemon="pokemonB" side-color="text-red-300" />
          <div v-if="!pokemonA" class="text-center text-gray-500 text-sm py-4">等待数据...</div>
          <div v-if="!pokemonB" class="text-center text-gray-500 text-sm py-4">等待数据...</div>
        </div>
      </div>

      <!-- Action panel -->
      <div v-if="activeBattle.status==='active'" class="glass-card p-5">
        <h3 class="text-sm font-bold text-gray-700 mb-3">🎮 你的行动 ({{ mySide.toUpperCase() }})</h3>
        <div class="flex gap-2 mb-3">
          <button v-for="t in actionTypes" :key="t.value" @click="actionType=t.value"
            class="px-4 py-2 rounded-full text-xs font-semibold transition-all duration-200"
            :class="actionType===t.value
              ? 'bg-pokeball-red text-white shadow-md'
              : 'bg-gray-100 text-gray-500 hover:bg-gray-200'">{{ t.label }}</button>
        </div>
        <div v-if="actionType==='attack'" class="grid grid-cols-2 gap-2 mb-3">
          <button v-for="(m,i) in myMoves" :key="i" @click="m.pp>0?selectedMove=i:null"
            class="text-left px-3 py-2.5 rounded-xl text-sm transition-all duration-200 border-2"
            :class="m.pp<=0
              ? 'bg-gray-100 border-transparent text-gray-400 cursor-not-allowed opacity-50'
              : selectedMove===i
                ? 'bg-pokeball-red/10 border-pokeball-red text-gray-800 font-semibold'
                : 'bg-gray-50 border-transparent text-gray-600 hover:border-gray-300'">
            <div class="font-medium">{{ moveNames[m.id]||'#'+m.id }}</div>
            <div class="text-xs mt-0.5" :class="m.pp<=0?'text-red-400':'text-gray-400'">PP {{ m.pp }}/{{ m.maxPp }}</div>
          </button>
        </div>
        <div v-if="actionType==='switch'" class="grid grid-cols-3 gap-2 mb-3 max-h-48 overflow-y-auto">
          <button v-for="p in allMyPokemon" :key="p._slot"
            @click="p._canSwitch ? switchTarget=p._slot : null"
            class="text-center px-3 py-2.5 rounded-xl text-xs transition-all duration-200 border-2"
            :class="p._isActive
              ? 'bg-green-100 border-green-400 text-green-700 font-semibold cursor-default'
              : p.fainted
                ? 'bg-gray-100 border-transparent text-gray-400 opacity-40 cursor-not-allowed'
                : switchTarget===p._slot
                  ? 'bg-blue-100 border-blue-400 text-blue-700 font-semibold'
                  : 'bg-white border-gray-200 text-gray-600 hover:border-gray-400 cursor-pointer'"
            :disabled="!p._canSwitch">
            <div class="font-medium">{{ p._speciesName||('#'+p.speciesId) }}</div>
            <div class="text-xs mt-0.5" :class="p.fainted ? 'text-gray-400' : 'text-gray-500'">
              {{ p.fainted ? '濒死' : 'HP '+p.hp+'/'+p.maxHp }}
            </div>
          </button>
        </div>
        <button @click="submitMyAction" :disabled="submitting"
          class="w-full py-3 rounded-full font-bold text-white bg-pokeball-red hover:bg-red-600 disabled:bg-gray-300 transition-all duration-200 text-sm shadow-md hover:shadow-lg">
          {{ submitting ? '⏳ 已提交，等待对手...' : '⚡ 确认行动' }}
        </button>
      </div>

      <!-- Event log (auto-scroll to bottom) -->
      <div class="glass-card p-4 max-h-64 overflow-y-auto scroll-smooth" ref="eventLog">
        <h3 class="text-sm font-bold text-gray-700 mb-3">📜 对战日志</h3>
        <div v-for="(ev,i) in events" :key="i"
          class="flex gap-2 text-xs py-1.5 border-b border-gray-100 last:border-0 animate-fadeIn">
          <span class="text-gray-400 w-6 shrink-0 font-mono">#{{ i }}</span>
          <span class="px-1.5 py-0.5 rounded-full shrink-0 text-xs" :class="evBadge(ev.event_type)">{{ ev.event_type||'info' }}</span>
          <span class="text-gray-700">{{ ev.description }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted, watch } from 'vue'
import PokemonCard from '../components/battle/PokemonCard.vue'
import { connect, send, on, getPlayerId, request } from '../api/wsClient'
import { getMoveName } from '../api/dataWs'

const inQueue = ref(false)
const wsConnected = ref(false)
const activeBattle = ref(null)
const mySide = ref('a')
const battleState = ref(null)
const loading = ref(false)
const actionType = ref('attack')
const selectedMove = ref(0)
const submitting = ref(false)
const moveNames = ref({})
const savedTeams = ref([])
const selectedTeam = ref(null)
const submittedMsg = ref('')
const actionTypes = [{value:'attack',label:'⚔️ 攻击'},{value:'switch',label:'🔄 换人'},{value:'pass',label:'⏭️ 跳过'}]
const switchTarget = ref(0)
const canJoin = computed(() => selectedTeam.value?.pokemon?.length > 0)
const allMyPokemon = computed(() => {
  const sidesArr = sides.value
  const side = mySide.value === 'a' ? sidesArr[0] : sidesArr[1]
  if (!side) return []
  const activeIdx = side.active || 0
  return (side.pokemons || []).map((p, i) => ({
    ...p,
    _idx: i,
    _slot: p.slot ?? i,
    _isActive: i === activeIdx,
    _canSwitch: !p.fainted && i !== activeIdx
  }))
})
const turnNumber = computed(() => battleState.value?.turn ?? 0)
const sides = computed(() => battleState.value?.battle?.sides || [])
const pokemonA = computed(() => sides.value[0]?.pokemons?.[sides.value[0]?.active||0])
const pokemonB = computed(() => sides.value[1]?.pokemons?.[sides.value[1]?.active||0])
const myMoves = computed(() => {
  const p = mySide.value==='a'?pokemonA.value:pokemonB.value
  return (p?.moves||[]).map(m => {
    if (m.id&&!moveNames.value[m.id]) getMoveName(m.id).then(n=>moveNames.value[m.id]=n)
    return m
  })
})
const events = computed(() => battleState.value?.events||[])
const eventLog = ref(null)
watch(events, () => {
  setTimeout(() => { if (eventLog.value) eventLog.value.scrollTop = eventLog.value.scrollHeight }, 50)
})
function evBadge(t) {
  const m = {switch_in:'bg-green-100 text-green-600',ability_trigger:'bg-purple-100 text-purple-600',status_apply:'bg-orange-100 text-orange-600',heal:'bg-emerald-100 text-emerald-600',damage:'bg-red-100 text-red-600',stat_change:'bg-blue-100 text-blue-600',faint:'bg-gray-200 text-gray-600',info:'bg-gray-100 text-gray-500'}
  return m[t]||'bg-gray-100 text-gray-500'
}
const weatherLabel = computed(() => {
  const w = battleState.value?._weather; return w?.type ? `${w.label} ${w.duration}t` : ''
})
const fieldLabel = computed(() => {
  const f = battleState.value?._field; return f?.type ? `${f.label} ${f.duration}t` : ''
})

let unsubs = []
async function setupWS() {
  try { await connect('Player'); wsConnected.value=true } catch { wsConnected.value=false; setTimeout(setupWS,1500); return }
  const uid = getPlayerId()
  if (uid) {
    try { savedTeams.value = await request('get_user_teams',{user_id:uid}) } catch { savedTeams.value = [] }
  }
  unsubs.push(on('handshake_ok',()=>{wsConnected.value=true}))
  unsubs.push(on('user_teams',(d)=>{savedTeams.value = d}))
  unsubs.push(on('matchmaking_status',(d)=>{
    if(d.status==='waiting') inQueue.value=true
    if(d.status==='already_queued'){ inQueue.value=true; submittedMsg.value='已在队列中，请勿重复加入' }
  }))
  unsubs.push(on('matched',(d)=>{
    inQueue.value=false; activeBattle.value={id:d.battle_id,status:'active'}; mySide.value=d.side
    battleState.value=d.state; loading.value=false
  }))
  unsubs.push(on('battle_state_update',(d)=>{
    battleState.value=d.state; loading.value=false
  }))
  unsubs.push(on('turn_processed',(d)=>{
    battleState.value=d.state; submitting.value=false
    if(activeBattle.value)activeBattle.value.status=d.status
  }))
  unsubs.push(on('action_submitted',()=>{ submittedMsg.value = '已提交, 等待对手...' }))
}
setupWS()

function selectTeam(t) { selectedTeam.value = t }
async function joinQueue() {
  const teamJson = JSON.stringify({name:selectedTeam.value.name,pokemon:selectedTeam.value.pokemon})
  send('join_matchmaking',{player_id:getPlayerId(),team_json:teamJson})
}
async function submitMyAction() {
  submitting.value=true
  const action = {side:mySide.value,type:actionType.value}
  if(actionType.value==='attack')action.move_index=selectedMove.value
  if(actionType.value==='switch')action.switch_index=switchTarget.value
  send('submit_action',{battle_id:activeBattle.value.id,action})
}
function leaveQueue(){inQueue.value=false}
function reset(){activeBattle.value=null;battleState.value=null;submitting.value=false;loading.value=false}
onUnmounted(()=>{unsubs.forEach(fn=>fn())})
</script>
