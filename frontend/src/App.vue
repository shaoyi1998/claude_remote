<template>
  <router-view />
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { syncFromServer } from './stores/shortcuts'

// 修复移动端 100vh 问题
function setVH() {
  const vh = window.innerHeight * 0.01
  document.documentElement.style.setProperty('--vh', `${vh}px`)
}

onMounted(async () => {
  setVH()
  window.addEventListener('resize', setVH)

  // 应用启动时从服务器同步快捷键配置（如果已登录）
  await syncFromServer()
})

onUnmounted(() => {
  window.removeEventListener('resize', setVH)
})
</script>
