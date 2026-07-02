<template>
  <nav class="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b-2 border-b-gray-200 shadow-[0_2px_8px_-2px_rgba(0,0,0,0.08),0_0_1px_rgba(0,0,0,0.04)]">
    <div class="container mx-auto px-6 max-w-7xl">
      <div class="flex items-center justify-between h-12">
        <router-link to="/" class="text-lg font-bold text-gray-700 hover:text-rose-400 transition-colors">
          PokemonSimulator
        </router-link>
        <div class="flex items-center gap-0.5">
          <router-link to="/battles" class="nav-link" active-class="nav-active">对战</router-link>
          <router-link to="/matchmaking" class="nav-link" active-class="nav-active">匹配</router-link>
          <router-link to="/teams" class="nav-link" active-class="nav-active">组队</router-link>
          <router-link to="/history" class="nav-link" active-class="nav-active">历史</router-link>
          <router-link to="/stats" class="nav-link" active-class="nav-active">统计</router-link>
          <router-link to="/data" class="nav-link" active-class="nav-active">数据</router-link>
        </div>
        <div class="flex items-center gap-2">
          <span v-if="username" class="text-sm text-gray-500">{{ username }}</span>
          <router-link v-if="!username" to="/login" class="text-xs px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-600 rounded-lg transition-colors">登录</router-link>
          <button v-else @click="logout" class="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 text-gray-400 rounded-lg">退出</button>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const username = ref('')
onMounted(() => { username.value = localStorage.getItem('trainer_name') || '' })
// Poll for login changes (LoginPage sets localStorage)
setInterval(() => { const n = localStorage.getItem('trainer_name')||''; if (n !== username.value) username.value = n }, 500)
function logout() { username.value = ''; localStorage.removeItem('trainer_name') }
</script>

<style scoped>
.nav-link { @apply px-3 py-1.5 rounded-lg text-sm text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-all; }
.nav-active { @apply text-rose-500 bg-rose-50 font-medium; }
</style>
