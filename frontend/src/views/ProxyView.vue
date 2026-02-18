<template>
  <div class="proxy-view">
    <div class="proxy-header">
      <h1>反向代理</h1>
      <p class="subtitle">通过代理访问本地开发服务器</p>
    </div>

    <div class="proxy-form">
      <div class="form-group">
        <label for="port">端口号</label>
        <input
          id="port"
          v-model="port"
          type="number"
          placeholder="例如: 5173"
          min="1024"
          max="65535"
        />
      </div>

      <div class="form-group">
        <label for="path">路径 (可选)</label>
        <input
          id="path"
          v-model="path"
          type="text"
          placeholder="例如: / 或 /index.html"
        />
      </div>

      <button class="btn-primary" @click="openProxy" :disabled="!isValidPort">
        打开代理
      </button>
    </div>

    <div class="proxy-info">
      <h3>使用说明</h3>
      <ul>
        <li>输入本地开发服务器的端口号（如 Vite 默认 5173）</li>
        <li>点击"打开代理"将在新标签页中打开代理地址</li>
        <li>代理会自动携带认证信息</li>
      </ul>

      <h3>常用端口</h3>
      <div class="port-suggestions">
        <button
          v-for="p in commonPorts"
          :key="p.port"
          class="port-btn"
          @click="selectPort(p.port)"
        >
          {{ p.port }} - {{ p.name }}
        </button>
      </div>
    </div>

    <div class="proxy-warning">
      <strong>注意：</strong> 代理仅支持端口 1024-65535，不支持特权端口。
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { getServerAddress } from '../api'

const port = ref('')
const path = ref('/')

const commonPorts = [
  { port: 5173, name: 'Vite' },
  { port: 3000, name: 'Node.js' },
  { port: 8080, name: 'Vue CLI' },
  { port: 4200, name: 'Angular' },
  { port: 5000, name: 'Flask' },
  { port: 8000, name: 'Django' },
]

const isValidPort = computed(() => {
  const p = parseInt(port.value)
  return p >= 1024 && p <= 65535
})

function selectPort(p) {
  port.value = p
}

function openProxy() {
  if (!isValidPort.value) return

  const { host, port: serverPort } = getServerAddress()
  const token = localStorage.getItem('token')

  // 构建代理 URL
  let proxyPath = path.value || '/'
  if (!proxyPath.startsWith('/')) {
    proxyPath = '/' + proxyPath
  }

  const proxyUrl = `http://${host}:${serverPort}/proxy/${port.value}${proxyPath}?token=${encodeURIComponent(token)}`

  // 在新标签页打开
  window.open(proxyUrl, '_blank')
}
</script>

<style scoped>
.proxy-view {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.proxy-header {
  text-align: center;
  margin-bottom: 30px;
}

.proxy-header h1 {
  font-size: 24px;
  margin-bottom: 8px;
}

.subtitle {
  color: #666;
  font-size: 14px;
}

.proxy-form {
  background: #f5f5f5;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
}

.form-group input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
  box-sizing: border-box;
}

.btn-primary {
  width: 100%;
  padding: 12px;
  background: #1976d2;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
}

.btn-primary:hover {
  background: #1565c0;
}

.btn-primary:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.proxy-info {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
  margin-bottom: 20px;
}

.proxy-info h3 {
  font-size: 16px;
  margin-bottom: 10px;
}

.proxy-info ul {
  margin: 0 0 15px 0;
  padding-left: 20px;
}

.proxy-info li {
  margin-bottom: 6px;
  color: #555;
  font-size: 14px;
}

.port-suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.port-btn {
  padding: 6px 12px;
  background: #e3f2fd;
  border: 1px solid #90caf9;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
}

.port-btn:hover {
  background: #bbdefb;
}

.proxy-warning {
  background: #fff3e0;
  padding: 12px;
  border-radius: 4px;
  font-size: 13px;
  color: #e65100;
}
</style>
