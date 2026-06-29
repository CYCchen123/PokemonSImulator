import client from './client'

export const battleAPI = {
  list: (params) => client.get('/battles', { params }),
  get: (id) => client.get(`/battles/${id}`),
  create: (data) => client.post('/battles', data),
  processTurn: (id, actions) => client.post(`/battles/${id}/turns`, { actions }),
}
