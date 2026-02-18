<template>
  <div class="page">
    <div class="header">
      <button class="btn btn-sm btn-secondary" @click="goBack">取消</button>
      <h1>新建任务</h1>
      <div></div>
    </div>

    <div v-if="error" class="error-message">{{ error }}</div>

    <form @submit.prevent="createTask">
      <div class="form-group">
        <label class="form-label">项目名</label>
        <input
          v-model="form.project_name"
          type="text"
          class="form-input"
          placeholder="输入项目名"
          required
        />
        <small class="form-hint">工作目录: {{ fullWorkDir }}</small>
      </div>

      <div class="form-group">
        <label class="form-label">默认目录前缀</label>
        <input
          v-model="form.work_dir_prefix"
          type="text"
          class="form-input"
          placeholder="~/claude_project/"
        />
      </div>

      <!-- 启动参数 -->
      <div class="form-group">
        <label class="form-label">启动参数</label>
        <div class="checkbox-group">
          <label class="checkbox-label">
            <input type="checkbox" v-model="form.skip_permissions" />
            <span>--dangerously-skip-permissions</span>
            <small>跳过权限确认</small>
          </label>
          <label class="checkbox-label">
            <input type="checkbox" v-model="form.teammate_mode" />
            <span>--teammate-mode auto</span>
            <small>启用团队协作模式</small>
          </label>
        </div>
      </div>

      <button
        type="submit"
        class="btn btn-primary btn-block"
        :disabled="loading"
      >
        <span v-if="loading" class="loading">
          <span class="spinner" style="width: 20px; height: 20px;"></span>
        </span>
        <span v-else>创建任务</span>
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()
const loading = ref(false)
const error = ref('')

// 从 localStorage 读取默认目录前缀
const savedPrefix = localStorage.getItem('work_dir_prefix') || '~/claude_project/'

const form = reactive({
  project_name: '',
  work_dir_prefix: savedPrefix,
  skip_permissions: false,
  teammate_mode: false
})

// 计算完整工作目录
const fullWorkDir = computed(() => {
  const prefix = form.work_dir_prefix.endsWith('/')
    ? form.work_dir_prefix
    : form.work_dir_prefix + '/'
  return prefix + (form.project_name || '项目名')
})

async function createTask() {
  if (!form.project_name.trim()) {
    error.value = '请输入项目名'
    return
  }

  // 保存目录前缀到 localStorage
  localStorage.setItem('work_dir_prefix', form.work_dir_prefix)

  loading.value = true
  error.value = ''

  try {
    const res = await api.post('/tasks', {
      name: form.project_name,
      work_dir: fullWorkDir.value,
      skip_permissions: form.skip_permissions,
      teammate_mode: form.teammate_mode
    })
    router.push(`/task/${res.data.id}`)
  } catch (e) {
    error.value = e.response?.data?.detail || '创建任务失败'
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push('/')
}
</script>

<style scoped>
.header {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 12px;
  align-items: center;
}

.header h1 {
  text-align: center;
  font-size: 1.1rem;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  cursor: pointer;
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
}

.checkbox-label input[type="checkbox"] {
  margin-top: 2px;
  width: 18px;
  height: 18px;
}

.checkbox-label span {
  font-weight: 500;
}

.checkbox-label small {
  display: block;
  color: var(--text-secondary);
  font-size: 0.75rem;
  margin-top: 2px;
}

.form-hint {
  display: block;
  color: var(--text-secondary);
  font-size: 0.8rem;
  margin-top: 4px;
  font-family: monospace;
  background: var(--bg-secondary);
  padding: 4px 8px;
  border-radius: 4px;
}
</style>
