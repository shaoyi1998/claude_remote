<template>
  <div class="page">
    <div class="header">
      <h1>任务列表</h1>
      <div class="header-actions">
        <button class="btn btn-sm btn-secondary" @click="goToSettings">设置</button>
        <button class="btn btn-sm btn-secondary" @click="logout">退出</button>
      </div>
    </div>

    <div v-if="error" class="error-message">{{ error }}</div>

    <div v-if="loading" class="loading">
      <span class="spinner"></span>
    </div>

    <template v-else>
      <!-- 筛选器 -->
      <div class="filter-bar">
        <button
          v-for="f in filters"
          :key="f.value"
          :class="['filter-btn', { active: currentFilter === f.value }]"
          @click="currentFilter = f.value"
        >
          {{ f.label }}
          <span v-if="f.count > 0" class="filter-count">{{ f.count }}</span>
        </button>
      </div>

      <div v-if="filteredTasks.length === 0" class="empty-state">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
          <line x1="9" y1="9" x2="15" y2="9"></line>
          <line x1="9" y1="13" x2="15" y2="13"></line>
          <line x1="9" y1="17" x2="12" y2="17"></line>
        </svg>
        <p>{{ currentFilter === 'all' ? '暂无任务' : '没有' + getFilterLabel(currentFilter) + '的任务' }}</p>
        <p v-if="currentFilter === 'all'" style="font-size: 0.75rem; margin-top: 8px;">点击右下角按钮创建新任务</p>
      </div>

      <div v-else class="task-list">
        <div
          v-for="task in filteredTasks"
          :key="task.id"
          :class="['card', 'task-item', { 'task-stopped': task.status === 'stopped' }]"
          @click="goToTask(task.id)"
        >
          <div class="card-header">
            <span class="card-title">{{ task.name }}</span>
            <span :class="['status-badge', 'status-' + task.status]">
              {{ statusText(task.status) }}
            </span>
          </div>
          <div class="card-subtitle">{{ task.work_dir }}</div>
          <div v-if="task.session_name" class="card-subtitle">会话: {{ task.session_name }}</div>
          <div class="actions">
            <button
              class="btn btn-sm btn-secondary"
              @click.stop="openSettings(task)"
            >
              配置
            </button>
            <button
              v-if="task.status === 'stopped'"
              class="btn btn-sm btn-primary"
              @click.stop="restoreTask(task.id)"
            >
              恢复
            </button>
            <button
              v-if="task.status === 'running'"
              class="btn btn-sm btn-secondary"
              @click.stop="stopTask(task.id)"
            >
              终止
            </button>
            <button
              class="btn btn-sm btn-danger"
              @click.stop="deleteTask(task.id)"
            >
              删除
            </button>
          </div>
        </div>
      </div>
    </template>

    <button class="fab" @click="goToNew">+</button>

    <!-- 设置弹窗 -->
    <div v-if="showSettings" class="modal-overlay" @click.self="showSettings = false">
      <div class="modal">
        <div class="modal-header">
          <h3>任务配置</h3>
          <button class="btn btn-sm btn-secondary" @click="showSettings = false">关闭</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">任务名称</label>
            <input type="text" v-model="editTaskName" class="text-input" placeholder="输入任务名称" />
          </div>
          <p class="settings-hint">修改以下设置后，下次恢复会话时生效</p>
          <div class="checkbox-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="settings.skip_permissions" />
              <span>--dangerously-skip-permissions</span>
              <small>跳过权限确认</small>
            </label>
            <label class="checkbox-label">
              <input type="checkbox" v-model="settings.teammate_mode" />
              <span>--teammate-mode auto</span>
              <small>启用团队协作模式</small>
            </label>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-primary" @click="saveSettings" :disabled="savingSettings">
            {{ savingSettings ? '保存中...' : '保存设置' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()
const loading = ref(true)
const error = ref('')
const tasks = ref([])
const showSettings = ref(false)
const savingSettings = ref(false)
const currentTask = ref(null)
const currentFilter = ref('all')
const editTaskName = ref('')

const settings = reactive({
  skip_permissions: false,
  teammate_mode: false
})

// 筛选器配置
const filters = computed(() => [
  { value: 'all', label: '全部', count: tasks.value.length },
  { value: 'running', label: '运行中', count: tasks.value.filter(t => t.status === 'running').length },
  { value: 'stopped', label: '已停止', count: tasks.value.filter(t => t.status === 'stopped').length },
])

// 筛选后的任务列表
const filteredTasks = computed(() => {
  if (currentFilter.value === 'all') {
    return tasks.value
  }
  return tasks.value.filter(t => t.status === currentFilter.value)
})

function getFilterLabel(filter) {
  const map = { running: '运行中', stopped: '已停止' }
  return map[filter] || filter
}

onMounted(() => {
  loadTasks()
})

async function loadTasks() {
  try {
    const res = await api.get('/tasks')
    tasks.value = res.data
  } catch (e) {
    error.value = '加载任务失败'
  } finally {
    loading.value = false
  }
}

function statusText(status) {
  const map = {
    running: '运行中',
    stopped: '已停止',
    error: '错误'
  }
  return map[status] || status
}

function goToTask(id) {
  router.push(`/task/${id}`)
}

function goToNew() {
  router.push('/new')
}

function goToSettings() {
  router.push('/settings')
}

function openSettings(task) {
  currentTask.value = task
  editTaskName.value = task.name
  settings.skip_permissions = task.skip_permissions
  settings.teammate_mode = task.teammate_mode
  showSettings.value = true
}

async function saveSettings() {
  if (!currentTask.value) return
  savingSettings.value = true
  try {
    // 保存任务名称（如果有修改）
    if (editTaskName.value !== currentTask.value.name && editTaskName.value.trim()) {
      await api.patch(`/tasks/${currentTask.value.id}`, {
        name: editTaskName.value.trim()
      })
    }
    // 保存其他设置
    await api.patch(`/tasks/${currentTask.value.id}`, {
      skip_permissions: settings.skip_permissions,
      teammate_mode: settings.teammate_mode
    })
    showSettings.value = false
    await loadTasks()
  } catch (e) {
    error.value = e.response?.data?.detail || '保存设置失败'
  } finally {
    savingSettings.value = false
  }
}

async function restoreTask(id) {
  try {
    await api.post(`/tasks/${id}/restore`)
    await loadTasks()
  } catch (e) {
    error.value = e.response?.data?.detail || '恢复失败'
  }
}

async function stopTask(id) {
  if (!confirm('确定要终止此任务吗？可以稍后恢复。')) return

  try {
    await api.post(`/tasks/${id}/stop`)
    await loadTasks()
  } catch (e) {
    error.value = e.response?.data?.detail || '终止失败'
  }
}

async function deleteTask(id) {
  const task = tasks.value.find(t => t.id === id)
  const deleteFiles = confirm('是否同时删除工作目录？\n\n确定 = 删除任务和目录\n取消 = 只删除任务记录')

  if (!confirm('确定要删除此任务吗？此操作不可恢复。')) return

  try {
    await api.delete(`/tasks/${id}?delete_files=${deleteFiles}`)
    tasks.value = tasks.value.filter(t => t.id !== id)
  } catch (e) {
    error.value = '删除任务失败'
  }
}

function logout() {
  localStorage.removeItem('token')
  router.push('/login')
}
</script>

<style scoped>
.header-actions {
  display: flex;
  gap: 8px;
}

/* 筛选器样式 */
.filter-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.filter-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border: 1px solid var(--border-color, #333);
  border-radius: 16px;
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-size: 0.85rem;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}

.filter-btn:hover {
  background: var(--bg-card);
}

.filter-btn.active {
  background: var(--primary-color);
  border-color: var(--primary-color);
  color: #fff;
}

.filter-count {
  background: rgba(255, 255, 255, 0.2);
  padding: 2px 6px;
  border-radius: 10px;
  font-size: 0.75rem;
}

.filter-btn.active .filter-count {
  background: rgba(255, 255, 255, 0.3);
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-item {
  cursor: pointer;
  transition: transform 0.2s, opacity 0.2s;
}

.task-item:active {
  transform: scale(0.98);
}

/* 已停止任务灰显 */
.task-stopped {
  opacity: 0.6;
}

.task-stopped:hover {
  opacity: 0.8;
}

/* 设置弹窗 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  -webkit-backdrop-filter: blur(4px);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--bg-primary);
  border-radius: var(--border-radius);
  width: 90%;
  max-width: 400px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  opacity: 1;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid var(--bg-secondary);
}

.modal-header h3 {
  margin: 0;
  font-size: 1rem;
}

.modal-body {
  padding: 16px;
}

.modal-footer {
  padding: 16px;
  border-top: 1px solid var(--bg-secondary);
}

.form-group {
  margin-bottom: 16px;
}

.form-label {
  display: block;
  font-size: 0.85rem;
  font-weight: 500;
  margin-bottom: 6px;
  color: var(--text-secondary);
}

.text-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color, #333);
  border-radius: var(--border-radius);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 1rem;
  box-sizing: border-box;
}

.text-input:focus {
  outline: none;
  border-color: var(--primary-color);
}

.settings-hint {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-bottom: 16px;
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
</style>
