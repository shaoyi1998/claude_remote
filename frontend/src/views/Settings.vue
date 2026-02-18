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
          $ claude --continue<br>
          Welcome to Claude Code...
        </div>
      </div>

      <!-- 服务器配置 -->
      <div class="settings-item server-config">
        <div class="settings-label">
          <span>服务器配置</span>
        </div>
        <p class="settings-hint">配置后端服务器地址（APK 使用时需要填写电脑的局域网 IP）</p>

        <div class="server-input-group">
          <label>服务器地址</label>
          <input
            v-model="serverHost"
            type="text"
            placeholder="如: 192.168.1.100（留空则使用当前页面地址）"
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
          <p class="settings-hint">点击编辑，可自定义命令和显示名称</p>
          <div class="shortcut-list">
            <div v-for="item in shortcuts.commands" :key="item.id" class="shortcut-item editable">
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
          <p class="settings-hint">可设置 Ctrl/Alt 组合键或功能键</p>
          <div class="shortcut-list">
            <div v-for="item in shortcuts.shortcuts" :key="item.id" class="shortcut-item editable">
              <label class="toggle-wrap">
                <input type="checkbox" v-model="item.enabled" @change="saveShortcutsData" />
                <span class="toggle-slider"></span>
              </label>
              <template v-if="editingId === item.id">
                <input v-model="editLabel" class="shortcut-input small" placeholder="显示名称" />
                <select v-model="editKey" class="shortcut-select">
                  <option v-for="key in availableKeys" :key="key" :value="key">{{ key }}</option>
                </select>
                <input v-model="editDesc" class="shortcut-input small" placeholder="说明" />
                <button class="btn btn-sm btn-primary" @click="saveEdit('shortcuts', item.id)">保存</button>
                <button class="btn btn-sm btn-secondary" @click="cancelEdit">取消</button>
              </template>
              <template v-else>
                <div class="item-info" @click="startEditShortcut(item.id, item.label, item.key, item.description)">
                  <span class="item-label">{{ item.label }}</span>
                  <span class="item-desc">{{ item.key }} {{ item.description ? '- ' + item.description : '' }}</span>
                </div>
                <button class="btn btn-sm btn-danger" @click="deleteItem('shortcuts', item.id)">删除</button>
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { saveServerConfig, getServerAddress, updateApiBaseURL } from '../api'
import { getShortcuts, saveShortcuts as saveShortcutsToStorage, resetShortcuts, addShortcut, deleteShortcut, availableKeys } from '../stores/shortcuts'

const router = useRouter()
const fontSize = ref(16)
const terminalFontSize = ref(14)
const serverHost = ref('')
const serverPort = ref('8000')

// 快捷键配置
const shortcuts = ref({ commands: [], shortcuts: [] })
const editingId = ref(null)
const editLabel = ref('')
const editCommand = ref('')
const editKey = ref('')
const editDesc = ref('')

onMounted(() => {
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
function saveShortcutsData() {
  saveShortcutsToStorage(shortcuts.value)
}

function startEdit(category, id, label, command) {
  editingId.value = id
  editLabel.value = label || ''
  editCommand.value = command || ''
}

function startEditShortcut(id, label, key, desc) {
  editingId.value = id
  editLabel.value = label || ''
  editKey.value = key || 'C-c'
  editDesc.value = desc || ''
}

function saveEdit(category, id) {
  const list = shortcuts.value[category]
  const index = list.findIndex(item => item.id === id)
  if (index !== -1) {
    if (category === 'commands') {
      list[index].label = editLabel.value || editCommand.value
      list[index].command = editCommand.value
    } else {
      list[index].label = editLabel.value || editKey.value
      list[index].key = editKey.value
      list[index].description = editDesc.value
    }
    saveShortcutsData()
  }
  cancelEdit()
}

function cancelEdit() {
  editingId.value = null
  editLabel.value = ''
  editCommand.value = ''
  editKey.value = ''
  editDesc.value = ''
}

function addCommand() {
  const newItem = {
    label: '新命令',
    command: '/new-command',
    enabled: true
  }
  shortcuts.value = addShortcut('commands', newItem)
}

function addNewShortcut() {
  const newItem = {
    label: '新快捷键',
    key: 'C-c',
    description: '',
    enabled: true
  }
  shortcuts.value = addShortcut('shortcuts', newItem)
}

function deleteItem(category, id) {
  if (confirm('确定要删除此项吗？')) {
    shortcuts.value = deleteShortcut(category, id)
  }
}

function resetAllShortcuts() {
  if (confirm('确定要重置所有快捷键为默认配置吗？')) {
    shortcuts.value = resetShortcuts()
    alert('已重置为默认配置！')
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
  gap: 16px;
}

.settings-item {
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
  padding: 16px;
}

.settings-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
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
  margin-top: 12px;
  padding: 12px;
  background: var(--bg-card);
  border-radius: 8px;
}

.terminal-preview {
  margin-top: 12px;
  padding: 12px;
  background: #0d1117;
  border-radius: 8px;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  line-height: 1.4;
}

.server-config {
  border: 1px solid var(--border-color, #333);
}

.settings-hint {
  font-size: 0.85em;
  color: #888;
  margin-bottom: 12px;
}

.server-input-group {
  margin-bottom: 12px;
}

.server-input-group label {
  display: block;
  font-size: 0.9em;
  margin-bottom: 4px;
  color: #aaa;
}

.text-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color, #333);
  border-radius: 8px;
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
  gap: 12px;
  margin-top: 16px;
}

.server-actions .btn {
  flex: 1;
  padding: 10px 16px;
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
  margin-top: 12px;
  padding: 8px 12px;
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
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--border-color, #333);
}

.shortcut-section:first-of-type {
  margin-top: 12px;
  padding-top: 0;
  border-top: none;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.section-header h4 {
  margin: 0;
  font-size: 0.9em;
  color: var(--text-secondary);
}

.shortcut-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.shortcut-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
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
</style>
