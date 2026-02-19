/**
 * 快捷键配置存储
 * 支持自定义命令按钮和自定义快捷键
 */

// 可用的修饰键
export const availableModifiers = [
  { value: '', label: '无' },
  { value: 'C', label: 'Ctrl' },
  { value: 'S', label: 'Shift' },
  { value: 'M', label: 'Alt' },
]

// 可用的按键选项
export const availableKeyOptions = [
  // 字母
  { value: 'a', label: 'A' }, { value: 'b', label: 'B' }, { value: 'c', label: 'C' },
  { value: 'd', label: 'D' }, { value: 'e', label: 'E' }, { value: 'f', label: 'F' },
  { value: 'g', label: 'G' }, { value: 'h', label: 'H' }, { value: 'i', label: 'I' },
  { value: 'j', label: 'J' }, { value: 'k', label: 'K' }, { value: 'l', label: 'L' },
  { value: 'm', label: 'M' }, { value: 'n', label: 'N' }, { value: 'o', label: 'O' },
  { value: 'p', label: 'P' }, { value: 'q', label: 'Q' }, { value: 'r', label: 'R' },
  { value: 's', label: 'S' }, { value: 't', label: 'T' }, { value: 'u', label: 'U' },
  { value: 'v', label: 'V' }, { value: 'w', label: 'W' }, { value: 'x', label: 'X' },
  { value: 'y', label: 'Y' }, { value: 'z', label: 'Z' },
  // 数字
  { value: '0', label: '0' }, { value: '1', label: '1' }, { value: '2', label: '2' },
  { value: '3', label: '3' }, { value: '4', label: '4' }, { value: '5', label: '5' },
  { value: '6', label: '6' }, { value: '7', label: '7' }, { value: '8', label: '8' },
  { value: '9', label: '9' },
  // 功能键
  { value: 'F1', label: 'F1' }, { value: 'F2', label: 'F2' }, { value: 'F3', label: 'F3' },
  { value: 'F4', label: 'F4' }, { value: 'F5', label: 'F5' }, { value: 'F6', label: 'F6' },
  { value: 'F7', label: 'F7' }, { value: 'F8', label: 'F8' }, { value: 'F9', label: 'F9' },
  { value: 'F10', label: 'F10' }, { value: 'F11', label: 'F11' }, { value: 'F12', label: 'F12' },
  // 特殊键
  { value: 'Tab', label: 'Tab' },
  { value: 'Home', label: 'Home' },
  { value: 'End', label: 'End' },
  { value: 'Insert', label: 'Insert' },
  { value: 'Delete', label: 'Delete' },
  { value: 'PageUp', label: 'PageUp' },
  { value: 'PageDown', label: 'PageDown' },
]

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

  // 自定义命令按钮（可编辑命令和标签）- 精简为 4 个
  commands: [
    { id: 'cmd1', label: '/compact', command: '/compact', enabled: true },
    { id: 'cmd2', label: '/clear', command: '/clear', enabled: true },
    { id: 'cmd3', label: '/help', command: '/help', enabled: true },
    { id: 'cmd4', label: '/rewind', command: '/rewind', enabled: true },
  ],

  // 自定义快捷键（新数据结构）- 精简为 4 个默认
  shortcuts: [
    { id: 'hk1', label: '中断', modifiers: ['C'], key: 'c', description: '中断当前命令', enabled: true },
    { id: 'hk2', label: '退出', modifiers: ['C'], key: 'd', description: '退出/EOF', enabled: true },
    { id: 'hk3', label: '清屏', modifiers: ['C'], key: 'l', description: '清空屏幕', enabled: true },
    { id: 'hk4', label: '搜索', modifiers: ['C'], key: 'r', description: '搜索历史', enabled: true },
  ]
}

// 获取快捷键配置
export function getShortcuts() {
  const saved = localStorage.getItem('shortcuts_v3')
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
  localStorage.setItem('shortcuts_v3', JSON.stringify(shortcuts))
}

// 重置为默认配置
export function resetShortcuts() {
  localStorage.removeItem('shortcuts_v3')
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

// 移动配置项顺序（direction: 'up' 或 'down'）
export function moveShortcut(category, id, direction) {
  const shortcuts = getShortcuts()
  const list = shortcuts[category]
  const index = list.findIndex(item => item.id === id)

  if (index === -1) return shortcuts

  const newIndex = direction === 'up' ? index - 1 : index + 1

  // 边界检查
  if (newIndex < 0 || newIndex >= list.length) return shortcuts

  // 交换位置
  const temp = list[index]
  list[index] = list[newIndex]
  list[newIndex] = temp

  saveShortcuts(shortcuts)
  return shortcuts
}

/**
 * 将新数据结构转换为 tmux 格式
 * @param {Object} shortcut - 快捷键对象 { modifiers: ['C', 'S'], key: 'c' }
 * @returns {string} tmux 格式的按键，如 'C-S-c'
 */
export function keyToTmux(shortcut) {
  if (!shortcut) return ''

  const { modifiers = [], key = '' } = shortcut

  // 如果没有修饰键，直接返回按键
  if (!modifiers.length || modifiers.every(m => !m)) {
    return key
  }

  // 过滤空修饰键，拼接成 tmux 格式
  const validModifiers = modifiers.filter(m => m)
  if (validModifiers.length === 0) {
    return key
  }

  // tmux 格式：C-S-c (Ctrl+Shift+c)
  return [...validModifiers, key].join('-')
}

/**
 * 从 tmux 格式解析为新数据结构
 * @param {string} tmuxKey - tmux 格式的按键，如 'C-c' 或 'C-S-c'
 * @returns {Object} { modifiers: ['C'], key: 'c' }
 */
export function tmuxToKey(tmuxKey) {
  if (!tmuxKey) return { modifiers: [], key: '' }

  const parts = tmuxKey.split('-')
  if (parts.length === 1) {
    return { modifiers: [], key: parts[0] }
  }

  const modifiers = parts.slice(0, -1)
  const key = parts[parts.length - 1]

  return { modifiers, key }
}

/**
 * 生成显示名称
 * @param {Object} shortcut - 快捷键对象
 * @returns {string} 显示名称，如 'Ctrl+C' 或 'Ctrl+Shift+Z'
 */
export function getKeyDisplayName(shortcut) {
  if (!shortcut) return ''

  const { modifiers = [], key = '' } = shortcut

  const modifierNames = {
    'C': 'Ctrl',
    'S': 'Shift',
    'M': 'Alt',
  }

  const parts = modifiers
    .filter(m => m)
    .map(m => modifierNames[m] || m)

  if (key) {
    parts.push(key.toUpperCase())
  }

  return parts.join('+')
}

// 兼容旧版本的按键显示名称映射
export const keyDisplayNames = {
  'C-': 'Ctrl+',
  'M-': 'Alt+',
  'S-': 'Shift+',
  'BSpace': '退格',
  'Up': '↑', 'Down': '↓', 'Left': '←', 'Right': '→',
}

// 兼容旧版本的 availableKeys（用于向后兼容）
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
