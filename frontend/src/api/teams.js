import client from './client'

export const teamAPI = {
  list: (params) => client.get('/teams', { params }),
  get: (id) => client.get(`/teams/${id}`),
  create: (data) => client.post('/teams', data),
  delete: (id) => client.delete(`/teams/${id}`),
}
