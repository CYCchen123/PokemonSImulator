import axios from 'axios'

const client = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// Response interceptor: unwrap { ok, data, error } envelope
client.interceptors.response.use(
  (response) => {
    const body = response.data
    if (body && body.ok === true) {
      response.data = body.data
    } else if (body && body.ok === false) {
      return Promise.reject(new Error(body.error || 'Unknown error'))
    }
    return response
  },
  (error) => {
    if (error.response?.data?.error) {
      return Promise.reject(new Error(error.response.data.error))
    }
    return Promise.reject(error)
  }
)

export default client
