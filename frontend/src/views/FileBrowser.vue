<template>
  <div class="page">
    <div class="header">
      <button class="btn btn-sm btn-secondary" @click="goBack">返回</button>
      <h1>文件浏览器</h1>
      <button class="btn btn-sm btn-secondary" @click="goToWorkDir">工作目录</button>
    </div>

    <div v-if="error" class="error-message">{{ error }}</div>

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
      </div>
    </div>

    <!-- 空目录提示 -->
    <div v-if="!loading && currentDir && currentDir.items.length === 0" class="empty-dir">
      空目录
    </div>

    <!-- 文件预览面板 -->
    <div v-if="previewFile" class="preview-panel">
      <div class="preview-header">
        <span class="preview-title">{{ previewFile.name }}</span>
        <div class="preview-actions">
          <button class="btn btn-sm btn-secondary" @click="copyContent">复制内容</button>
          <button class="btn btn-sm btn-secondary" @click="closePreview">关闭</button>
        </div>
      </div>
      <div v-if="previewLoading" class="preview-loading">
        <span class="spinner"></span>
      </div>
      <pre v-else class="preview-content"><code :class="previewLanguage" v-html="highlightedContent"></code></pre>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
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
  previewLoading.value = true

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

function closePreview() {
  previewFile.value = null
  previewContent.value = ''
}

async function copyContent() {
  if (previewContent.value) {
    try {
      await navigator.clipboard.writeText(previewContent.value)
      alert('已复制到剪贴板')
    } catch (e) {
      alert('复制失败')
    }
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
  grid-template-columns: 32px 1fr 80px 100px;
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

/* 预览面板 */
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

/* 响应式 */
@media (max-width: 480px) {
  .file-item {
    grid-template-columns: 28px 1fr 60px;
  }

  .file-time {
    display: none;
  }
}
</style>
