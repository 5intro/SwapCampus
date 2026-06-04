import axios from 'axios'
import { ElMessage } from 'element-plus'

const client = axios.create({
  baseURL: '/api',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  (response) => {
    const data = response.data
    if (data && typeof data.success === 'boolean' && data.success === false) {
      ElMessage.error(data.error?.message || '请求失败')
      return Promise.reject(new Error(data.error?.message || '请求失败'))
    }
    return response
  },
  async (error) => {
    const { config, response } = error

    if (response?.status === 401 && !config._retry) {
      config._retry = true
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const res = await axios.post('/api/users/token/refresh/', {
            refresh: refreshToken,
          })
          const newToken = res.data.data?.access || res.data.access
          localStorage.setItem('access_token', newToken)
          config.headers.Authorization = `Bearer ${newToken}`
          return client(config)
        } catch {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('user')
          window.location.href = '/login'
        }
      } else {
        localStorage.removeItem('access_token')
        localStorage.removeItem('user')
        window.location.href = '/login'
      }
    }

    const msg = response?.data?.error?.message || response?.data?.detail || '网络错误'
    if (response?.status !== 401) {
      ElMessage.error(msg)
    }
    return Promise.reject(error)
  },
)

export default client
