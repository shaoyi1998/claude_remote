<template>
  <div class="page">
    <div class="header">
      <button class="btn btn-sm btn-secondary" @click="goBack">返回</button>
      <h1>设置</h1>
      <div></div>
    </div>

    <div class="settings-list">
      <div class="settings-item">
        <div class="settings-label">
          <span>字体大小</span>
          <span class="settings-value">{{ fontSize }}px</span>
        </div>
        <input
          type="range"
          min="10"
          max="28"
          :value="fontSize"
          @input="updateFontSize($event.target.value)"
          class="slider"
        />
        <div class="font-preview" :style="{ fontSize: fontSize + 'px' }">
          预览文字：这是一段示例文本
        </div>
      </div>

      <div class="settings-item">
        <div class="settings-label">
          <span>终端字体大小</span>
          <span class="settings-value">{{ terminalFontSize }}px</span>
        </div>
        <input
          type="range"
          min="6"
          max="24"
          :value="terminalFontSize"
          @input="updateTerminalFontSize($event.target.value)"
          class="slider"
        />
        <div class="terminal-preview" :style="{ fontSize: terminalFontSize + 'px' }">
          <span class="term-green">$</span> claude --continue<br>
          <span class="term-cyan">Welcome to Claude Code...</span>
        </div>
      </div>

      <!-- 服务器配置 - 仅 APK 显示 -->
      <div v-if="isApp" class="settings-item server-config">
        <div class="settings-label">
          <span>服务器配置</span>
        </div>
        <p class="settings-hint">配置后端服务器地址（填写电脑的局域网 IP）</p>

        <div class="server-input-group">
          <label>服务器地址</label>
          <input
            v-model="serverHost"
            type="text"
            placeholder="如: 192.168.1.100"
            class="text-input"
          />
        </div>

        <div class="server-input-group">
          <label>服务器端口</label>
          <input
            v-model="serverPort"
            type="number"
            placeholder="默认: 8000"
            class="text-input"
          />
        </div>

        <div class="server-actions">
          <button class="btn btn-primary" @click="handleSaveServerConfig">保存配置</button>
          <button class="btn btn-secondary" @click="resetServerConfig">重置默认</button>
        </div>

        <div class="server-info">
          <p>当前配置: {{ serverHost || '自动检测' }}:{{ serverPort }}</p>
        </div>
      </div>

      <!-- 快捷键配置 -->
      <div class="settings-item shortcuts-config">
        <div class="settings-label">
          <span>快捷键配置</span>
          <button class="btn btn-sm btn-secondary" @click="resetAllShortcuts">重置默认</button>
        </div>

        <!-- 快捷命令 -->
        <div class="shortcut-section">
          <div class="section-header">
            <h4>快捷命令</h4>
            <button class="btn btn-sm btn-primary" @click="addCommand">+ 添加</button>
          </div>
          <p class="settings-hint">点击编辑，可自定义命令和显示名称。<span class="highlight">前5个启用的命令会在任务详情页显示。</span></p>
          <div class="shortcut-list">
            <div v-for="(item, index) in shortcuts.commands" :key="item.id" class="shortcut-item editable" :class="{ 'item-highlight': item.enabled && index < 5 }">
              <div class="sort-buttons">
                <button class="sort-btn" @click="moveItem('commands', item.id, 'up')" :disabled="index === 0" title="上移">↑</button>
                <button class="sort-btn" @click="moveItem('commands', item.id, 'down')" :disabled="index === shortcuts.commands.length - 1" title="下移">↓</button>
              </div>
              <label class="toggle-wrap">
                <input type="checkbox" v-model="item.enabled" @change="saveShortcutsData" />
                <span class="toggle-slider"></span>
              </label>
              <template v-if="editingId === item.id">
                <input v-model="editLabel" class="shortcut-input small" placeholder="显示名称" />
                <input v-model="editCommand" class="shortcut-input" placeholder="命令" />
                <button class="btn btn-sm btn-primary" @click="saveEdit('commands', item.id)">保存</button>
                <button class="btn btn-sm btn-secondary" @click="cancelEdit">取消</button>
              </template>
              <template v-else>
                <div class="item-info" @click="startEdit('commands', item.id, item.label, item.command)">
                  <span class="item-label">{{ item.label }}</span>
                  <span class="item-desc">{{ item.command }}</span>
                </div>
                <button class="btn btn-sm btn-danger" @click="deleteItem('commands', item.id)">删除</button>
              </template>
            </div>
          </div>
        </div>

        <!-- 自定义快捷键 -->
        <div class="shortcut-section">
          <div class="section-header">
            <h4>自定义快捷键</h4>
            <button class="btn btn-sm btn-primary" @click="addNewShortcut">+ 添加</button>
          </div>
          <p class="settings-hint">可设置 Ctrl/Shift/Alt 组合键或功能键。<span class="highlight">前5个启用的快捷键会在任务详情页显示。</span></p>
          <div class="shortcut-list">
            <div v-for="(item, index) in shortcuts.shortcuts" :key="item.id" class="shortcut-item editable" :class="{ 'item-highlight': item.enabled && index < 5 }">
              <div class="sort-buttons">
                <button class="sort-btn" @click="moveItem('shortcuts', item.id, 'up')" :disabled="index === 0" title="上移">↑</button>
                <button class="sort-btn" @click="moveItem('shortcuts', item.id, 'down')" :disabled="index === shortcuts.shortcuts.length - 1" title="下移">↓</button>
              </div>
              <label class="toggle-wrap">
                <input type="checkbox" v-model="item.enabled" @change="saveShortcutsData" />
                <span class="toggle-slider"></span>
              </label>
              <template v-if="editingId === item.id">
                <!-- 新的三列选择器 UI -->
                <div class="shortcut-editors">
                  <input v-model="editLabel" class="shortcut-input small" placeholder="名称" />
                  <div class="key-selectors">
                    <select v-model="editModifier1" class="shortcut-select">
                      <option v-for="mod in modifierOptions" :key="mod.value" :value="mod.value">{{ mod.label }}</option>
                    </select>
                    <select v-model="editModifier2" class="shortcut-select">
                      <option v-for="mod in modifierOptions" :key="mod.value" :value="mod.value">{{ mod.label }}</option>
                    </select>
                    <select v-model="editKey" class="shortcut-select">
                      <option v-for="key in keyOptions" :key="key.value" :value="key.value">{{ key.label }}</option>
                    </select>
                  </div>
                  <input v-model="editDesc" class="shortcut-input small" placeholder="说明" />
                </div>
                <div class="edit-preview">
                  <span class="preview-label">预览:</span>
                  <span class="preview-value">{{ editPreview }}</span>
                </div>
                <div class="edit-actions">
                  <button class="btn btn-sm btn-primary" @click="saveShortcutEdit(item.id)">保存</button>
                  <button class="btn btn-sm btn-secondary" @click="cancelEdit">取消</button>
                </div>
              </template>
              <template v-else>
                <div class="item-info" @click="startEditShortcut(item)">
                  <span class="item-label">{{ item.label }}</span>
                  <span class="item-desc">{{ getShortcutDisplay(item) }} {{ item.description ? '- ' + item.description : '' }}</span>
                </div>
                <button class="btn btn-sm btn-danger" @click="deleteItem('shortcuts', item.id)">删除</button>
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- 账号安全 -->
      <div class="settings-item">
        <div class="settings-label">
          <span>账号安全</span>
        </div>
        <p class="settings-hint">修改登录密码</p>

        <div class="password-form">
          <div class="password-input-group">
            <label>当前密码</label>
            <input
              v-model="oldPassword"
              type="password"
              placeholder="输入当前密码"
              class="text-input"
            />
          </div>
          <div class="password-input-group">
            <label>新密码</label>
            <input
              v-model="newPassword"
              type="password"
              placeholder="输入新密码"
              class="text-input"
            />
          </div>
          <div class="password-input-group">
            <label>确认新密码</label>
            <input
              v-model="confirmPassword"
              type="password"
              placeholder="再次输入新密码"
              class="text-input"
            />
          </div>
          <button class="btn btn-primary" @click="handleChangePassword" :disabled="passwordLoading">
            {{ passwordLoading ? '修改中...' : '修改密码' }}
          </button>
          <p v-if="passwordError" class="password-error">{{ passwordError }}</p>
          <p v-if="passwordSuccess" class="password-success">{{ passwordSuccess }}</p>
        </div>
      </div>

      <!-- 反向代理 -->
      <div class="settings-item">
        <div class="settings-label">
          <span>反向代理</span>
        </div>
        <p class="settings-hint">通过代理访问本地开发服务器（如 Vite、Webpack 等）</p>
        <button class="btn btn-primary" @click="goProxy">打开代理工具</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api, { saveServerConfig, getServerAddress, updateApiBaseURL } from '../api'
import {
  getShortcuts,
  saveShortcutsLocal,
  resetShortcuts,
  addShortcut,
  deleteShortcut,
  moveShortcut,
  availableModifiers,
  availableKeyOptions,
  getKeyDisplayName,
  keyToTmux,
  tmuxToKey,
  syncToServer,
  syncFromServer,
} from '../stores/shortcuts'
import { isCapacitorApp } from '../utils/platform'

const router = useRouter()
const fontSize = ref(16)
const terminalFontSize = ref(14)
const serverHost = ref('')
const serverPort = ref('8000')

// 平台检测
const isApp = isCapacitorApp()

// 密码修改
const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const passwordLoading = ref(false)
const passwordError = ref('')
const passwordSuccess = ref('')

// 快捷键配置
const shortcuts = ref({ commands: [], shortcuts: [] })
const editingId = ref(null)
const editLabel = ref('')
const editCommand = ref('')
const editModifier1 = ref('')
const editModifier2 = ref('')
const editKey = ref('c')
const editDesc = ref('')

// 修饰键选项（排除 '无' 用于第二列）
const modifierOptions = computed(() => availableModifiers)
const keyOptions = computed(() => availableKeyOptions)

// 编辑预览
const editPreview = computed(() => {
  const modifiers = [editModifier1.value, editModifier2.value].filter(m => m)
  const shortcut = { modifiers, key: editKey.value }
  return getKeyDisplayName(shortcut)
})

onMounted(async () => {
  // 加载保存的设置
  const savedFontSize = localStorage.getItem('fontSize')
  const savedTerminalFontSize = localStorage.getItem('terminalFontSize')

  if (savedFontSize) {
    fontSize.value = parseInt(savedFontSize)
    applyFontSize(fontSize.value)
  }
  if (savedTerminalFontSize) {
    terminalFontSize.value = parseInt(savedTerminalFontSize)
    applyTerminalFontSize(terminalFontSize.value)
  }

  // 加载服务器配置
  const serverAddr = getServerAddress()
  serverHost.value = serverAddr.host || ''
  serverPort.value = serverAddr.port || '8000'

  // 先从服务器同步快捷键配置（如果已登录）
  await syncFromServer()

  // 加载快捷键配置
  shortcuts.value = getShortcuts()
})

function updateFontSize(value) {
  fontSize.value = parseInt(value)
  localStorage.setItem('fontSize', value)
  applyFontSize(value)
}

function updateTerminalFontSize(value) {
  terminalFontSize.value = parseInt(value)
  localStorage.setItem('terminalFontSize', value)
  applyTerminalFontSize(value)
}

function applyFontSize(size) {
  document.documentElement.style.setProperty('--font-size-base', size + 'px')
}

function applyTerminalFontSize(size) {
  document.documentElement.style.setProperty('--font-size-terminal', size + 'px')
}

function goBack() {
  router.push('/')
}

function goProxy() {
  router.push('/proxy')
}

function handleSaveServerConfig() {
  saveServerConfig(serverHost.value, serverPort.value)
  updateApiBaseURL()
  alert('服务器配置已保存！')
}

function resetServerConfig() {
  serverHost.value = ''
  serverPort.value = '8000'
  localStorage.removeItem('serverHost')
  localStorage.removeItem('serverPort')
  updateApiBaseURL()
  alert('已重置为默认配置！')
}

// 快捷键相关方法
async function saveShortcutsData() {
  saveShortcutsLocal(shortcuts.value)
  // 异步同步到服务器
  syncToServer(shortcuts.value)
}

function startEdit(category, id, label, command) {
  editingId.value = id
  editLabel.value = label || ''
  editCommand.value = command || ''
}

function startEditShortcut(item) {
  editingId.value = item.id
  editLabel.value = item.label || ''
  editDesc.value = item.description || ''

  // 解析修饰键
  const modifiers = item.modifiers || []
  editModifier1.value = modifiers[0] || ''
  editModifier2.value = modifiers[1] || ''
  editKey.value = item.key || 'c'
}

function saveEdit(category, id) {
  const list = shortcuts.value[category]
  const index = list.findIndex(item => item.id === id)
  if (index !== -1) {
    if (category === 'commands') {
      list[index].label = editLabel.value || editCommand.value
      list[index].command = editCommand.value
    }
    saveShortcutsData()
  }
  cancelEdit()
}

function saveShortcutEdit(id) {
  const list = shortcuts.value.shortcuts
  const index = list.findIndex(item => item.id === id)
  if (index !== -1) {
    const modifiers = [editModifier1.value, editModifier2.value].filter(m => m)
    list[index].label = editLabel.value || editPreview.value
    list[index].modifiers = modifiers
    list[index].key = editKey.value
    list[index].description = editDesc.value
    saveShortcutsData()
  }
  cancelEdit()
}

function cancelEdit() {
  editingId.value = null
  editLabel.value = ''
  editCommand.value = ''
  editModifier1.value = ''
  editModifier2.value = ''
  editKey.value = 'c'
  editDesc.value = ''
}

async function addCommand() {
  const newItem = {
    label: '新命令',
    command: '/new-command',
    enabled: true
  }
  shortcuts.value = await addShortcut('commands', newItem)
}

async function addNewShortcut() {
  const newItem = {
    label: '新快捷键',
    modifiers: ['C'],
    key: 'c',
    description: '',
    enabled: true
  }
  shortcuts.value = await addShortcut('shortcuts', newItem)
}

async function deleteItem(category, id) {
  if (confirm('确定要删除此项吗？')) {
    shortcuts.value = await deleteShortcut(category, id)
  }
}

async function moveItem(category, id, direction) {
  shortcuts.value = await moveShortcut(category, id, direction)
}

async function resetAllShortcuts() {
  if (confirm('确定要重置所有快捷键为默认配置吗？')) {
    shortcuts.value = resetShortcuts()
    // 同步到服务器
    await syncToServer(shortcuts.value)
    alert('已重置为默认配置！')
  }
}

function getShortcutDisplay(item) {
  return getKeyDisplayName(item)
}

// 修改密码
async function handleChangePassword() {
  passwordError.value = ''
  passwordSuccess.value = ''

  // 验证
  if (!oldPassword.value) {
    passwordError.value = '请输入当前密码'
    return
  }
  if (!newPassword.value) {
    passwordError.value = '请输入新密码'
    return
  }
  if (newPassword.value.length < 6) {
    passwordError.value = '新密码至少需要6个字符'
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    passwordError.value = '两次输入的密码不一致'
    return
  }

  passwordLoading.value = true

  try {
    await api.post('/users/change-password', {
      old_password: oldPassword.value,
      new_password: newPassword.value
    })
    passwordSuccess.value = '密码修改成功！'
    oldPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
  } catch (e) {
    passwordError.value = e.response?.data?.detail || '密码修改失败'
  } finally {
    passwordLoading.value = false
  }
}
</script>

<style scoped>
.header {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 12px;
  align-items: center;
  margin-bottom: 16px;
}

.header h1 {
  text-align: center;
  font-size: 1rem;
}

.settings-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.settings-item {
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
  padding: 12px;
}

.settings-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.settings-label span:first-child {
  font-weight: 500;
}

.settings-value {
  color: var(--primary-color);
  font-weight: 600;
}

.slider {
  width: 100%;
  height: 8px;
  border-radius: 4px;
  background: var(--bg-card);
  outline: none;
  -webkit-appearance: none;
  appearance: none;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--primary-color);
  cursor: pointer;
}

.font-preview {
  margin-top: 8px;
  padding: 10px;
  background: var(--bg-card);
  border-radius: 8px;
}

.terminal-preview {
  margin-top: 8px;
  padding: 10px;
  background: #0d1117;
  border-radius: 8px;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  line-height: 1.5;
  color: #58a6ff;
  position: relative;
}

.terminal-preview::after {
  content: '▋';
  animation: cursor-blink 1s infinite;
  color: #fff;
}

@keyframes cursor-blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.term-green { color: #3fb950; }
.term-cyan { color: #58a6ff; }
.term-yellow { color: #d29922; }
.term-red { color: #f85149; }
.term-magenta { color: #bc8cff; }

.server-config {
  border: 1px solid var(--border-color, #333);
}

.settings-hint {
  font-size: 0.85em;
  color: #888;
  margin-bottom: 8px;
}

.server-input-group {
  margin-bottom: 8px;
}

.server-input-group label {
  display: block;
  font-size: 0.9em;
  margin-bottom: 4px;
  color: #aaa;
}

.text-input {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--border-color, #333);
  border-radius: 6px;
  background: var(--bg-card, #1a1a2e);
  color: var(--text-color, #fff);
  font-size: 14px;
  box-sizing: border-box;
}

.text-input:focus {
  outline: none;
  border-color: var(--primary-color);
}

.server-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.server-actions .btn {
  flex: 1;
  padding: 8px 12px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-primary {
  background: var(--primary-color);
  color: #fff;
}

.btn-primary:hover {
  opacity: 0.9;
}

.btn-secondary {
  background: var(--bg-card, #2a2a3e);
  color: #fff;
  border: 1px solid var(--border-color, #333);
}

.btn-secondary:hover {
  background: var(--bg-secondary, #3a3a4e);
}

.btn-danger {
  background: #dc3545;
  color: #fff;
  border: none;
  padding: 4px 8px;
  font-size: 0.75rem;
}

.server-info {
  margin-top: 8px;
  padding: 6px 10px;
  background: var(--bg-card, #1a1a2e);
  border-radius: 6px;
  font-size: 0.85em;
  color: #888;
}

.server-info p {
  margin: 0;
}

/* 快捷键配置样式 */
.shortcuts-config {
  border: 1px solid var(--border-color, #333);
}

.shortcut-section {
  margin-top: 12px;
  padding-top: 8px;
  border-top: 1px solid var(--border-color, #333);
}

.shortcut-section:first-of-type {
  margin-top: 8px;
  padding-top: 0;
  border-top: none;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.section-header h4 {
  margin: 0;
  font-size: 0.9em;
  color: var(--text-secondary);
}

.shortcut-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.shortcut-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: var(--bg-card, #1a1a2e);
  border-radius: 6px;
  font-size: 0.85em;
}

.shortcut-item.editable {
  flex-wrap: wrap;
}

.item-info {
  flex: 1;
  cursor: pointer;
  min-width: 0;
}

.item-label {
  font-weight: 500;
  display: block;
}

.item-desc {
  color: var(--text-secondary);
  font-size: 0.8em;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.shortcut-input {
  flex: 1;
  min-width: 80px;
  padding: 6px 8px;
  border: 1px solid var(--border-color, #333);
  border-radius: 4px;
  background: var(--bg-secondary, #2a2a3e);
  color: var(--text-color, #fff);
  font-size: 0.85em;
}

.shortcut-input.small {
  max-width: 100px;
}

.shortcut-input:focus {
  outline: none;
  border-color: var(--primary-color);
}

.shortcut-select {
  padding: 6px 8px;
  border: 1px solid var(--border-color, #333);
  border-radius: 4px;
  background: var(--bg-secondary, #2a2a3e);
  color: var(--text-color, #fff);
  font-size: 0.85em;
}

/* 快捷键编辑区域 */
.shortcut-editors {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  width: 100%;
  margin-bottom: 6px;
}

.key-selectors {
  display: flex;
  gap: 4px;
  flex: 1;
  min-width: 200px;
}

.key-selectors .shortcut-select {
  flex: 1;
  min-width: 60px;
}

.edit-preview {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 6px 10px;
  background: var(--bg-primary, #1a1a2e);
  border-radius: 4px;
  margin-bottom: 6px;
}

.preview-label {
  color: var(--text-secondary);
  font-size: 0.8em;
}

.preview-value {
  font-weight: 600;
  color: var(--primary-color);
}

.edit-actions {
  display: flex;
  gap: 6px;
  width: 100%;
}

/* 开关样式 */
.toggle-wrap {
  position: relative;
  width: 40px;
  height: 22px;
  flex-shrink: 0;
}

.toggle-wrap input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #555;
  transition: 0.3s;
  border-radius: 22px;
}

.toggle-slider:before {
  position: absolute;
  content: "";
  height: 16px;
  width: 16px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.3s;
  border-radius: 50%;
}

.toggle-wrap input:checked + .toggle-slider {
  background-color: var(--primary-color);
}

.toggle-wrap input:checked + .toggle-slider:before {
  transform: translateX(18px);
}

/* 排序按钮 */
.sort-buttons {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex-shrink: 0;
}

.sort-btn {
  width: 24px;
  height: 20px;
  padding: 0;
  border: 1px solid var(--border-color, #444);
  border-radius: 4px;
  background: var(--bg-secondary, #2a2a3e);
  color: var(--text-secondary);
  font-size: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}

.sort-btn:hover:not(:disabled) {
  background: var(--primary-color);
  color: #fff;
  border-color: var(--primary-color);
}

.sort-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

/* 高亮显示前5项 */
.item-highlight {
  border-left: 3px solid var(--primary-color);
}

.settings-hint .highlight {
  color: var(--primary-color);
  font-weight: 500;
}

/* 密码修改样式 */
.password-form {
  margin-top: 8px;
}

.password-input-group {
  margin-bottom: 10px;
}

.password-input-group label {
  display: block;
  font-size: 0.85em;
  margin-bottom: 4px;
  color: #aaa;
}

.password-error {
  color: #f85149;
  font-size: 0.85em;
  margin-top: 8px;
}

.password-success {
  color: #3fb950;
  font-size: 0.85em;
  margin-top: 8px;
}
</style>
