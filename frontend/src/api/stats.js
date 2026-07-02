import client from './client'

export const statsAPI = {
  global: () => client.get('/stats/global'),
  // Deep analytics
  deepSummary: () => client.get('/stats/deep/summary'),
  deepMeta: () => client.get('/stats/deep/meta'),
  deepMoves: () => client.get('/stats/deep/moves'),
  deepItems: () => client.get('/stats/deep/items'),
  deepAbilities: () => client.get('/stats/deep/abilities'),
  deepTypes: () => client.get('/stats/deep/types'),
  deepBattle: () => client.get('/stats/deep/battle'),
  deepPokemonHp: () => client.get('/stats/deep/pokemon-hp'),
  deepEvents: () => client.get('/stats/deep/events'),
  deepSurvival: () => client.get('/stats/deep/survival'),
  deepAll: () => client.get('/stats/deep/all'),
  deepLive: () => client.get('/stats/deep/live'),
  deepRefresh: () => client.post('/stats/deep/refresh', {}),
  pokemonDetail: (speciesId) => client.get(`/stats/deep/pokemon/${speciesId}`),
}

export const dataAPI = {
  enums: () => client.get('/data/enums'),
}
