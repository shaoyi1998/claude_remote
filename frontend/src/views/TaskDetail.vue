<template>
  <div class="page">
    <div class="header">
      <button class="btn btn-sm btn-secondary" @click="goBack">返回</button>
      <h1>{{ task?.name || '任务详情' }}</h1>
      <button class="btn btn-sm" :class="inputLocked ? 'btn-danger' : 'btn-secondary'" @click="toggleLock">
        {{ inputLocked ? '解锁' : '锁定' }}
      </button>
    </div>

    <div v-if="error" class="error-message">{{ error }}</div>

    <div v-if="loading" class="loading">
      <span class="spinner"></span>
    </div>

    <template v-if="task">
      <!-- 精简状态栏 -->
      <div class="status-bar">
        <span :class="['status-badge', 'status-' + task.status]">
          {{ statusText(task.status) }}
        </span>
        <span class="status-info">{{ task.work_dir }}</span>
      </div>

      <!-- 主内容区 - 横屏时左右布局 -->
      <div class="main-content">
        <!-- 终端区域 - 使用 xterm.js -->
        <div class="terminal-wrapper">
          <div ref="terminalContainer" class="terminal-container" @click="handleTerminalClick"></div>
          <!-- 终端连接加载动画 -->
          <div v-if="terminalConnecting" class="terminal-loading-overlay">
            <div class="terminal-loading-spinner"></div>
            <span class="terminal-loading-text">连接终端中...</span>
          </div>
          <!-- 锁定提示遮罩 - 拦截触摸事件，手动处理滚动 -->
          <div v-if="inputLocked" class="terminal-overlay"
            @touchstart.passive="onOverlayTouchStart"
            @touchmove.passive="onOverlayTouchMove">
            <svg class="lock-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0110 0v4"/>
            </svg>
          </div>
        </div>

        <!-- 快捷键面板 -->
        <div class="shortcuts-panel">
          <!-- 基础方向键 -->
          <div class="shortcuts-row">
            <button class="btn btn-sm btn-secondary" @click="sendShortcut('escape')">Esc</button>
            <button class="btn btn-sm btn-secondary" @click="sendShortcut('up')">↑</button>
            <button class="btn btn-sm btn-secondary" @click="sendShortcut('enter')">Enter</button>
            <button class="btn btn-sm btn-secondary" @click="sendText('/')">/</button>
          </div>
          <div class="shortcuts-row">
            <button class="btn btn-sm btn-secondary" @click="sendShortcut('left')">←</button>
            <button class="btn btn-sm btn-secondary" @click="sendShortcut('down')">↓</button>
            <button class="btn btn-sm btn-secondary" @click="sendShortcut('right')">→</button>
            <button class="btn btn-sm btn-secondary"
              @touchstart.prevent="startBackspaceRepeat"
              @touchend="stopBackspaceRepeat"
              @mousedown="startBackspaceRepeat"
              @mouseup="stopBackspaceRepeat"
              @mouseleave="stopBackspaceRepeat">退格</button>
          </div>
          <div class="shortcuts-row">
            <button class="btn btn-sm btn-secondary" @click="scrollToBottom">底部</button>
            <button class="btn btn-sm btn-secondary" @click="sendShortcut('shift_up')">Shift+↑</button>
            <button class="btn btn-sm btn-secondary" @click="sendShortcut('shift_down')">Shift+↓</button>
            <button class="btn btn-sm btn-secondary" @click="sendShortcut('shift_tab')">Shift+Tab</button>
          </div>

          <!-- 自定义命令按钮 - 可展开 -->
          <div class="shortcuts-section" v-if="enabledCommands.length > 0">
            <div class="section-header" @click="toggleCommandsPanel">
              <span>快捷命令</span>
              <span class="toggle-icon">{{ showCommandsPanel ? '▼' : '▶' }}</span>
            </div>
            <div v-if="showCommandsPanel" class="shortcuts-grid commands-grid">
              <button v-for="cmd in enabledCommands" :key="cmd.id"
                class="btn btn-sm btn-cmd"
                @click="sendCommand(cmd.command)">
                {{ cmd.label }}
              </button>
            </div>
          </div>

          <!-- 自定义快捷键 - 可展开 -->
          <div class="shortcuts-section" v-if="enabledShortcutsList.length > 0">
            <div class="section-header" @click="toggleShortcutsPanel">
              <span>快捷键</span>
              <span class="toggle-icon">{{ showShortcutsPanel ? '▼' : '▶' }}</span>
            </div>
            <div v-if="showShortcutsPanel" class="shortcuts-grid hk-grid">
              <button v-for="hk in enabledShortcutsList" :key="hk.id"
                class="btn btn-sm btn-hk"
                :title="hk.description"
                @click="sendShortcutByKey(hk.key)">
                {{ hk.label }}
              </button>
            </div>
          </div>

          <!-- 恢复按钮 -->
          <div v-if="task.status === 'stopped'" class="restore-bar">
            <button class="btn btn-primary btn-block" @click="restoreTask">恢复会话</button>
          </div>

          <!-- 文件浏览器入口 -->
          <div class="file-browser-entry">
            <button class="btn btn-sm btn-secondary btn-block" @click="openFileBrowser">
              浏览文件
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Terminal } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'
import 'xterm/css/xterm.css'
import api, { getServerAddress } from '../api'
import { getEnabledCommands, getEnabledShortcuts } from '../stores/shortcuts'

const router = useRouter()
const route = useRoute()
const loading = ref(true)
const error = ref('')
const task = ref(null)
const terminalConnecting = ref(false)
const terminalContainer = ref(null)
const inputLocked = ref(false)

// 面板展开状态
const showCommandsPanel = ref(true)
const showShortcutsPanel = ref(false)

// 获取启用的快捷键配置
const enabledCommands = computed(() => getEnabledCommands())
const enabledShortcutsList = computed(() => getEnabledShortcuts())

let terminal = null
let fitAddon = null
let ws = null
let backspaceInterval = null
let backspaceSpeed = 200 // 初始间隔(ms)

onMounted(async () => {
  await loadTask()
  if (task.value?.status === 'running') {
    await nextTick()
    initTerminal()
  }
})

onUnmounted(() => {
  if (ws) {
    ws.close()
  }
  if (terminal) {
    terminal.dispose()
  }
  if (backspaceInterval) {
    clearInterval(backspaceInterval)
  }
  window.removeEventListener('resize', handleResize)
})

async function loadTask() {
  try {
    const res = await api.get(`/tasks/${route.params.id}`)
    task.value = res.data
  } catch (e) {
    error.value = '加载任务失败'
  } finally {
    loading.value = false
  }
}

function initTerminal() {
  if (terminal) return
  if (!terminalContainer.value) {
    console.error('Terminal container not ready')
    return
  }

  // 读取用户设置的终端字体大小
  const savedFontSize = localStorage.getItem('terminalFontSize')
  const fontSize = savedFontSize ? parseInt(savedFontSize) : 14

  // 初始化终端
  terminal = new Terminal({
    cursorBlink: false,
    cursorStyle: 'block',
    fontSize: fontSize,
    fontFamily: 'Consolas, "Courier New", monospace',
    lineHeight: 1.2,  // 明确设置行高，确保光标定位准确
    letterSpacing: 0,
    theme: {
      background: '#1e1e1e',
      foreground: '#d4d4d4',
      cursor: '#ffffff',
      cursorAccent: '#000000',
      selectionBackground: '#264f78',
      // ANSI 16色 - VS Code One Dark Pro 风格
      black: '#000000',
      red: '#e06c75',
      green: '#98c379',
      yellow: '#e5c07b',
      blue: '#61afef',
      magenta: '#c678dd',
      cyan: '#56b6c2',
      white: '#abb2bf',
      // 高亮16色
      brightBlack: '#5c6370',
      brightRed: '#e06c75',
      brightGreen: '#98c379',
      brightYellow: '#e5c07b',
      brightBlue: '#61afef',
      brightMagenta: '#c678dd',
      brightCyan: '#56b6c2',
      brightWhite: '#ffffff'
    },
    allowTransparency: false,
    scrollback: 5000,
    convertEol: true
  })

  fitAddon = new FitAddon()
  terminal.loadAddon(fitAddon)
  terminal.open(terminalContainer.value)

  // 延迟调用 fit，确保元素有尺寸
  // 使用双重 requestAnimationFrame 确保 DOM 完全渲染
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      try {
        if (fitAddon && terminal) {
          fitAddon.fit()
          // 如果 WebSocket 已连接，立即同步尺寸
          if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
              type: 'resize',
              cols: terminal.cols,
              rows: terminal.rows
            }))
          }
        }
      } catch (e) {
        console.warn('Failed to fit terminal:', e)
      }
    })
  })

  terminal.focus()

  window.addEventListener('resize', handleResize)

  // 监听用户输入
  terminal.onData((data) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'input', data }))
    }
  })

  // 连接 WebSocket
  connectWebSocket()
}

function connectWebSocket() {
  // 使用配置的服务器地址连接后端
  const token = localStorage.getItem('token')
  const { host, port } = getServerAddress()
  const wsUrl = `ws://${host}:${port}/ws/tasks/${route.params.id}?token=${token}`

  console.log('Connecting to WebSocket:', wsUrl)
  terminalConnecting.value = true

  try {
    ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('WebSocket connected')
      terminalConnecting.value = false
      // 连接成功后立即同步终端尺寸到后端
      if (fitAddon && terminal) {
        try {
          fitAddon.fit()
          const cols = terminal.cols
          const rows = terminal.rows
          ws.send(JSON.stringify({
            type: 'resize',
            cols: cols,
            rows: rows
          }))
          console.log('Terminal size synced:', cols, 'x', rows)
        } catch (e) {
          console.warn('Failed to sync terminal size:', e)
        }
      }
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        console.log('WebSocket message:', msg.type, msg.append ? 'append' : 'full', msg.data?.length)
        if (msg.type === 'output' && terminal) {
          if (msg.append) {
            terminal.write(msg.data)
          } else {
            // 使用 clear() 代替 reset() 避免 dimensions 错误
            terminal.clear()
            terminal.write(msg.data)
          }
        }
      } catch (e) {
        console.error('WebSocket message error:', e)
      }
    }

    ws.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason)
      terminalConnecting.value = false
      // 尝试重连
      setTimeout(() => {
        if (task.value?.status === 'running') {
          connectWebSocket()
        }
      }, 2000)
    }

    ws.onerror = (err) => {
      console.error('WebSocket error:', err)
      terminalConnecting.value = false
    }
  } catch (e) {
    console.error('Failed to create WebSocket:', e)
  }
}

function handleResize() {
  try {
    if (fitAddon && terminal) {
      fitAddon.fit()
      // 同步尺寸到后端 tmux
      const cols = terminal.cols
      const rows = terminal.rows
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          type: 'resize',
          cols: cols,
          rows: rows
        }))
      }
    }
  } catch (e) {
    console.warn('Failed to fit terminal on resize:', e)
  }
}

function focusTerminal() {
  if (terminal) {
    terminal.focus()
  }
}

function handleTerminalClick() {
  if (!inputLocked.value) {
    focusTerminal()
  }
}

function toggleLock() {
  inputLocked.value = !inputLocked.value
  if (terminal) {
    if (inputLocked.value) {
      terminal.options.readOnly = true
      terminal.blur()
    } else {
      terminal.options.readOnly = false
      terminal.focus()
    }
  }
}

// 触摸滚动相关变量
let lastTouchY = 0

// 遮罩层触摸开始
function onOverlayTouchStart(e) {
  lastTouchY = e.touches[0].clientY
}

// 遮罩层触摸移动 - 手动滚动终端
function onOverlayTouchMove(e) {
  const viewport = terminalContainer.value?.querySelector('.xterm-viewport')
  if (viewport) {
    const currentY = e.touches[0].clientY
    const deltaY = lastTouchY - currentY
    viewport.scrollTop += deltaY
    lastTouchY = currentY
  }
}

function scrollToBottom() {
  if (terminal) {
    terminal.scrollToBottom()
    if (!inputLocked.value) terminal.focus()
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

async function sendShortcut(key) {
  try {
    await api.post(`/tasks/${route.params.id}/shortcut`, { key })
  } catch (e) {
    error.value = e.response?.data?.detail || '发送快捷键失败'
  }
}

// 长按退格加速
function startBackspaceRepeat() {
  // 立即发送一次
  sendShortcut('backspace')

  // 初始速度
  backspaceSpeed = 200
  let repeatCount = 0

  // 开始重复
  backspaceInterval = setInterval(() => {
    sendShortcut('backspace')
    repeatCount++

    // 每5次加速一次，最快50ms
    if (repeatCount % 5 === 0 && backspaceSpeed > 50) {
      backspaceSpeed -= 30
      clearInterval(backspaceInterval)
      backspaceInterval = setInterval(() => {
        sendShortcut('backspace')
        repeatCount++
        if (repeatCount % 5 === 0 && backspaceSpeed > 50) {
          backspaceSpeed -= 30
          clearInterval(backspaceInterval)
          backspaceInterval = setInterval(() => {
            sendShortcut('backspace')
          }, backspaceSpeed)
        }
      }, backspaceSpeed)
    }
  }, backspaceSpeed)
}

function stopBackspaceRepeat() {
  if (backspaceInterval) {
    clearInterval(backspaceInterval)
    backspaceInterval = null
  }
}

function sendText(text) {
  // 通过 WebSocket 直接发送文本
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'input', data: text }))
    if (!inputLocked.value) terminal.focus()
  }
}

function sendCommand(cmd) {
  // 通过 WebSocket 直接发送命令（带回车）
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'input', data: cmd + '\r' }))
    if (!inputLocked.value) terminal.focus()
  }
}

async function restoreTask() {
  try {
    await api.post(`/tasks/${route.params.id}/restore`)
    await loadTask()
    if (!terminal && task.value?.status === 'running') {
      await nextTick()
      initTerminal()
    }
  } catch (e) {
    error.value = e.response?.data?.detail || '恢复失败'
  }
}

function goBack() {
  router.push('/')
}

// 切换面板
function toggleCommandsPanel() {
  showCommandsPanel.value = !showCommandsPanel.value
}

function toggleShortcutsPanel() {
  showShortcutsPanel.value = !showShortcutsPanel.value
}

// 通过按键值发送快捷键
async function sendShortcutByKey(key) {
  try {
    await api.post(`/tasks/${route.params.id}/shortcut`, { key })
  } catch (e) {
    error.value = e.response?.data?.detail || '发送快捷键失败'
  }
}

// 打开文件浏览器
function openFileBrowser() {
  if (task.value?.work_dir) {
    router.push(`/files/${route.params.id}?path=${encodeURIComponent(task.value.work_dir)}`)
  } else {
    router.push(`/files/${route.params.id}`)
  }
}
</script>

<style scoped>
/* 页面容器 - 使用 dvh 自动响应键盘 */
.page {
  display: flex;
  flex-direction: column;
  height: 100dvh;
  overflow: hidden;
}

.header {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 12px;
  align-items: center;
  margin-bottom: 8px;
  flex-shrink: 0;
}

.header h1 {
  text-align: center;
  font-size: 1rem;
}

/* 精简状态栏 */
.status-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
  margin-bottom: 8px;
  flex-shrink: 0;
}

.status-info {
  font-size: 0.8rem;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

/* 主内容区 - 默认竖屏布局 */
.main-content {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;  /* 关键：允许 flex 子项收缩 */
  overflow: hidden;
}

.terminal-wrapper {
  flex: 1;
  min-height: 150px;
  max-height: calc(100dvh - 280px);  /* 为快捷键面板预留空间 */
  display: flex;
  flex-direction: column;
  position: relative;
}

/* 遮罩样式 - 拦截触摸事件，手动处理滚动 */
.terminal-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--border-radius);
  z-index: 10;
  pointer-events: auto;      /* 拦截触摸事件，防止弹出输入法 */
  touch-action: pan-y;       /* 允许垂直滑动 */
  overscroll-behavior: contain;
}

.lock-icon {
  width: 32px;
  height: 32px;
  color: rgba(255, 255, 255, 0.5);
}

/* 终端连接加载动画 */
.terminal-loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(30, 30, 30, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  border-radius: var(--border-radius);
  z-index: 20;
}

.terminal-loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #333;
  border-top-color: var(--primary-color, #61afef);
  border-radius: 50%;
  animation: terminal-spin 0.8s linear infinite;
}

@keyframes terminal-spin {
  to {
    transform: rotate(360deg);
  }
}

.terminal-loading-text {
  color: var(--text-secondary, #abb2bf);
  font-size: 0.85rem;
}

/* 终端容器 - 使用 xterm.js */
.terminal-container {
  flex: 1;
  min-height: 100px;
  background: #1e1e1e;
  border-radius: var(--border-radius);
  padding: 0;  /* 移除 padding，让 xterm 自己管理 */
  margin-bottom: 8px;
  overflow: hidden;
  touch-action: pan-y;
  overscroll-behavior: contain;
}

/* xterm.js 样式调整 */
.terminal-container :deep(.xterm) {
  padding: 8px;  /* 在 xterm 内部添加 padding */
  box-sizing: border-box;
}

.terminal-container :deep(.xterm-screen) {
  padding: 0;
}

/* 隐藏 xterm.js 光标，使用终端内容自带的光标 */
.terminal-container :deep(.xterm-cursor) {
  position: absolute !important;
  left: -9999px !important;
  visibility: hidden !important;
}

/* 隐藏只包含光标的空行 */
.terminal-container :deep(.xterm-rows > div:has(.xterm-cursor:only-child)) {
  display: none !important;
}

.terminal-container :deep(.xterm-viewport) {
  overflow-y: auto !important;
  -webkit-overflow-scrolling: touch;
  transform: translateZ(0);
  will-change: scroll-position;
  overscroll-behavior: contain;
}

/* 滚动条样式 - 更宽更易触摸 */
.terminal-container :deep(.xterm-viewport::-webkit-scrollbar) {
  width: 12px;
}

.terminal-container :deep(.xterm-viewport::-webkit-scrollbar-track) {
  background: #2d2d2d;
  border-radius: 6px;
}

.terminal-container :deep(.xterm-viewport::-webkit-scrollbar-thumb) {
  background: #555;
  border-radius: 6px;
  border: 2px solid #2d2d2d;
}

.terminal-container :deep(.xterm-viewport::-webkit-scrollbar-thumb:hover) {
  background: #777;
}

/* Firefox 滚动条 */
.terminal-container :deep(.xterm-viewport) {
  scrollbar-width: auto;
  scrollbar-color: #555 #2d2d2d;
}

/* 快捷键面板 - 竖屏 */
.shortcuts-panel {
  flex-shrink: 0;  /* 不允许收缩 */
  min-height: fit-content;
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
  padding: 8px;
  margin-bottom: 8px;
}

.shortcuts-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
  margin-bottom: 6px;
}

.shortcuts-row:last-child {
  margin-bottom: 0;
}

.shortcuts-row .btn {
  padding: 12px 8px;
  font-size: 0.85rem;
}

.restore-bar {
  margin-top: 8px;
}

/* 快捷键分区 */
.shortcuts-section {
  margin-top: 8px;
  border-top: 1px solid var(--border-color, #333);
  padding-top: 8px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 4px;
  cursor: pointer;
  font-size: 0.8rem;
  color: var(--text-secondary);
  user-select: none;
}

.section-header:hover {
  background: var(--bg-card);
  border-radius: 4px;
}

.toggle-icon {
  font-size: 0.7rem;
}

/* 快捷键网格 */
.shortcuts-grid {
  display: grid;
  gap: 4px;
  margin-top: 6px;
}

.commands-grid {
  grid-template-columns: repeat(3, 1fr);
}

.hk-grid {
  grid-template-columns: repeat(4, 1fr);
}

.btn-cmd, .btn-hk {
  padding: 8px 4px;
  font-size: 0.7rem;
  background: var(--bg-card);
  color: var(--text-secondary);
}

.btn-cmd:hover, .btn-hk:hover {
  background: var(--primary-color);
  color: #fff;
}

/* 文件浏览器入口 */
.file-browser-entry {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--border-color, #333);
}

/* 横屏布局 */
@media (orientation: landscape) {
  .main-content {
    flex-direction: row;
    gap: 8px;
    flex: 1;
    min-height: 0;
  }

  .terminal-wrapper {
    flex: 1;
    min-width: 0;
    max-height: none;  /* 横屏时移除最大高度限制 */
  }

  .terminal-container {
    height: calc(100dvh - 100px);
    max-height: none;
    margin-bottom: 0;
  }

  .shortcuts-panel {
    width: 200px;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    justify-content: center;
    margin-bottom: 0;
  }

  .shortcuts-row .btn {
    padding: 10px 6px;
    font-size: 0.8rem;
  }
}
</style>
