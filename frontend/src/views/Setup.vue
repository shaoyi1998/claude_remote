<template>
  <div class="page setup-page">
    <div class="setup-container">
      <div class="setup-header">
        <h1>Claude Remote</h1>
        <p>首次使用，请配置服务器地址</p>
      </div>

      <div class="setup-card">
        <div class="setup-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
            <line x1="8" y1="21" x2="16" y2="21"></line>
            <line x1="12" y1="17" x2="12" y2="21"></line>
          </svg>
        </div>

        <p class="setup-hint">
          请输入运行后端服务的电脑 IP 地址<br>
          确保手机和电脑在同一局域网内
        </p>

        <div v-if="error" class="error-message">{{ error }}</div>
        <div v-if="success" class="success-message">{{ success }}</div>

        <form @submit.prevent="handleSave">
          <div class="form-group">
            <label class="form-label">服务器地址</label>
            <input
              v-model="serverHost"
              type="text"
              class="form-input"
              placeholder="如: 192.168.1.100"
              required
            />
          </div>

          <div class="form-group">
            <label class="form-label">服务器端口</label>
            <input
              v-model="serverPort"
              type="number"
              class="form-input"
              placeholder="默认: 8000"
            />
          </div>

          <button
            type="submit"
            class="btn btn-primary btn-block"
            :disabled="loading"
          >
            <span v-if="loading" class="loading">
              <span class="spinner" style="width: 20px; height: 20px;"></span>
            </span>
            <span v-else>保存并测试连接</span>
          </button>
        </form>

        <div class="setup-tips">
          <h3>如何获取电脑 IP？</h3>
          <ol>
            <li>在电脑上打开命令提示符（Win+R 输入 cmd）</li>
            <li>输入 <code>ipconfig</code> 并回车</li>
            <li>找到"IPv4 地址"那一行</li>
          </ol>
        </div>

        <div class="setup-footer" v-if="hasConfig">
          <button class="btn btn-secondary btn-block" @click="skipSetup">
            跳过（使用当前配置）
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { saveServerConfig, getServerAddress, updateApiBaseURL } from '../api'
import axios from 'axios'

const router = useRouter()
const serverHost = ref('')
const serverPort = ref('8000')
const loading = ref(false)
const error = ref('')
const success = ref('')
const hasConfig = ref(false)

onMounted(() => {
  const config = getServerAddress()
  serverHost.value = config.host || ''
  serverPort.value = config.port || '8000'
  hasConfig.value = !!(config.host && config.host !== 'localhost' && config.host !== window.location.hostname)
})

async function handleSave() {
  if (!serverHost.value) {
    error.value = '请输入服务器地址'
    return
  }

  loading.value = true
  error.value = ''
  success.value = ''

  try {
    // 先测试连接
    const testUrl = `http://${serverHost.value}:${serverPort.value || '8000'}/api/platform`
    await axios.get(testUrl, { timeout: 5000 })

    // 连接成功，保存配置
    saveServerConfig(serverHost.value, serverPort.value || '8000')
    success.value = '连接成功！正在跳转...'

    setTimeout(() => {
      router.push('/login')
    }, 1000)
  } catch (e) {
    error.value = '无法连接到服务器，请检查地址和网络'
  } finally {
    loading.value = false
  }
}

function skipSetup() {
  router.push('/login')
}
</script>

<style scoped>
.setup-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 24px;
}

.setup-container {
  width: 100%;
  max-width: 400px;
}

.setup-header {
  text-align: center;
  margin-bottom: 24px;
}

.setup-header h1 {
  font-size: 1.75rem;
  margin-bottom: 8px;
}

.setup-header p {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.setup-card {
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
  padding: 24px;
}

.setup-icon {
  text-align: center;
  color: var(--primary-color);
  margin-bottom: 16px;
}

.setup-hint {
  text-align: center;
  color: var(--text-secondary);
  font-size: 0.875rem;
  margin-bottom: 24px;
  line-height: 1.6;
}

.error-message {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #ef4444;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 16px;
  text-align: center;
}

.success-message {
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.3);
  color: #22c55e;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 16px;
  text-align: center;
}

.setup-tips {
  margin-top: 24px;
  padding: 16px;
  background: var(--bg-card);
  border-radius: 8px;
}

.setup-tips h3 {
  font-size: 0.875rem;
  margin-bottom: 12px;
  color: var(--text-secondary);
}

.setup-tips ol {
  padding-left: 20px;
  margin: 0;
}

.setup-tips li {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-bottom: 8px;
  line-height: 1.5;
}

.setup-tips code {
  background: var(--bg-secondary);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
  color: var(--primary-color);
}

.setup-footer {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color, #333);
}
</style>
