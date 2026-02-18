/**
 * 平台检测工具
 */

/**
 * 检测是否在 Capacitor 环境中（APK）
 */
export function isCapacitorApp() {
  return typeof window !== 'undefined' &&
    (window.Capacitor?.isNativePlatform() ||
     window.location.protocol === 'capacitor:' ||
     document.documentElement.getAttribute('data-capacitor') === 'true')
}

/**
 * 检测是否需要服务器配置
 * 只有 APK 需要配置服务器地址
 */
export function needsServerConfig() {
  return isCapacitorApp()
}
