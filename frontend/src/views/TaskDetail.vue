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

        <!-- 横屏时的快捷键面板 -->
        <div class="shortcuts-panel desktop-panel">
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
                @click="sendShortcutByItem(hk)">
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

      <!-- 底部固定按钮栏 - 竖屏时显示 -->
      <div class="bottom-bar">
        <button class="bar-btn" @click="showInputPanel = true">快捷输入</button>
        <button class="bar-btn" @click="showShortcutPanel = true">快捷键</button>
        <button class="bar-btn" @click="showMorePanel = true">更多</button>
      </div>
    </template>

    <!-- 快捷输入浮动面板 -->
    <Transition name="slide-up">
      <div v-if="showInputPanel" class="floating-panel" @click.self="closeAllPanels">
        <!-- 终端预览条 -->
        <div class="terminal-preview">
          <div class="preview-content">{{ terminalPreviewLines || '$ ' }}</div>
        </div>
        <div class="panel-content glass-panel">
          <div class="panel-header">
            <span class="panel-title">快捷输入</span>
            <button class="close-btn" @click="showInputPanel = false">×</button>
          </div>
          <div class="panel-grid">
            <button v-for="btn in inputButtons" :key="btn.action"
              class="grid-btn"
              @click="handleInput(btn)"
              @touchstart.prevent="btn.action === 'backspace' ? startBackspaceRepeat() : null"
              @touchend="btn.action === 'backspace' ? stopBackspaceRepeat() : null">
              {{ btn.label }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 快捷键浮动面板 -->
    <Transition name="slide-up">
      <div v-if="showShortcutPanel" class="floating-panel" @click.self="closeAllPanels">
        <!-- 终端预览条 -->
        <div class="terminal-preview">
          <div class="preview-content">{{ terminalPreviewLines || '$ ' }}</div>
        </div>
        <div class="panel-content glass-panel">
          <div class="panel-header">
            <span class="panel-title">快捷键</span>
            <button class="close-btn" @click="showShortcutPanel = false">×</button>
          </div>
          <!-- 快捷命令 -->
          <div v-if="enabledCommands.length > 0" class="panel-section">
            <div class="section-title">命令</div>
            <div class="panel-grid cmd-grid">
              <button v-for="cmd in enabledCommands" :key="cmd.id"
                class="grid-btn"
                @click="sendCommand(cmd.command); showShortcutPanel = false; scrollToBottom()">
                {{ cmd.label }}
              </button>
            </div>
          </div>
          <!-- 自定义快捷键 -->
          <div v-if="enabledShortcutsList.length > 0" class="panel-section">
            <div class="section-title">快捷键</div>
            <div class="panel-grid hk-grid">
              <button v-for="hk in enabledShortcutsList" :key="hk.id"
                class="grid-btn"
                @click="sendShortcutByItem(hk); showShortcutPanel = false; scrollToBottom()">
                {{ hk.label }}
              </button>
            </div>
          </div>
          <div v-if="enabledCommands.length === 0 && enabledShortcutsList.length === 0" class="empty-tip">
            暂无自定义快捷键，请在设置中添加
          </div>
        </div>
      </div>
    </Transition>

    <!-- 更多浮动面板 -->
    <Transition name="slide-up">
      <div v-if="showMorePanel" class="floating-panel" @click.self="closeAllPanels">
        <!-- 终端预览条 -->
        <div class="terminal-preview">
          <div class="preview-content">{{ terminalPreviewLines || '$ ' }}</div>
        </div>
        <div class="panel-content glass-panel">
          <div class="panel-header">
            <span class="panel-title">更多</span>
            <button class="close-btn" @click="showMorePanel = false">×</button>
          </div>
          <div class="more-list">
            <button class="more-item" @click="toggleLockFromPanel">
              <span class="more-icon">{{ inputLocked ? '🔓' : '🔒' }}</span>
              <span>{{ inputLocked ? '解锁终端' : '锁定终端' }}</span>
            </button>
            <button class="more-item" @click="openFileBrowserFromPanel">
              <span class="more-icon">📁</span>
              <span>浏览文件</span>
            </button>
            <button v-if="task?.status === 'stopped'" class="more-item" @click="restoreFromPanel">
              <span class="more-icon">▶️</span>
              <span>恢复会话</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Terminal } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'
import 'xterm/css/xterm.css'
import api, { getServerAddress } from '../api'
import { getEnabledCommands, getEnabledShortcuts, keyToTmux, getKeyDisplayName } from '../stores/shortcuts'

const router = useRouter()
const route = useRoute()
const loading = ref(true)
const error = ref('')
const task = ref(null)
const terminalConnecting = ref(false)
const terminalContainer = ref(null)
const inputLocked = ref(false)

// 面板展开状态 (横屏用)
const showCommandsPanel = ref(true)
const showShortcutsPanel = ref(false)

// 浮动面板状态 (竖屏用)
const showInputPanel = ref(false)
const showShortcutPanel = ref(false)
const showMorePanel = ref(false)

// 基础输入按钮配置
const inputButtons = [
  { label: 'Esc', action: 'escape' },
  { label: '↑', action: 'up' },
  { label: '↓', action: 'down' },
  { label: '←', action: 'left' },
  { label: '→', action: 'right' },
  { label: 'Enter', action: 'enter' },
  { label: '退格', action: 'backspace' },
  { label: '/', action: 'text', value: '/' },
  { label: '底部', action: 'scrollBottom' },
  { label: 'S↑', action: 'shift_up' },
  { label: 'S↓', action: 'shift_down' },
  { label: 'S⇥', action: 'shift_tab' },
]

// 获取启用的快捷键配置
const enabledCommands = computed(() => getEnabledCommands())
const enabledShortcutsList = computed(() => getEnabledShortcuts())

// 终端预览内容
const terminalPreviewLines = ref('')

// 监听面板打开状态，自动滚动到底部
watch([showInputPanel, showShortcutPanel, showMorePanel], (vals) => {
  if (vals.some(v => v)) {
    scrollToBottom()
  }
})

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
          // 更新终端预览内容
          updateTerminalPreview()
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

// 更新终端预览内容（获取可见区域最后3行）
function updateTerminalPreview() {
  if (!terminal) return
  try {
    const buffer = terminal.buffer.active
    const lines = []

    // 获取 buffer 长度和可见行数
    const bufferLength = buffer.length
    const visibleRows = terminal.rows

    // 可见区域的起始行（当在底部时）
    // 如果 bufferLength < visibleRows，说明内容不够一屏
    const visibleStart = Math.max(0, bufferLength - visibleRows)
    const visibleEnd = bufferLength

    // 从可见区域底部向上获取非空行
    for (let i = visibleEnd - 1; i >= visibleStart && lines.length < 3; i--) {
      const line = buffer.getLine(i)
      if (line) {
        const text = line.translateToString(true)
        if (text.trim()) {
          lines.unshift(text)
        }
      }
    }

    terminalPreviewLines.value = lines.join('\n') || '$ '
  } catch (e) {
    terminalPreviewLines.value = '$ '
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

// 通过按键值发送快捷键（旧版兼容）
async function sendShortcutByKey(key) {
  try {
    await api.post(`/tasks/${route.params.id}/shortcut`, { key })
  } catch (e) {
    error.value = e.response?.data?.detail || '发送快捷键失败'
  }
}

// 通过快捷键对象发送（新版）
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

// 处理基础输入按钮
function handleInput(btn) {
  if (btn.action === 'scrollBottom') {
    scrollToBottom()
  } else if (btn.action === 'text') {
    sendText(btn.value)
  } else {
    sendShortcut(btn.action)
  }
  // 操作后自动滚动到底部
  scrollToBottom()
}

// 关闭所有浮动面板
function closeAllPanels() {
  showInputPanel.value = false
  showShortcutPanel.value = false
  showMorePanel.value = false
}

// 从更多面板锁定/解锁
function toggleLockFromPanel() {
  toggleLock()
  showMorePanel.value = false
}

// 从更多面板打开文件浏览器
function openFileBrowserFromPanel() {
  showMorePanel.value = false
  openFileBrowser()
}

// 从更多面板恢复会话
async function restoreFromPanel() {
  showMorePanel.value = false
  await restoreTask()
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
  min-height: 0;
  max-height: calc(100dvh - 140px);  /* 减去 header + status-bar + bottom-bar 的高度 */
  overflow: hidden;
}

.terminal-wrapper {
  flex: 1;
  min-height: 100px;
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
  margin-bottom: 8px;
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

/* 桌面端快捷键面板 - 默认隐藏 */
.desktop-panel {
  display: none;
}

/* 底部固定按钮栏 */
.bottom-bar {
  display: flex;
  gap: 8px;
  padding: 8px;
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-color, #333);
  flex-shrink: 0;
  min-height: 52px;
  position: sticky;
  bottom: 0;
  z-index: 10;
}

.bar-btn {
  flex: 1;
  padding: 12px 8px;
  border-radius: 8px;
  background: var(--bg-card);
  color: var(--text-color);
  font-size: 0.9rem;
  border: none;
  cursor: pointer;
  transition: background 0.2s;
}

.bar-btn:active {
  background: var(--primary-color);
  color: #fff;
}

/* 浮动面板 */
.floating-panel {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  z-index: 100;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}

/* 毛玻璃面板 */
.glass-panel {
  background: rgba(30, 30, 30, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

/* 终端预览条 */
.terminal-preview {
  background: rgba(20, 20, 20, 0.7);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  padding: 6px 10px;
  margin: 0 8px 4px 8px;
  border-radius: 8px 8px 0 0;
  min-height: 50px;
  max-height: 70px;
  overflow: hidden;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.preview-content {
  font-family: Consolas, "Courier New", monospace;
  font-size: 11px;
  color: #d4d4d4;
  white-space: pre-wrap;
  word-break: break-all;
  line-height: 1.3;
}

.panel-content {
  background: var(--bg-primary, #1a1a1a);
  border-radius: 16px 16px 0 0;
  padding: 16px;
  max-height: 50vh;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.panel-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-color);
}

.close-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-size: 1.2rem;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 按钮网格 */
.panel-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
}

.grid-btn {
  padding: 12px 6px;
  font-size: 0.85rem;
  border-radius: 8px;
  background: var(--bg-card);
  color: var(--text-color);
  border: none;
  cursor: pointer;
  transition: background 0.15s;
  touch-action: manipulation;
}

.grid-btn:active {
  background: var(--primary-color);
  color: #fff;
  transform: scale(0.95);
}

/* 命令网格 - 3列 */
.cmd-grid {
  grid-template-columns: repeat(3, 1fr);
}

/* 快捷键网格 - 4列 */
.hk-grid {
  grid-template-columns: repeat(4, 1fr);
}

/* 分区 */
.panel-section {
  margin-bottom: 16px;
}

.panel-section:last-child {
  margin-bottom: 0;
}

.section-title {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-bottom: 8px;
  padding-left: 4px;
}

/* 空提示 */
.empty-tip {
  text-align: center;
  color: var(--text-secondary);
  font-size: 0.85rem;
  padding: 20px;
}

/* 更多面板列表 */
.more-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.more-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: var(--bg-card);
  border-radius: 8px;
  border: none;
  cursor: pointer;
  color: var(--text-color);
  font-size: 0.95rem;
  text-align: left;
  transition: background 0.15s;
}

.more-item:active {
  background: var(--primary-color);
  color: #fff;
}

.more-icon {
  font-size: 1.2rem;
}

/* 滑入动画 */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.25s ease;
}

.slide-up-enter-active .panel-content,
.slide-up-leave-active .panel-content,
.slide-up-enter-active .terminal-preview,
.slide-up-leave-active .terminal-preview {
  transition: transform 0.25s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  background: rgba(0, 0, 0, 0);
}

.slide-up-enter-from .panel-content,
.slide-up-leave-to .panel-content,
.slide-up-enter-from .terminal-preview,
.slide-up-leave-to .terminal-preview {
  transform: translateY(100%);
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
  }

  .terminal-container {
    height: calc(100dvh - 100px);
    margin-bottom: 0;
  }

  /* 横屏时显示桌面面板，隐藏底部栏 */
  .desktop-panel {
    display: flex;
    flex-direction: column;
    width: 220px;
    flex-shrink: 0;
    background: var(--bg-secondary);
    border-radius: var(--border-radius);
    padding: 8px;
    max-height: calc(100dvh - 100px);
    overflow-y: auto;
  }

  .bottom-bar {
    display: none;
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
    padding: 10px 6px;
    font-size: 0.8rem;
  }

  .restore-bar {
    margin-top: 8px;
  }

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

  .file-browser-entry {
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px solid var(--border-color, #333);
  }
}
</style>
