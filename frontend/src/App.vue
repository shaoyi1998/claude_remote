<template>
  <router-view />
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'

// 修复移动端 100vh 问题
function setVH() {
  const vh = window.innerHeight * 0.01
  document.documentElement.style.setProperty('--vh', `${vh}px`)
}

onMounted(() => {
  setVH()
  window.addEventListener('resize', setVH)
})

onUnmounted(() => {
  window.removeEventListener('resize', setVH)
})
</script>
