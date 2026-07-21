// 后端 API 地址 — 开发环境走 Vite proxy，生产环境走环境变量
const API_BASE = import.meta.env.VITE_API_URL || '/api'

export default API_BASE
