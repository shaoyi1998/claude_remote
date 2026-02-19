<template>
  <div class="page login-page">
    <div class="login-container">
      <div class="login-header">
        <h1>Claude Remote</h1>
        <p>Claude Code 远程任务管理</p>
      </div>

      <div v-if="error" class="error-message">{{ error }}</div>

      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label class="form-label">用户名</label>
          <input
            v-model="form.username"
            type="text"
            class="form-input"
            placeholder="请输入用户名"
            required
          />
        </div>

        <div class="form-group">
          <label class="form-label">密码</label>
          <input
            v-model="form.password"
            type="password"
            class="form-input"
            placeholder="请输入密码"
            required
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
          <span v-else>登录</span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import { syncFromServer } from '../stores/shortcuts'

const router = useRouter()
const loading = ref(false)
const error = ref('')

const form = reactive({
  username: '',
  password: ''
})

onMounted(() => {
  // 检查是否需要初始化
  checkInit()
})

async function checkInit() {
  try {
    const res = await api.post('/users/init')
    if (res.data.message) {
      error.value = `初始账号: ${res.data.username} / ${res.data.password}`
    }
  } catch (e) {
    // 已有用户，忽略
  }
}

async function handleLogin() {
  loading.value = true
  error.value = ''

  try {
    const formData = new FormData()
    formData.append('username', form.username)
    formData.append('password', form.password)

    const res = await api.post('/auth/login', formData)
    localStorage.setItem('token', res.data.access_token)

    // 登录成功后从服务器同步快捷键配置
    await syncFromServer()

    router.push('/')
  } catch (e) {
    error.value = e.response?.data?.detail || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 24px;
}

.login-container {
  width: 100%;
  max-width: 360px;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h1 {
  font-size: 1.75rem;
  margin-bottom: 8px;
}

.login-header p {
  color: var(--text-secondary);
  font-size: 0.875rem;
}
</style>
