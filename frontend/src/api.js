// 后端 API 地址 — 开发环境走 Vite proxy，生产环境走环境变量
const API_BASE = import.meta.env.VITE_API_URL || '/api'

function getToken() {
  return localStorage.getItem('token') || ''
}

async function request(method, url, data = null, options = {}) {
  const fullUrl = url.startsWith('http') ? url : `${API_BASE}${url.startsWith('/') ? url : '/' + url}`
  const headers = {
    'Accept': 'application/json',
    ...(data ? { 'Content-Type': 'application/json' } : {}),
    ...(options.headers || {}),
  }
  const token = getToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const fetchOptions = {
    method,
    headers,
    ...(data ? { body: JSON.stringify(data) } : {}),
    ...options,
  }

  const response = await fetch(fullUrl, fetchOptions)
  const text = await response.text()
  let parsed = null
  try {
    parsed = text ? JSON.parse(text) : null
  } catch {
    parsed = text
  }

  const axiosLikeError = new Error(`HTTP ${response.status}`)
  axiosLikeError.response = { status: response.status, data: parsed }
  axiosLikeError.request = { method, url: fullUrl }

  if (!response.ok) {
    // 401 统一抛出，便于页面跳登录
    if (response.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      // 不自动跳转，让页面自己处理
    }
    throw axiosLikeError
  }

  // 兼容 axios 的 response.data 写法
  return {
    data: parsed,
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
    config: fetchOptions,
    request: fetchOptions,
  }
}

const api = {
  get: (url, options = {}) => request('GET', url, null, options),
  post: (url, data, options = {}) => request('POST', url, data, options),
  put: (url, data, options = {}) => request('PUT', url, data, options),
  patch: (url, data, options = {}) => request('PATCH', url, data, options),
  delete: (url, options = {}) => request('DELETE', url, null, options),
}

export { API_BASE }
export default api
