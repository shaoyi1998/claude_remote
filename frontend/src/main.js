import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './style.css'

// 检测 Capacitor 环境并标记
if (typeof window !== 'undefined') {
  // 延迟检测，等待 Capacitor 加载
  setTimeout(() => {
    if (window.Capacitor?.isNativePlatform?.() ||
        window.location.protocol === 'capacitor:' ||
        window.location.hostname === 'localhost' && window.location.port === '') {
      document.documentElement.setAttribute('data-capacitor', 'true')
    }
  }, 100)
}

const app = createApp(App)
app.use(router)
app.mount('#app')
