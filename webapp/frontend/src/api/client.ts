import axios from 'axios'

export const api = axios.create({
  baseURL: '/api/v1',
  timeout: 120_000,
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    const msg = err?.response?.data?.detail || err?.message || '请求失败'
    return Promise.reject(new Error(msg))
  },
)
