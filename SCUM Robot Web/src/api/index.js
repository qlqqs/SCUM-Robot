/**
 * API服务统一导出
 */

// 导出配置
export * from './config.js'

// 导出客户端
export { default as apiClient, retryRequest } from './client.js'

// 导出服务
export * from './services/authApi.js'
export * from './services/usersApi.js'
export * from './services/itemsApi.js'
export * from './services/adminApi.js'
export * from './services/signinApi.js'
export * from './services/vipApi.js'
export * from './services/characterApi.js'
export * from './services/robotApi.js'
export * from './services/settingsApi.js'

// 统一的API服务对象
export const api = {
  // 认证相关
  auth: null,

  // 用户管理
  users: null,

  // 类目相关
  categories: null,
  subcategories: null,

  // 物品相关
  items: null,

  // 游戏功能
  robot: null,
  signin: null,
  vip: null,
  character: null,

  // 管理员功能
  admin: null,

  // 系统设置
  settings: null,
}

// 动态导入API服务（避免循环依赖）
import('./services/authApi.js').then((module) => {
  api.auth = module.authApi
})

import('./services/usersApi.js').then((module) => {
  api.users = module.usersApi
})

import('./services/itemsApi.js').then((module) => {
  api.items = module.itemsApi
  api.categories = module.categoriesApi
  api.subcategories = module.subcategoriesApi
})

import('./services/robotApi.js').then((module) => {
  api.robot = module.robotApi
})

import('./services/signinApi.js').then((module) => {
  api.signin = module.signinApi
})

import('./services/vipApi.js').then((module) => {
  api.vip = module.vipApi
})

import('./services/characterApi.js').then((module) => {
  api.character = module.characterApi
})

import('./services/settingsApi.js').then((module) => {
  api.settings = module.settingsApi
})

import('./services/adminApi.js').then((module) => {
  api.admin = module.adminApi
})

/**
 * 初始化API服务
 * @returns {Promise<boolean>} 初始化是否成功
 */
export async function initializeApi() {
  try {
    console.log('[API] Initializing API services...')
    console.log('[API] API services initialized successfully')
    return true
  } catch (error) {
    console.error('[API] Failed to initialize API services:', error)
    return false
  }
}

/**
 * 获取API服务状态
 * @returns {Promise<Object>} 服务状态信息
 */
export async function getApiStatus() {
  try {
    const { robotApi } = await import('./services/robotApi.js')

    const [robotStatus] = await Promise.allSettled([
      robotApi
        .getStatus()
        .then(() => true)
        .catch(() => false),
    ])

    return {
      robot: robotStatus.status === 'fulfilled' ? robotStatus.value : false,
      timestamp: new Date().toISOString(),
    }
  } catch (error) {
    console.error('[API] Failed to get API status:', error)
    return {
      robot: false,
      error: error.message,
      timestamp: new Date().toISOString(),
    }
  }
}
