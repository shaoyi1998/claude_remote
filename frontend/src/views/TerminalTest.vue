<template>
  <div class="page">
    <div class="header">
      <h1>xterm.js 颜色测试</h1>
      <button class="btn btn-sm btn-secondary" @click="goBack">返回</button>
    </div>

    <div class="test-container">
      <div ref="terminalContainer" class="terminal-container"></div>
    </div>

    <div class="test-buttons">
      <button class="btn btn-primary" @click="testAnsiColors">测试ANSI颜色</button>
      <button class="btn btn-secondary" @click="test256Colors">测试256色</button>
      <button class="btn btn-secondary" @click="testRainbow">彩虹测试</button>
      <button class="btn btn-secondary" @click="testLsColors">模拟ls --color</button>
      <button class="btn btn-danger" @click="clearTerminal">清空</button>
    </div>

    <div class="info-panel">
      <h3>颜色测试说明</h3>
      <p>如果上方终端显示彩色文字，说明 xterm.js 颜色配置正确。</p>
      <p>如果仍然是黑白，可能是：</p>
      <ul>
        <li>xterm.css 未正确加载</li>
        <li>主题配置未生效</li>
        <li>CSS 样式冲突</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Terminal } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'
import 'xterm/css/xterm.css'

const router = useRouter()
const terminalContainer = ref(null)
let terminal = null
let fitAddon = null

onMounted(() => {
  initTerminal()
})

onUnmounted(() => {
  if (terminal) {
    terminal.dispose()
  }
  window.removeEventListener('resize', handleResize)
})

function initTerminal() {
  // 使用完整的 One Dark Pro 主题
  terminal = new Terminal({
    cursorBlink: true,
    cursorStyle: 'block',
    fontSize: 14,
    fontFamily: 'Consolas, "Courier New", monospace',
    lineHeight: 1.2,
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

  // 双重 requestAnimationFrame 确保 DOM 完全渲染
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      try {
        fitAddon.fit()
      } catch (e) {
        console.warn('Failed to fit terminal:', e)
      }
    })
  })

  window.addEventListener('resize', handleResize)

  // 显示欢迎信息
  terminal.writeln('\x1b[1;36m=== xterm.js 颜色测试页面 ===\x1b[0m')
  terminal.writeln('')
  terminal.writeln('点击下方按钮测试不同的颜色效果')
  terminal.writeln('')
}

function handleResize() {
  try {
    if (fitAddon && terminal) {
      fitAddon.fit()
    }
  } catch (e) {
    console.warn('Failed to fit terminal:', e)
  }
}

function testAnsiColors() {
  terminal.writeln('')
  terminal.writeln('\x1b[1m=== 标准 ANSI 16色测试 ===\x1b[0m')
  terminal.writeln('')

  // 标准8色
  const colors = [
    { name: 'Black', code: 30 },
    { name: 'Red', code: 31 },
    { name: 'Green', code: 32 },
    { name: 'Yellow', code: 33 },
    { name: 'Blue', code: 34 },
    { name: 'Magenta', code: 35 },
    { name: 'Cyan', code: 36 },
    { name: 'White', code: 37 }
  ]

  let line = ''
  colors.forEach(c => {
    line += `\x1b[${c.code}m${c.name}\x1b[0m  `
  })
  terminal.writeln(line)

  // 高亮8色
  terminal.writeln('')
  terminal.writeln('\x1b[1m高亮颜色:\x1b[0m')
  line = ''
  colors.forEach(c => {
    line += `\x1b[1;${c.code}m${c.name}\x1b[0m  `
  })
  terminal.writeln(line)

  // 背景色
  terminal.writeln('')
  terminal.writeln('\x1b[1m背景色:\x1b[0m')
  line = ''
  colors.forEach(c => {
    line += `\x1b[${c.code + 10}m ${c.name.slice(0, 4)} \x1b[0m `
  })
  terminal.writeln(line)
  terminal.writeln('')
}

function test256Colors() {
  terminal.writeln('')
  terminal.writeln('\x1b[1m=== 256色测试 ===\x1b[0m')
  terminal.writeln('')

  // 测试 256 色的前 16 色
  for (let i = 0; i < 16; i++) {
    terminal.write(`\x1b[38;5;${i}m█\x1b[0m`)
  }
  terminal.writeln('')

  // 测试 216 色方块
  for (let r = 0; r < 6; r++) {
    for (let g = 0; g < 6; g++) {
      for (let b = 0; b < 6; b++) {
        const color = 16 + r * 36 + g * 6 + b
        terminal.write(`\x1b[38;5;${color}m█\x1b[0m`)
      }
    }
    terminal.writeln('')
  }

  // 灰度色
  terminal.writeln('')
  terminal.writeln('\x1b[1m灰度:\x1b[0m')
  for (let i = 232; i < 256; i++) {
    terminal.write(`\x1b[38;5;${i}m█\x1b[0m`)
  }
  terminal.writeln('')
}

function testRainbow() {
  terminal.writeln('')
  terminal.writeln('\x1b[1m=== 彩虹测试 ===\x1b[0m')
  terminal.writeln('')

  const text = 'Claude Remote - xterm.js 颜色测试成功！'
  const colors = [196, 202, 208, 214, 226, 190, 154, 118, 82, 46, 47, 48, 49, 51, 45, 39, 33, 27, 93, 129, 165]

  for (let i = 0; i < text.length; i++) {
    const color = colors[i % colors.length]
    terminal.write(`\x1b[38;5;${color}m${text[i]}\x1b[0m`)
  }
  terminal.writeln('')

  // 另一行彩虹
  const text2 = '★★★ 终端彩色输出正常工作 ★★★'
  for (let i = 0; i < text2.length; i++) {
    const color = colors[(i + 10) % colors.length]
    terminal.write(`\x1b[38;5;${color}m${text2[i]}\x1b[0m`)
  }
  terminal.writeln('')
}

function testLsColors() {
  terminal.writeln('')
  terminal.writeln('\x1b[1m=== 模拟 ls --color 输出 ===\x1b[0m')
  terminal.writeln('')

  // 模拟不同文件类型的颜色
  terminal.writeln('\x1b[1;34mDocuments/\x1b[0m  \x1b[1;34mDownloads/\x1b[0m  \x1b[1;34mPictures/\x1b[0m')
  terminal.writeln('\x1b[32mscript.sh\x1b[0m  \x1b[33mconfig.yaml\x1b[0m  \x1b[31merror.log\x1b[0m')
  terminal.writeln('\x1b[36mREADME.md\x1b[0m  \x1b[35mdata.json\x1b[0m  \x1b[37mplain.txt\x1b[0m')
  terminal.writeln('\x1b[1;32m executable \x1b[0m  \x1b[0;34m symlink\x1b[0m  \x1b[0;30;41m broken\x1b[0m')
  terminal.writeln('')
  terminal.writeln('\x1b[2m权限:\x1b[0m \x1b[1;32m-rwxr-xr-x\x1b[0m \x1b[1;34muser\x1b[0m:\x1b[1;34mgroup\x1b[0m 4096 Jan 18 12:34')
}

function clearTerminal() {
  terminal.clear()
  terminal.writeln('\x1b[1;36m=== 终端已清空 ===\x1b[0m')
  terminal.writeln('')
}

function goBack() {
  router.push('/')
}
</script>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  height: 100dvh;
  overflow: hidden;
  padding: 16px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.header h1 {
  font-size: 1.2rem;
}

.test-container {
  flex: 1;
  min-height: 300px;
  margin-bottom: 16px;
}

.terminal-container {
  width: 100%;
  height: 100%;
  background: #1e1e1e;
  border-radius: 8px;
  padding: 0;
}

.terminal-container :deep(.xterm) {
  padding: 8px;
  box-sizing: border-box;
}

.terminal-container :deep(.xterm-screen) {
  padding: 0;
}

.test-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.info-panel {
  background: var(--bg-secondary);
  border-radius: 8px;
  padding: 16px;
  flex-shrink: 0;
}

.info-panel h3 {
  margin: 0 0 8px 0;
  font-size: 0.9rem;
}

.info-panel p {
  margin: 0 0 4px 0;
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.info-panel ul {
  margin: 8px 0 0 0;
  padding-left: 20px;
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.info-panel li {
  margin-bottom: 4px;
}

/* xterm 样式强制覆盖 */
.terminal-container :deep(.xterm) {
  padding: 4px;
}

.terminal-container :deep(.xterm-viewport) {
  overflow-y: auto !important;
}
</style>
