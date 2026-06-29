import client from './client'

export const statsAPI = {
  global: () => client.get('/stats/global'),
}

export const dataAPI = {
  enums: () => client.get('/data/enums'),
}
