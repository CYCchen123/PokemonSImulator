<template>
  <div class="min-h-[calc(100vh-80px)] flex items-center justify-center">
    <div class="bg-white rounded-2xl p-8 w-96 shadow-xl border border-gray-100 text-center">
      <div class="text-5xl mb-4">⚔️</div>
      <h1 class="text-xl font-bold text-gray-800 mb-2">PokemonSimulator</h1>
      <p class="text-sm text-gray-400 mb-6">登录后可跨设备同步队伍</p>
      <input v-model="name" @keyup.enter="login" placeholder="训练家名称"
        class="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-sm text-gray-700 mb-4 text-center focus:outline-none focus:ring-2 focus:ring-rose-300" />
      <button @click="login" :disabled="!name.trim()"
        class="w-full py-3 rounded-xl font-bold text-white bg-rose-400 hover:bg-rose-500 disabled:bg-gray-300 transition-colors">
        登录
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { connect, send } from '../api/wsClient'

const router = useRouter()
const name = ref(localStorage.getItem('trainer_name') || '')

async function login() {
  if (!name.value.trim()) return
  localStorage.setItem('trainer_name', name.value.trim())
  try { await connect(name.value.trim()); send('save_user', { name: name.value.trim() }) } catch {}
  router.push('/')
}
</script>
