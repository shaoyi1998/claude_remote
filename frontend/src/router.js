import { createRouter, createWebHistory } from 'vue-router'
import Login from './views/Login.vue'
import TaskList from './views/TaskList.vue'
import TaskDetail from './views/TaskDetail.vue'
import NewTask from './views/NewTask.vue'
import Settings from './views/Settings.vue'
import Setup from './views/Setup.vue'
import FileBrowser from './views/FileBrowser.vue'
import ProxyView from './views/ProxyView.vue'

const routes = [
  {
    path: '/setup',
    name: 'Setup',
    component: Setup,
    meta: { requiresAuth: false, isSetup: true }
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'TaskList',
    component: TaskList,
    meta: { requiresAuth: true }
  },
  {
    path: '/task/:id',
    name: 'TaskDetail',
    component: TaskDetail,
    meta: { requiresAuth: true }
  },
  {
    path: '/new',
    name: 'NewTask',
    component: NewTask,
    meta: { requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
    meta: { requiresAuth: true }
  },
  {
    path: '/files/:taskId?',
    name: 'FileBrowser',
    component: FileBrowser,
    meta: { requiresAuth: true }
  },
  {
    path: '/proxy',
    name: 'Proxy',
    component: ProxyView,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 检测是否在 Capacitor 环境中（APK）
function isCapacitorApp() {
  return typeof window !== 'undefined' &&
    (window.Capacitor?.isNativePlatform() ||
     window.location.protocol === 'capacitor:' ||
     document.documentElement.getAttribute('data-capacitor') === 'true')
}

// 检测是否需要服务器配置
function needsServerSetup() {
  // 只在 APK 环境中检查
  if (!isCapacitorApp()) return false

  // 检查是否已配置服务器地址
  const serverHost = localStorage.getItem('serverHost')
  return !serverHost
}

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')

  // APK 环境首次启动，跳转到配置页面
  if (needsServerSetup() && to.path !== '/setup') {
    next('/setup')
    return
  }

  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else if (to.path === '/setup' && !needsServerSetup()) {
    // 已配置服务器，跳转到登录
    next('/login')
  } else {
    next()
  }
})

export default router
