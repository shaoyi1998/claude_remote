import axios from 'axios'

// 获取服务器地址（优先从 localStorage 读取用户配置）
function getServerHost() {
  return localStorage.getItem('serverHost') || window.location.hostname
}

function getServerPort() {
  return localStorage.getItem('serverPort') || '8000'
}

// 动态构建 API 基础地址
function getApiBaseURL() {
  const host = getServerHost()
  const port = getServerPort()
  return `http://${host}:${port}/api`
}

// 创建 axios 实例
const api = axios.create({
  baseURL: getApiBaseURL(),
  timeout: 30000
})

// 更新 API 基础地址（当用户修改服务器配置时调用）
export function updateApiBaseURL() {
  api.defaults.baseURL = getApiBaseURL()
}

// 请求拦截器 - 添加 token
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

// 响应拦截器 - 处理错误
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// 获取服务器地址（供 WebSocket 使用）
export function getServerAddress() {
  return {
    host: getServerHost(),
    port: getServerPort()
  }
}

// 保存服务器配置
export function saveServerConfig(host, port) {
  if (host) {
    localStorage.setItem('serverHost', host)
  } else {
    localStorage.removeItem('serverHost')
  }
  if (port) {
    localStorage.setItem('serverPort', port)
  } else {
    localStorage.removeItem('serverPort')
  }
  // 更新 axios 实例的 baseURL
  updateApiBaseURL()
}

export default api
