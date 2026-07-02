/**
 * Data query helpers using WebSocket request/response pattern.
 * Caches results for instant re-access.
 */
import { request, connect, getPlayerId } from './wsClient'

let _ready = false
async function ensure() {
  if (!_ready) {
    await connect('DataClient')
    _ready = true
  }
}

const cache = { species: {}, moves: {}, abilities: {} }

export async function searchSpecies(query = '') {
  await ensure()
  const data = await request('get_species', { search: query || '', limit: 15 })
  data.forEach(s => { cache.species[s.id] = s })
  return data
}

export async function searchMoves(query = '', learnset = null) {
  await ensure()
  const params = { search: query || '', limit: 15 }
  if (learnset && learnset.length > 0) params.learnset = learnset
  const data = await request('get_moves', params)
  data.forEach(m => { cache.moves[m.id] = m })
  return data
}

export async function getMove(id) {
  if (cache.moves[id]) return cache.moves[id]
  await ensure()
  const data = await request('get_move', { id })
  cache.moves[id] = data
  return data
}

export async function getMoveName(id) {
  const m = await getMove(id)
  return m?.name || `#${id}`
}

export async function getAbility(id) {
  if (!id) return { name: '无' }
  if (cache.abilities[id]) return cache.abilities[id]
  await ensure()
  const data = await request('get_ability', { id })
  cache.abilities[id] = data
  return data
}

export async function getAbilityName(id) {
  const a = await getAbility(id)
  return a?.name || `#${id}`
}

export async function searchAbilities(query = '') {
  await ensure()
  const data = await request('get_abilities', { search: query || '' })
  data.forEach(a => { cache.abilities[a.id] = a })
  return data
}

// Sprite URL cache (fetched from server)
const spriteUrlCache = {}
export async function getSpriteUrl(speciesId) {
  if (!speciesId) return ''
  if (spriteUrlCache[speciesId]) return spriteUrlCache[speciesId]
  await ensure()
  try {
    const data = await request('get_sprite_url', { id: speciesId })
    spriteUrlCache[speciesId] = data.url || `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/${speciesId}.gif`
  } catch {
    spriteUrlCache[speciesId] = `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/${speciesId}.gif`
  }
  return spriteUrlCache[speciesId]
}
