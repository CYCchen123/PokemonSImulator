import { defineStore } from 'pinia'
import { ref } from 'vue'
import { teamAPI } from '../api/teams'
import { playerAPI } from '../api/players'

export const useTeamStore = defineStore('team', () => {
  const teams = ref([])
  const players = ref([])
  const loading = ref(false)

  async function fetchTeams(playerId = null) {
    loading.value = true
    try {
      const result = await teamAPI.list(playerId ? { player_id: playerId } : {})
      teams.value = result.data || []
    } finally {
      loading.value = false
    }
  }

  async function createTeam(playerId, name, pokemon) {
    const result = await teamAPI.create({ player_id: playerId, name, pokemon })
    teams.value.unshift(result.data)
    return result.data
  }

  async function deleteTeam(id) {
    await teamAPI.delete(id)
    teams.value = teams.value.filter(t => t.id !== id)
  }

  async function fetchPlayers() {
    const result = await playerAPI.list({ limit: 100 })
    players.value = result.data || []
  }

  async function createPlayer(name) {
    const result = await playerAPI.create(name)
    players.value.unshift(result.data)
    return result.data
  }

  return { teams, players, loading, fetchTeams, createTeam, deleteTeam, fetchPlayers, createPlayer }
})
