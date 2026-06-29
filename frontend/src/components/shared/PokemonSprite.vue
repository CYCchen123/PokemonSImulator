<template>
  <div class="pokemon-sprite" :class="sizeClass">
    <img
      v-if="!imgError"
      :src="spriteUrl"
      :alt="`#${speciesId}`"
      :class="animated ? 'pixelated' : ''"
      @error="onImgError"
      loading="lazy"
    />
    <!-- Fallback: show species ID -->
    <div v-else class="sprite-fallback">
      <span class="text-xs text-gray-500">#{{ speciesId }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { getAnimatedSprite, getIconSprite } from '../../utils/sprites'

const props = defineProps({
  speciesId: { type: Number, required: true },
  animated: { type: Boolean, default: true },
  size: { type: String, default: 'md' }, // sm, md, lg
  back: { type: Boolean, default: false },
})

const imgError = ref(false)

const spriteUrl = computed(() => {
  if (props.size === 'sm' || props.size === 'icon') {
    return getIconSprite(props.speciesId)
  }
  // Use animated Showdown-style sprites from PokeAPI
  return getAnimatedSprite(props.speciesId)
})

const sizeClass = computed(() => {
  switch (props.size) {
    case 'sm': return 'w-8 h-8'
    case 'lg': return 'w-24 h-24'
    case 'xl': return 'w-32 h-32'
    default: return 'w-16 h-16'
  }
})

function onImgError() {
  imgError.value = true
}
</script>

<style scoped>
.pokemon-sprite {
  display: flex;
  align-items: center;
  justify-content: center;
}
.pokemon-sprite img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.pixelated {
  image-rendering: pixelated;
}
.sprite-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255,255,255,0.05);
  border-radius: 50%;
}
</style>
