<template>
  <div class="flex items-center justify-center p-8">
    <div class="animate-spin rounded-full h-8 w-8 border-2 border-pokeball-red border-t-transparent"></div>
    <span class="ml-3 text-gray-500">{{ text || '加载中...' }}</span>
  </div>
</template>

<script setup>
defineProps({ text: String })
</script>
