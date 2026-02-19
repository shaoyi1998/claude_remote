<template>
  <div class="page">
    <div v-if="error" class="error-message">{{ error }}</div>

    <div v-if="loading" class="loading">
      <span class="spinner"></span>
    </div>

    <template v-if="task">
      <!-- 紧凑头部 - 合并原有头部、状态栏和底部栏 -->
      <div class="compact-header">
        <!-- 返回按钮 -->
        <button class="header-btn" @click="goBack" title="返回">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
        </button>

        <!-- 任务名称 + 状态指示点 -->
        <h1 class="header-title">
          {{ task.name || '任务详情' }}
          <span :class="['status-dot', 'status-' + task.status]" :title="statusText(task.status)"></span>
        </h1>

        <!-- 工作目录 -->
        <span class="header-path" :title="task.work_dir">{{ task.work_dir }}</span>

        <!-- 文件管理按钮 -->
        <button class="header-btn" @click="openFileBrowser" title="文件管理">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
          </svg>
        </button>

        <!-- 锁定/解锁按钮 -->
        <button class="header-btn" :class="{ locked: inputLocked }" @click="toggleLock" :title="inputLocked ? '解锁' : '锁定'">
          <svg v-if="inputLocked" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
          </svg>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
            <path d="M7 11V7a5 5 0 0 1 9.9-1"/>
          </svg>
        </button>
      </div>

      <!-- 主内容区 - 终端 + 右侧快捷栏 -->
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

        <!-- 右侧快捷栏 - 竖屏和横屏都显示 -->
        <div class="shortcuts-panel right-sidebar">
          <!-- 折叠/展开按钮 -->
          <button class="sidebar-toggle" @click="toggleSidebar">
            {{ sidebarCollapsed ? '◀' : '✕' }}
          </button>

          <!-- 快捷按钮列表（可折叠） -->
          <div v-if="!sidebarCollapsed" class="sidebar-buttons">
            <button class="side-btn" @click="sendShortcut('escape')">Esc</button>
            <button class="side-btn" @click="sendShortcut('up')">↑</button>
            <button class="side-btn" @click="sendShortcut('down')">↓</button>
            <button class="side-btn" @click="sendShortcut('left')">←</button>
            <button class="side-btn" @click="sendShortcut('right')">→</button>
            <button class="side-btn"
              @touchstart.prevent="startBackspaceRepeat"
              @touchend="stopBackspaceRepeat"
              @mousedown="startBackspaceRepeat"
              @mouseup="stopBackspaceRepeat"
              @mouseleave="stopBackspaceRepeat">退格</button>
            <button class="side-btn" @click="sendText('/')">/</button>
            <button class="side-btn" @click="scrollToBottom">底部</button>

            <!-- 自定义命令（最多显示 N 个） -->
            <template v-for="(cmd, idx) in enabledCommands.slice(0, maxVisibleCommands)" :key="cmd.id">
              <button class="side-btn side-btn-cmd" @click="sendCommand(cmd.command)">
                {{ cmd.label }}
              </button>
            </template>

            <!-- 自定义快捷键（最多显示 N 个） -->
            <template v-for="(hk, idx) in enabledShortcutsList.slice(0, maxVisibleShortcuts)" :key="hk.id">
              <button class="side-btn side-btn-hk" @click="sendShortcutByItem(hk)">
                {{ hk.label }}
              </button>
            </template>

            <!-- 恢复按钮（仅停止状态显示） -->
            <button v-if="task.status === 'stopped'" class="side-btn side-btn-restore" @click="restoreTask">
              恢复
            </button>
          </div>

          <!-- Enter 按钮 - 始终显示在底部 -->
          <button class="side-btn side-btn-enter" @click="sendShortcut('enter')">↵</button>
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
import { getEnabledCommands, getEnabledShortcuts, keyToTmux } from '../stores/shortcuts'

const router = useRouter()
const route = useRoute()
const loading = ref(true)
const error = ref('')
const task = ref(null)
const terminalConnecting = ref(false)
const terminalContainer = ref(null)
const inputLocked = ref(false)

// 右侧快捷栏折叠状态
const sidebarCollapsed = ref(false)

// 最多显示的按钮数
const maxVisibleCommands = 5
const maxVisibleShortcuts = 5

// 获取启用的快捷键配置
const enabledCommands = computed(() => getEnabledCommands())
const enabledShortcutsList = computed(() => getEnabledShortcuts())

// 切换侧边栏折叠
function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

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

  // 移动端不自动聚焦，避免弹出输入法
  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
  if (!isMobile) {
    terminal.focus()
  }

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
  // 检查 task_id 是否有效
  const taskId = route.params.id
  if (!taskId || taskId === 'undefined') {
    console.error('Invalid task_id:', taskId)
    error.value = '任务ID无效，请返回重试'
    return
  }

  // 使用配置的服务器地址连接后端
  const token = localStorage.getItem('token')
  if (!token) {
    error.value = '未登录，请重新登录'
    router.push('/login')
    return
  }

  const { host, port } = getServerAddress()
  const wsUrl = `ws://${host}:${port}/ws/tasks/${taskId}?token=${token}`

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
  // 通过 WebSocket 直接发送文本，不自动聚焦
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'input', data: text }))
  }
}

function sendCommand(cmd) {
  // 通过 WebSocket 直接发送命令（带回车），不自动聚焦
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'input', data: cmd + '\r' }))
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

// 通过快捷键对象发送
async function sendShortcutByItem(shortcut) {
  try {
    const tmuxKey = keyToTmux(shortcut)
    await api.post(`/tasks/${route.params.id}/shortcut`, { key: tmuxKey, isTmuxFormat: true })
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
/* 页面容器 - 使用固定高度避免键盘弹出时布局错乱 */
.page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  height: 100dvh;
  max-height: 100vh;
  overflow: hidden;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

/* 紧凑头部 - 合并原有头部、状态栏和底部栏 */
.compact-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
  margin-bottom: 8px;
  flex-shrink: 0;
}

.header-btn {
  width: 32px;
  height: 32px;
  padding: 4px;
  border: none;
  border-radius: 6px;
  background: var(--bg-card);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  touch-action: manipulation;
}

.header-btn svg {
  width: 18px;
  height: 18px;
}

.header-btn:active {
  background: var(--primary-color);
  color: #fff;
}

.header-btn.locked {
  background: rgba(220, 53, 69, 0.2);
  color: #dc3545;
}

.header-title {
  font-size: 0.9rem;
  font-weight: 600;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
  margin: 0;
}

/* 状态指示点 - 红绿灯效果 */
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-dot.status-running {
  background: #28a745;
  box-shadow: 0 0 6px #28a745;
}

.status-dot.status-stopped {
  background: #dc3545;
  box-shadow: 0 0 6px #dc3545;
}

.status-dot.status-error {
  background: #ffc107;
  box-shadow: 0 0 6px #ffc107;
}

.header-path {
  font-size: 0.75rem;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
  min-width: 0;
}

/* 主内容区 - 终端 + 右侧快捷栏 */
.main-content {
  display: flex;
  flex-direction: row;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.terminal-wrapper {
  flex: 1;
  min-width: 0;
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
  pointer-events: auto;
  touch-action: pan-y;
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
  padding: 0;
  overflow: hidden;
  touch-action: pan-y;
  overscroll-behavior: contain;
}

/* xterm.js 样式调整 */
.terminal-container :deep(.xterm) {
  padding: 8px;
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

/* 右侧快捷栏 - 竖屏和横屏都显示 */
.right-sidebar {
  display: flex;
  flex-direction: column;
  width: 50px;
  flex-shrink: 0;
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
  padding: 4px;
  margin-left: 4px;
  gap: 4px;
  overflow-y: auto;
  overflow-x: hidden;
}

.sidebar-toggle {
  padding: 8px 4px;
  font-size: 0.8rem;
  background: var(--bg-card);
  border: none;
  border-radius: 4px;
  color: var(--text-secondary);
  cursor: pointer;
  touch-action: manipulation;
}

.sidebar-toggle:active {
  background: var(--primary-color);
  color: #fff;
}

.sidebar-buttons {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  overflow-y: auto;
}

.side-btn {
  padding: 10px 4px;
  font-size: 0.75rem;
  background: var(--bg-card);
  border: none;
  border-radius: 4px;
  color: var(--text-color);
  cursor: pointer;
  touch-action: manipulation;
  min-height: 36px;
}

.side-btn:active {
  background: var(--primary-color);
  color: #fff;
}

.side-btn-enter {
  margin-top: auto;
  background: var(--primary-color);
  color: #fff;
  font-weight: bold;
  min-height: 44px;
}

.side-btn-cmd {
  background: rgba(97, 175, 239, 0.2);
  color: #61afef;
}

.side-btn-cmd:active {
  background: #61afef;
  color: #fff;
}

.side-btn-hk {
  background: rgba(198, 120, 221, 0.2);
  color: #c678dd;
}

.side-btn-hk:active {
  background: #c678dd;
  color: #fff;
}

.side-btn-restore {
  background: rgba(152, 195, 121, 0.2);
  color: #98c379;
}

.side-btn-restore:active {
  background: #98c379;
  color: #fff;
}

/* 横屏布局优化 */
@media (orientation: landscape) {
  .right-sidebar {
    width: 60px;
    margin-left: 8px;
  }

  .side-btn {
    padding: 12px 4px;
    font-size: 0.8rem;
  }
}
</style>
