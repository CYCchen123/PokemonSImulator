import { defineStore } from 'pinia'
import { ref } from 'vue'
import { dataAPI } from '../api/stats'

export const useDataStore = defineStore('data', () => {
  const enums = ref(null)
  const loading = ref(false)

  async function fetchEnums() {
    if (enums.value) return enums.value
    loading.value = true
    try {
      const result = await dataAPI.enums()
      enums.value = result.data
      return result.data
    } finally {
      loading.value = false
    }
  }

  return { enums, loading, fetchEnums }
})
