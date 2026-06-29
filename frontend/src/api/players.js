import client from './client'

export const playerAPI = {
  list: (params) => client.get('/players', { params }),
  get: (id) => client.get(`/players/${id}`),
  create: (name) => client.post('/players', { name }),
}
