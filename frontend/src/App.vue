<template>
  <div class="min-h-screen flex flex-col">
    <AppNavbar />
    <main class="flex-1 container mx-auto px-4 py-6 max-w-7xl">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import AppNavbar from './components/layout/AppNavbar.vue'
</script>
