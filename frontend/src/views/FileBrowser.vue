<template>
  <div class="page">
    <div class="header">
      <button class="btn btn-sm btn-secondary" @click="goBack">返回</button>
      <h1>文件浏览器</h1>
      <button class="btn btn-sm btn-secondary" @click="goToWorkDir">工作目录</button>
    </div>

    <div v-if="error" class="error-message">{{ error }}</div>

    <!-- 工具栏 - 新建文件/文件夹 -->
    <div class="toolbar">
      <button class="btn btn-sm btn-secondary" @click="showNewFileDialog = true">
        <span>新建文件</span>
      </button>
      <button class="btn btn-sm btn-secondary" @click="showNewDirDialog = true">
        <span>新建文件夹</span>
      </button>
    </div>

    <!-- 面包屑导航 -->
    <div class="breadcrumb">
      <button class="breadcrumb-item" @click="navigateTo('/')">
        <span class="icon">📁</span>
        <span>根目录</span>
      </button>
      <span v-for="(part, index) in pathParts" :key="index" class="breadcrumb-segment">
        <span class="separator">/</span>
        <button class="breadcrumb-item" @click="navigateTo(getPathUpTo(index))">
          {{ part }}
        </button>
      </span>
    </div>

    <!-- 文件列表 -->
    <div v-if="loading" class="loading">
      <span class="spinner"></span>
    </div>

    <div v-else-if="currentDir" class="file-list">
      <!-- 返回上级 -->
      <div v-if="currentDir.parent" class="file-item parent-dir" @click="navigateTo(currentDir.parent)">
        <span class="file-icon">📁</span>
        <span class="file-name">..</span>
        <span class="file-meta">返回上级</span>
      </div>

      <!-- 文件/目录列表 -->
      <div
        v-for="item in currentDir.items"
        :key="item.path"
        :class="['file-item', { 'is-dir': item.is_dir, 'selected': selectedItem === item.path }]"
        @click="selectItem(item)"
        @dblclick="openItem(item)"
      >
        <span class="file-icon">{{ getFileIcon(item) }}</span>
        <span class="file-name">{{ item.name }}</span>
        <span class="file-size">{{ formatSize(item.size) }}</span>
        <span class="file-time">{{ formatTime(item.modified) }}</span>
        <!-- 操作按钮 -->
        <div class="file-actions" @click.stop>
          <button v-if="!item.is_dir" class="action-btn action-btn-download" @click="downloadFileDirect(item)" title="下载">↓</button>
          <button class="action-btn action-btn-delete" @click="deleteFileDirect(item)" title="删除">×</button>
        </div>
      </div>
    </div>

    <!-- 空目录提示 -->
    <div v-if="!loading && currentDir && currentDir.items.length === 0" class="empty-dir">
      空目录
    </div>

    <!-- 文件预览/编辑面板 -->
    <div v-if="previewFile" class="preview-panel">
      <div class="preview-header">
        <span class="preview-title">{{ previewFile.name }}</span>
        <div class="preview-actions">
          <button
            v-if="!isEditMode && !isImageFile && !isAudioFile"
            class="btn btn-sm btn-primary"
            @click="enterEditMode"
          >
            编辑
          </button>
          <template v-else-if="isEditMode">
            <button class="btn btn-sm btn-primary" @click="saveFile" :disabled="saving">
              {{ saving ? '保存中...' : '保存' }}
            </button>
            <button class="btn btn-sm btn-secondary" @click="cancelEdit">
              取消
            </button>
          </template>
          <button class="btn btn-sm btn-secondary" @click="downloadFile" title="下载文件">下载</button>
          <button class="btn btn-sm btn-secondary" @click="copyPath" title="复制路径">路径</button>
          <button v-if="!isEditMode && !isImageFile && !isAudioFile" class="btn btn-sm btn-secondary" @click="copyContent">复制</button>
          <button v-if="!isEditMode" class="btn btn-sm btn-danger" @click="deleteFile">删除</button>
          <button class="btn btn-sm btn-secondary" @click="closePreview">关闭</button>
        </div>
      </div>
      <div v-if="previewLoading" class="preview-loading">
        <span class="spinner"></span>
      </div>
      <!-- 图片预览 -->
      <div v-else-if="isImageFile && imageData" class="image-preview">
        <img :src="imageData" :alt="previewFile.name" />
      </div>
      <!-- 音频预览 -->
      <div v-else-if="isAudioFile && audioData" class="audio-preview">
        <div class="audio-icon">&#9835;</div>
        <div class="audio-name">{{ previewFile.name }}</div>
        <audio controls :src="audioData" preload="metadata"></audio>
      </div>
      <!-- 编辑模式：Monaco Editor -->
      <div v-else-if="isEditMode" ref="editorContainer" class="editor-container"></div>
      <!-- 预览模式：高亮显示 -->
      <pre v-else class="preview-content"><code :class="previewLanguage" v-html="highlightedContent"></code></pre>
    </div>

    <!-- 新建文件对话框 -->
    <div v-if="showNewFileDialog" class="dialog-overlay" @click.self="showNewFileDialog = false">
      <div class="dialog">
        <h3>新建文件</h3>
        <input
          v-model="newFileName"
          type="text"
          class="input"
          placeholder="文件名（如：test.py）"
          @keyup.enter="createNewFile"
          ref="newFileInput"
        />
        <div class="dialog-actions">
          <button class="btn btn-secondary" @click="showNewFileDialog = false">取消</button>
          <button class="btn btn-primary" @click="createNewFile" :disabled="creating">
            {{ creating ? '创建中...' : '创建' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 新建文件夹对话框 -->
    <div v-if="showNewDirDialog" class="dialog-overlay" @click.self="showNewDirDialog = false">
      <div class="dialog">
        <h3>新建文件夹</h3>
        <input
          v-model="newDirName"
          type="text"
          class="input"
          placeholder="文件夹名"
          @keyup.enter="createNewDir"
          ref="newDirInput"
        />
        <div class="dialog-actions">
          <button class="btn btn-secondary" @click="showNewDirDialog = false">取消</button>
          <button class="btn btn-primary" @click="createNewDir" :disabled="creating">
            {{ creating ? '创建中...' : '创建' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../api'
import hljs from 'highlight.js/lib/core'
// 按需加载语言支持
import javascript from 'highlight.js/lib/languages/javascript'
import python from 'highlight.js/lib/languages/python'
import json from 'highlight.js/lib/languages/json'
import bash from 'highlight.js/lib/languages/bash'
import css from 'highlight.js/lib/languages/css'
import xml from 'highlight.js/lib/languages/xml'
import yaml from 'highlight.js/lib/languages/yaml'
import markdown from 'highlight.js/lib/languages/markdown'
import sql from 'highlight.js/lib/languages/sql'
import typescript from 'highlight.js/lib/languages/typescript'
import 'highlight.js/styles/atom-one-dark.css'

// Monaco Editor
import * as monaco from 'monaco-editor'

// 注册语言
hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('python', python)
hljs.registerLanguage('json', json)
hljs.registerLanguage('bash', bash)
hljs.registerLanguage('css', css)
hljs.registerLanguage('xml', xml)
hljs.registerLanguage('yaml', yaml)
hljs.registerLanguage('markdown', markdown)
hljs.registerLanguage('sql', sql)
hljs.registerLanguage('typescript', typescript)

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const error = ref('')
const currentPath = ref('/')
const currentDir = ref(null)
const selectedItem = ref(null)
const previewFile = ref(null)
const previewContent = ref('')
const previewLoading = ref(false)
const workDir = ref('')

// 编辑模式相关
const isEditMode = ref(false)
const editorContainer = ref(null)
const saving = ref(false)
const imageData = ref(null)
let editor = null

// 新建文件/文件夹相关
const showNewFileDialog = ref(false)
const showNewDirDialog = ref(false)
const newFileName = ref('')
const newDirName = ref('')
const creating = ref(false)
const newFileInput = ref(null)
const newDirInput = ref(null)

// 计算路径分段
const pathParts = computed(() => {
  if (!currentPath.value || currentPath.value === '/') return []
  return currentPath.value.split('/').filter(p => p)
})

// 获取路径到指定层级
function getPathUpTo(index) {
  const parts = pathParts.value.slice(0, index + 1)
  return '/' + parts.join('/')
}

// 预览语言
const previewLanguage = computed(() => {
  if (!previewFile.value) return ''
  const ext = previewFile.value.extension?.toLowerCase() || ''
  const langMap = {
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.py': 'python',
    '.json': 'json',
    '.sh': 'bash',
    '.bash': 'bash',
    '.css': 'css',
    '.html': 'xml',
    '.xml': 'xml',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.md': 'markdown',
    '.sql': 'sql'
  }
  return langMap[ext] || ''
})

// 判断是否为图片文件
const isImageFile = computed(() => {
  if (!previewFile.value) return false
  const ext = previewFile.value.extension?.toLowerCase() || ''
  return ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg', '.ico'].includes(ext)
})

// 判断是否为音频文件
const isAudioFile = computed(() => {
  if (!previewFile.value) return false
  const ext = previewFile.value.extension?.toLowerCase() || ''
  return ['.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac'].includes(ext)
})

// 音频数据（base64）
const audioData = ref(null)

// 获取Monaco语言ID
function getMonacoLanguage(extension) {
  const langMap = {
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.py': 'python',
    '.json': 'json',
    '.sh': 'shell',
    '.bash': 'shell',
    '.css': 'css',
    '.html': 'html',
    '.xml': 'xml',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.md': 'markdown',
    '.sql': 'sql',
    '.txt': 'plaintext'
  }
  return langMap[extension?.toLowerCase()] || 'plaintext'
}

// 高亮内容
const highlightedContent = computed(() => {
  if (!previewContent.value) return ''
  if (previewLanguage.value) {
    try {
      return hljs.highlight(previewContent.value, { language: previewLanguage.value }).value
    } catch (e) {
      return escapeHtml(previewContent.value)
    }
  }
  // 自动检测语言
  try {
    return hljs.highlightAuto(previewContent.value).value
  } catch (e) {
    return escapeHtml(previewContent.value)
  }
})

function escapeHtml(text) {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

onMounted(() => {
  // 从路由参数获取初始路径和工作目录
  const initialPath = route.query.path || '/'
  workDir.value = route.query.workDir || ''

  navigateTo(initialPath)
})

// 监听对话框打开，自动聚焦输入框
watch(showNewFileDialog, async (val) => {
  if (val) {
    newFileName.value = ''
    await nextTick()
    newFileInput.value?.focus()
  }
})

watch(showNewDirDialog, async (val) => {
  if (val) {
    newDirName.value = ''
    await nextTick()
    newDirInput.value?.focus()
  }
})

// 监听路由变化
watch(() => route.query.path, (newPath) => {
  if (newPath && newPath !== currentPath.value) {
    navigateTo(newPath)
  }
})

async function loadDirectory(path) {
  loading.value = true
  error.value = ''

  try {
    const res = await api.get('/files/list', {
      params: { path, show_hidden: true }
    })
    currentDir.value = res.data
    currentPath.value = res.data.path
  } catch (e) {
    error.value = e.response?.data?.detail || '加载目录失败'
  } finally {
    loading.value = false
  }
}

function navigateTo(path) {
  if (previewFile.value) {
    closePreview()
  }
  selectedItem.value = null
  loadDirectory(path)
  // 更新 URL（不触发导航）
  router.replace({
    query: { ...route.query, path }
  })
}

function selectItem(item) {
  if (selectedItem.value === item.path) {
    // 双击效果：再次点击已选中项时打开
    openItem(item)
  } else {
    selectedItem.value = item.path
  }
}

function openItem(item) {
  if (item.is_dir) {
    navigateTo(item.path)
  } else {
    openPreview(item)
  }
}

async function openPreview(item) {
  previewFile.value = item
  previewContent.value = ''
  imageData.value = null
  audioData.value = null
  previewLoading.value = true
  isEditMode.value = false

  // 判断是否为图片
  const ext = item.extension?.toLowerCase() || ''
  const imageExts = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg', '.ico']
  const audioExts = ['.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac']

  if (imageExts.includes(ext)) {
    // 读取图片
    try {
      const res = await api.get('/files/binary', {
        params: { path: item.path }
      })
      imageData.value = `data:${res.data.mime_type};base64,${res.data.base64}`
    } catch (e) {
      previewContent.value = `无法读取图片: ${e.response?.data?.detail || e.message}`
    } finally {
      previewLoading.value = false
    }
  } else if (audioExts.includes(ext)) {
    // 读取音频
    try {
      const res = await api.get('/files/binary', {
        params: { path: item.path }
      })
      audioData.value = `data:${res.data.mime_type};base64,${res.data.base64}`
    } catch (e) {
      previewContent.value = `无法读取音频: ${e.response?.data?.detail || e.message}`
    } finally {
      previewLoading.value = false
    }
  } else {
    // 读取文本文件
    try {
      const res = await api.get('/files/read', {
        params: { path: item.path }
      })
      previewContent.value = res.data.content
    } catch (e) {
      previewContent.value = `无法读取文件: ${e.response?.data?.detail || e.message}`
    } finally {
      previewLoading.value = false
    }
  }
}

function closePreview() {
  previewFile.value = null
  previewContent.value = ''
  imageData.value = null
  audioData.value = null
  isEditMode.value = false
  // 销毁编辑器
  if (editor) {
    editor.dispose()
    editor = null
  }
}

async function copyContent() {
  if (previewContent.value) {
    try {
      await copyToClipboard(previewContent.value)
      alert('已复制到剪贴板')
    } catch (e) {
      alert('复制失败')
    }
  }
}

async function copyPath() {
  if (previewFile.value) {
    try {
      await copyToClipboard(previewFile.value.path)
      alert('路径已复制到剪贴板')
    } catch (e) {
      alert('复制失败')
    }
  }
}

// 下载文件
async function downloadFile() {
  if (!previewFile.value) return

  // 检查文件大小（50MB 限制）
  const maxSize = 50 * 1024 * 1024
  if (previewFile.value.size > maxSize) {
    const sizeMB = (previewFile.value.size / 1024 / 1024).toFixed(2)
    alert(`文件过大（${sizeMB}MB），超过限制（50MB）`)
    return
  }

  try {
    const res = await api.get('/files/binary', {
      params: { path: previewFile.value.path }
    })

    // 解码 base64
    const binary = atob(res.data.base64)
    const bytes = new Uint8Array(binary.length)
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i)
    }

    // 创建 Blob 并下载
    const blob = new Blob([bytes], { type: res.data.mime_type })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = previewFile.value.name
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (e) {
    alert('下载失败: ' + (e.response?.data?.detail || e.message))
  }
}

// 直接下载文件（从列表）
async function downloadFileDirect(item) {
  // 检查文件大小（50MB 限制）
  const maxSize = 50 * 1024 * 1024
  if (item.size > maxSize) {
    const sizeMB = (item.size / 1024 / 1024).toFixed(2)
    alert(`文件过大（${sizeMB}MB），超过限制（50MB）`)
    return
  }

  try {
    const res = await api.get('/files/binary', {
      params: { path: item.path }
    })

    // 解码 base64
    const binary = atob(res.data.base64)
    const bytes = new Uint8Array(binary.length)
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i)
    }

    // 创建 Blob 并下载
    const blob = new Blob([bytes], { type: res.data.mime_type })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = item.name
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (e) {
    alert('下载失败: ' + (e.response?.data?.detail || e.message))
  }
}

// 直接删除文件/文件夹（从列表）
async function deleteFileDirect(item) {
  const typeText = item.is_dir ? '文件夹' : '文件'
  const confirmed = confirm(`确定要删除${typeText} "${item.name}" 吗？此操作不可恢复！`)
  if (!confirmed) return

  try {
    await api.delete('/files/delete', {
      params: { path: item.path }
    })
    loadDirectory(currentPath.value)
  } catch (e) {
    alert('删除失败: ' + (e.response?.data?.detail || e.message))
  }
}

// 兼容 HTTP/HTTPS 的复制方法
async function copyToClipboard(text) {
  // 优先使用 Clipboard API
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(text)
  } else {
    // 降级使用 execCommand
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.left = '-9999px'
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
  }
}

async function deleteFile() {
  if (!previewFile.value) return

  const confirmed = confirm(`确定要删除 "${previewFile.value.name}" 吗？此操作不可恢复！`)
  if (!confirmed) return

  try {
    await api.delete('/files/delete', {
      params: { path: previewFile.value.path }
    })
    alert('删除成功')
    closePreview()
    loadDirectory(currentPath.value)
  } catch (e) {
    alert('删除失败: ' + (e.response?.data?.detail || e.message))
  }
}

// 进入编辑模式
async function enterEditMode() {
  isEditMode.value = true
  await nextTick()

  if (editorContainer.value && previewFile.value) {
    // 销毁旧编辑器
    if (editor) {
      editor.dispose()
    }

    // 创建新编辑器
    editor = monaco.editor.create(editorContainer.value, {
      value: previewContent.value,
      language: getMonacoLanguage(previewFile.value.extension),
      theme: 'vs-dark',
      fontSize: 14,
      fontFamily: 'Consolas, Monaco, Courier New, monospace',
      minimap: { enabled: false },
      scrollBeyondLastLine: false,
      automaticLayout: true,
      tabSize: 2,
      wordWrap: 'on',
      lineNumbers: 'on',
      renderLineHighlight: 'line'
    })
  }
}

// 取消编辑
function cancelEdit() {
  isEditMode.value = false
  if (editor) {
    editor.dispose()
    editor = null
  }
}

// 保存文件
async function saveFile() {
  if (!editor || !previewFile.value) return

  const content = editor.getValue()
  saving.value = true

  try {
    await api.post('/files/write', { content }, {
      params: { path: previewFile.value.path }
    })
    previewContent.value = content
    isEditMode.value = false
    editor.dispose()
    editor = null
    alert('保存成功')
    // 刷新文件列表
    loadDirectory(currentPath.value)
  } catch (e) {
    alert('保存失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

// 创建新文件
async function createNewFile() {
  if (!newFileName.value.trim()) {
    alert('请输入文件名')
    return
  }

  creating.value = true
  const filePath = currentPath.value === '/'
    ? '/' + newFileName.value.trim()
    : currentPath.value + '/' + newFileName.value.trim()

  try {
    await api.post('/files/create', { path: filePath })
    showNewFileDialog.value = false
    newFileName.value = ''
    loadDirectory(currentPath.value)
  } catch (e) {
    alert('创建失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    creating.value = false
  }
}

// 创建新文件夹
async function createNewDir() {
  if (!newDirName.value.trim()) {
    alert('请输入文件夹名')
    return
  }

  creating.value = true
  const dirPath = currentPath.value === '/'
    ? '/' + newDirName.value.trim()
    : currentPath.value + '/' + newDirName.value.trim()

  try {
    await api.post('/files/mkdir', { path: dirPath })
    showNewDirDialog.value = false
    newDirName.value = ''
    loadDirectory(currentPath.value)
  } catch (e) {
    alert('创建失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    creating.value = false
  }
}

function goToWorkDir() {
  if (workDir.value) {
    navigateTo(workDir.value)
  }
}

function goBack() {
  router.back()
}

// 获取文件图标
function getFileIcon(item) {
  if (item.is_dir) return '📁'

  const ext = item.extension?.toLowerCase() || ''
  const iconMap = {
    '.js': '📜', '.jsx': '📜', '.ts': '📜', '.tsx': '📜',
    '.py': '🐍', '.rb': '💎',
    '.json': '📋', '.yaml': '📋', '.yml': '📋',
    '.md': '📝', '.txt': '📄',
    '.html': '🌐', '.css': '🎨',
    '.sh': '⌨️', '.bash': '⌨️',
    '.sql': '🗃️',
    '.png': '🖼️', '.jpg': '🖼️', '.jpeg': '🖼️', '.gif': '🖼️',
    '.pdf': '📕',
    '.zip': '📦', '.tar': '📦', '.gz': '📦'
  }
  return iconMap[ext] || '📄'
}

// 格式化文件大小
function formatSize(size) {
  if (size === 0) return '-'
  const units = ['B', 'KB', 'MB', 'GB']
  let unitIndex = 0
  let displaySize = size
  while (displaySize >= 1024 && unitIndex < units.length - 1) {
    displaySize /= 1024
    unitIndex++
  }
  return `${displaySize.toFixed(1)} ${units[unitIndex]}`
}

// 格式化时间
function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp * 1000)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString().slice(0, 5)
}
</script>

<style scoped>
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

/* 工具栏 */
.toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  flex-shrink: 0;
}

/* 面包屑导航 */
.breadcrumb {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
  margin-bottom: 8px;
  overflow-x: auto;
  flex-shrink: 0;
}

.breadcrumb-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: 4px;
  font-size: 0.85rem;
}

.breadcrumb-item:hover {
  background: var(--bg-card);
  color: var(--text-color);
}

.breadcrumb-segment {
  display: flex;
  align-items: center;
}

.separator {
  color: var(--text-secondary);
  margin: 0 2px;
}

/* 文件列表 */
.file-list {
  flex: 1;
  overflow-y: auto;
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
}

.file-item {
  display: grid;
  grid-template-columns: 32px 1fr 80px 100px auto;
  gap: 8px;
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid var(--border-color, #333);
  cursor: pointer;
  transition: background 0.15s;
}

.file-item:last-child {
  border-bottom: none;
}

.file-item:hover {
  background: var(--bg-card);
}

.file-item.selected {
  background: rgba(var(--primary-color-rgb, 100, 100, 255), 0.2);
}

.file-item.is-dir .file-name {
  font-weight: 500;
}

/* 文件操作按钮 */
.file-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.15s;
}

.file-item:hover .file-actions {
  opacity: 1;
}

.action-btn {
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
}

.action-btn-download {
  background: rgba(97, 175, 239, 0.2);
  color: #61afef;
}

.action-btn-download:hover {
  background: #61afef;
  color: #fff;
}

.action-btn-delete {
  background: rgba(220, 53, 69, 0.2);
  color: #dc3545;
}

.action-btn-delete:hover {
  background: #dc3545;
  color: #fff;
}

.file-icon {
  font-size: 1.2rem;
  text-align: center;
}

.file-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size, .file-time {
  font-size: 0.8rem;
  color: var(--text-secondary);
  text-align: right;
}

.parent-dir {
  background: var(--bg-card);
}

.empty-dir {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
}

/* 预览/编辑面板 */
.preview-panel {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--bg-primary, #1a1a2e);
  z-index: 100;
  display: flex;
  flex-direction: column;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color, #333);
  flex-shrink: 0;
}

.preview-title {
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.preview-actions {
  display: flex;
  gap: 8px;
}

.preview-loading {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-content {
  flex: 1;
  overflow: auto;
  padding: 16px;
  margin: 0;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 0.85rem;
  line-height: 1.5;
  background: #282c34;
  color: #abb2bf;
  white-space: pre-wrap;
  word-break: break-all;
}

.preview-content code {
  background: transparent;
  padding: 0;
}

/* Monaco 编辑器容器 */
.editor-container {
  flex: 1;
  overflow: hidden;
}

/* 图片预览 */
.image-preview {
  flex: 1;
  overflow: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
  padding: 16px;
}

.image-preview img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

/* 音频预览 */
.audio-preview {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  background: var(--bg-primary);
  padding: 24px;
}

.audio-icon {
  font-size: 4rem;
  color: var(--primary-color, #61afef);
}

.audio-name {
  font-size: 1rem;
  color: var(--text-color);
  text-align: center;
  word-break: break-all;
  max-width: 100%;
}

.audio-preview audio {
  width: 100%;
  max-width: 400px;
}

/* 按钮样式 */
.btn-danger {
  background: #dc3545;
  color: white;
}

.btn-danger:hover {
  background: #c82333;
}

/* 对话框 */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}

.dialog {
  background: var(--bg-secondary, #2d2d3d);
  border-radius: 8px;
  padding: 20px;
  width: 90%;
  max-width: 400px;
}

.dialog h3 {
  margin: 0 0 16px 0;
  font-size: 1rem;
}

.dialog .input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color, #444);
  border-radius: 4px;
  background: var(--bg-primary, #1a1a2e);
  color: var(--text-color, #e0e0e0);
  font-size: 0.9rem;
  box-sizing: border-box;
}

.dialog .input:focus {
  outline: none;
  border-color: var(--primary-color, #61afef);
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}

/* 响应式 */
@media (max-width: 480px) {
  .file-item {
    grid-template-columns: 28px 1fr 50px auto;
  }

  .file-time {
    display: none;
  }

  /* 移动端始终显示操作按钮 */
  .file-actions {
    opacity: 1;
  }
}
</style>
