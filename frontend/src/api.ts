import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 180000
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers = config.headers || {}
    config.headers['Authorization'] = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    const status = err?.response?.status
    if (status === 401) {
      localStorage.removeItem('token')
    }
    return Promise.reject(err)
  }
)

export function setToken(token: string | null) {
  if (!token) localStorage.removeItem('token')
  else localStorage.setItem('token', token)
}

export function getToken(): string | null {
  return localStorage.getItem('token')
}

export default api
