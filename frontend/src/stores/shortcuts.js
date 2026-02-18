/**
 * 快捷键配置存储
 * 支持自定义命令按钮和自定义快捷键
 */

// 默认快捷键配置
const defaultShortcuts = {
  // 基础方向键（固定）
  basic: [
    { id: 'escape', key: 'Escape', label: 'Esc', type: 'basic', enabled: true },
    { id: 'enter', key: 'Enter', label: 'Enter', type: 'basic', enabled: true },
    { id: 'up', key: 'Up', label: '↑', type: 'basic', enabled: true },
    { id: 'down', key: 'Down', label: '↓', type: 'basic', enabled: true },
    { id: 'left', key: 'Left', label: '←', type: 'basic', enabled: true },
    { id: 'right', key: 'Right', label: '→', type: 'basic', enabled: true },
    { id: 'backspace', key: 'BSpace', label: '退格', type: 'basic', enabled: true },
  ],

  // 自定义命令按钮（可编辑命令和标签）
  commands: [
    { id: 'cmd1', label: '/compact', command: '/compact', enabled: true },
    { id: 'cmd2', label: '/clear', command: '/clear', enabled: true },
    { id: 'cmd3', label: '/help', command: '/help', enabled: true },
    { id: 'cmd4', label: '/rewind', command: '/rewind', enabled: true },
    { id: 'cmd5', label: '/mcp', command: '/mcp', enabled: true },
    { id: 'cmd6', label: '/exit', command: '/exit', enabled: true },
    { id: 'cmd7', label: '/doctor', command: '/doctor', enabled: false },
    { id: 'cmd8', label: '/permissions', command: '/permissions', enabled: false },
  ],

  // 自定义快捷键（可设置组合键）
  shortcuts: [
    { id: 'hk1', label: 'Ctrl+C', key: 'C-c', description: '中断', enabled: true },
    { id: 'hk2', label: 'Ctrl+D', key: 'C-d', description: '退出', enabled: true },
    { id: 'hk3', label: 'Ctrl+L', key: 'C-l', description: '清屏', enabled: true },
    { id: 'hk4', label: 'Ctrl+R', key: 'C-r', description: '搜索', enabled: true },
    { id: 'hk5', label: 'Ctrl+Z', key: 'C-z', description: '后台', enabled: false },
    { id: 'hk6', label: 'Ctrl+A', key: 'C-a', description: '行首', enabled: false },
    { id: 'hk7', label: 'Ctrl+E', key: 'C-e', description: '行尾', enabled: false },
    { id: 'hk8', label: 'Ctrl+K', key: 'C-k', description: '删到行尾', enabled: false },
    { id: 'hk9', label: 'Ctrl+U', key: 'C-u', description: '删到行首', enabled: false },
    { id: 'hk10', label: 'Ctrl+W', key: 'C-w', description: '删词', enabled: false },
    { id: 'hk11', label: 'F1', key: 'F1', description: '', enabled: false },
    { id: 'hk12', label: 'F2', key: 'F2', description: '', enabled: false },
    { id: 'hk13', label: 'F3', key: 'F3', description: '', enabled: false },
    { id: 'hk14', label: 'F4', key: 'F4', description: '', enabled: false },
    { id: 'hk15', label: 'F5', key: 'F5', description: '', enabled: false },
    { id: 'hk16', label: 'F6', key: 'F6', description: '', enabled: false },
  ]
}

// 获取快捷键配置
export function getShortcuts() {
  const saved = localStorage.getItem('shortcuts_v2')
  if (saved) {
    try {
      const parsed = JSON.parse(saved)
      // 合并默认配置和保存的配置
      return {
        basic: parsed.basic || defaultShortcuts.basic,
        commands: parsed.commands || defaultShortcuts.commands,
        shortcuts: parsed.shortcuts || defaultShortcuts.shortcuts
      }
    } catch (e) {
      console.error('Failed to parse shortcuts:', e)
    }
  }
  return JSON.parse(JSON.stringify(defaultShortcuts))
}

// 保存快捷键配置
export function saveShortcuts(shortcuts) {
  localStorage.setItem('shortcuts_v2', JSON.stringify(shortcuts))
}

// 重置为默认配置
export function resetShortcuts() {
  localStorage.removeItem('shortcuts_v2')
  return JSON.parse(JSON.stringify(defaultShortcuts))
}

// 获取默认配置
export function getDefaultShortcuts() {
  return JSON.parse(JSON.stringify(defaultShortcuts))
}

// 获取启用的基础按键
export function getEnabledBasicKeys() {
  const shortcuts = getShortcuts()
  return shortcuts.basic.filter(item => item.enabled)
}

// 获取启用的命令按钮
export function getEnabledCommands() {
  const shortcuts = getShortcuts()
  return shortcuts.commands.filter(item => item.enabled)
}

// 获取启用的快捷键
export function getEnabledShortcuts() {
  const shortcuts = getShortcuts()
  return shortcuts.shortcuts.filter(item => item.enabled)
}

// 更新单个配置项
export function updateShortcut(category, id, data) {
  const shortcuts = getShortcuts()
  const index = shortcuts[category].findIndex(item => item.id === id)
  if (index !== -1) {
    shortcuts[category][index] = { ...shortcuts[category][index], ...data }
    saveShortcuts(shortcuts)
  }
  return shortcuts
}

// 添加新配置项
export function addShortcut(category, item) {
  const shortcuts = getShortcuts()
  const newId = `${category}_${Date.now()}`
  shortcuts[category].push({ ...item, id: newId })
  saveShortcuts(shortcuts)
  return shortcuts
}

// 删除配置项
export function deleteShortcut(category, id) {
  const shortcuts = getShortcuts()
  shortcuts[category] = shortcuts[category].filter(item => item.id !== id)
  saveShortcuts(shortcuts)
  return shortcuts
}

// 可用的按键选项（用于配置快捷键）
export const availableKeys = [
  // Ctrl 组合键
  'C-a', 'C-b', 'C-c', 'C-d', 'C-e', 'C-f', 'C-g', 'C-h', 'C-i', 'C-j', 'C-k', 'C-l', 'C-m',
  'C-n', 'C-o', 'C-p', 'C-q', 'C-r', 'C-s', 'C-t', 'C-u', 'C-v', 'C-w', 'C-x', 'C-y', 'C-z',
  // 功能键
  'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12',
  // Alt 组合键
  'M-a', 'M-b', 'M-c', 'M-d', 'M-e', 'M-f', 'M-g', 'M-h', 'M-i', 'M-j', 'M-k', 'M-l', 'M-m',
  'M-n', 'M-o', 'M-p', 'M-q', 'M-r', 'M-s', 'M-t', 'M-u', 'M-v', 'M-w', 'M-x', 'M-y', 'M-z',
  // 特殊键
  'Tab', 'S-Tab', 'Insert', 'Delete', 'Home', 'End', 'PageUp', 'PageDown',
]

// 按键显示名称映射
export const keyDisplayNames = {
  'C-': 'Ctrl+',
  'M-': 'Alt+',
  'S-': 'Shift+',
  'BSpace': '退格',
  'Up': '↑', 'Down': '↓', 'Left': '←', 'Right': '→',
}

// 获取按键显示名称
export function getKeyDisplayName(key) {
  let name = key
  for (const [code, display] of Object.entries(keyDisplayNames)) {
    name = name.replace(code, display)
  }
  return name
}
