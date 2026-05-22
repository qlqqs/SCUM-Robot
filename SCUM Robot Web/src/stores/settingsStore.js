import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { settingsApi } from '@/api/services/settingsApi.js'

/**
 * 系统设置分类定义
 */
export const SETTING_CATEGORIES = {
  SYSTEM: {
    id: 'system',
    name: '系统配置',
    description: '基础系统参数配置',
    icon: 'fas fa-cogs',
  },
  API: {
    id: 'api',
    name: 'API配置',
    description: 'API服务相关配置',
    icon: 'fas fa-plug',
  },
  SECURITY: {
    id: 'security',
    name: '安全配置',
    description: '安全和权限相关配置',
    icon: 'fas fa-shield-alt',
  },
  GAME: {
    id: 'game',
    name: '游戏配置',
    description: '游戏功能相关配置',
    icon: 'fas fa-gamepad',
  },
  USER: {
    id: 'user',
    name: '用户配置',
    description: '用户管理和权限相关配置',
    icon: 'fas fa-users',
  },
  NOTIFICATION: {
    id: 'notification',
    name: '通知配置',
    description: '通知和消息相关配置',
    icon: 'fas fa-bell',
  },
  PERFORMANCE: {
    id: 'performance',
    name: '性能配置',
    description: '性能优化相关配置',
    icon: 'fas fa-tachometer-alt',
  },
}

/**
 * 系统设置数据类型定义
 */
export const SETTING_TYPES = {
  STRING: 'string',
  NUMBER: 'number',
  BOOLEAN: 'boolean',
  SELECT: 'select',
  MULTI_SELECT: 'multi_select',
  JSON: 'json',
  PASSWORD: 'password',
  URL: 'url',
  EMAIL: 'email',
  COLOR: 'color',
  TEXTAREA: 'textarea',
}

export const useSettingsStore = defineStore('settingsStore', () => {
  // 状态
  const settings = ref({})
  const categories = ref(Object.values(SETTING_CATEGORIES))

  // 加载状态
  const loading = ref({
    settings: false,
    updating: false,
    resetting: false,
  })

  // 错误状态
  const errors = ref({
    settings: null,
    updating: null,
    resetting: null,
  })

  // 计算属性
  const isLoading = computed(() => Object.values(loading.value).some(Boolean))
  const hasErrors = computed(() => Object.values(errors.value).some(Boolean))

  // 按分类获取设置
  const getSettingsByCategory = computed(() => (categoryId) => {
    return Object.values(settings.value).filter((setting) => setting.category === categoryId)
  })

  // 获取设置值
  const getSettingValue = computed(() => (key) => {
    const setting = settings.value[key]
    return setting ? setting.value : null
  })

  // 获取设置项
  const getSetting = computed(() => (key) => {
    return settings.value[key] || null
  })

  // 清除错误
  const clearError = (type) => {
    if (type) {
      errors.value[type] = null
    } else {
      Object.keys(errors.value).forEach((key) => {
        errors.value[key] = null
      })
    }
  }

  // 加载所有设置
  const loadSettings = async (params = {}) => {
    loading.value.settings = true
    errors.value.settings = null

    try {
      console.log('[SettingsStore] Loading settings...')
      const response = await settingsApi.getAllSettings(params)

      if (response.success && response.data) {
        // 将设置数组转换为键值对对象
        const settingsMap = {}
        response.data.forEach((setting) => {
          settingsMap[setting.key] = setting
        })
        settings.value = settingsMap
        console.log(
          '[SettingsStore] Settings loaded successfully:',
          Object.keys(settingsMap).length,
        )
      } else {
        throw new Error(response.message || '加载设置失败')
      }
    } catch (error) {
      console.error('[SettingsStore] Failed to load settings:', error)
      errors.value.settings = error.message || '加载设置失败'
      throw error
    } finally {
      loading.value.settings = false
    }
  }

  // 按分类加载设置
  const loadSettingsByCategory = async (category) => {
    loading.value.settings = true
    errors.value.settings = null

    try {
      console.log('[SettingsStore] Loading settings for category:', category)
      const response = await settingsApi.getSettingsByCategory(category)

      if (response.success && response.data) {
        // 更新对应分类的设置
        response.data.forEach((setting) => {
          settings.value[setting.key] = setting
        })
        console.log('[SettingsStore] Category settings loaded successfully:', category)
      } else {
        throw new Error(response.message || '加载分类设置失败')
      }
    } catch (error) {
      console.error('[SettingsStore] Failed to load category settings:', error)
      errors.value.settings = error.message || '加载分类设置失败'
      throw error
    } finally {
      loading.value.settings = false
    }
  }

  // 更新单个设置
  const updateSetting = async (key, value) => {
    loading.value.updating = true
    errors.value.updating = null

    try {
      console.log('[SettingsStore] Updating setting:', key, value)
      const response = await settingsApi.updateSetting(key, value)

      if (response.success) {
        // 更新本地设置
        if (settings.value[key]) {
          settings.value[key].value = value
          settings.value[key].updated_at = new Date().toISOString()
        }
        console.log('[SettingsStore] Setting updated successfully:', key)
        return response
      } else {
        throw new Error(response.message || '更新设置失败')
      }
    } catch (error) {
      console.error('[SettingsStore] Failed to update setting:', error)
      errors.value.updating = error.message || '更新设置失败'
      throw error
    } finally {
      loading.value.updating = false
    }
  }

  // 批量更新设置
  const updateBatchSettings = async (settingsData) => {
    loading.value.updating = true
    errors.value.updating = null

    try {
      console.log('[SettingsStore] Updating batch settings:', Object.keys(settingsData))
      const response = await settingsApi.updateBatchSettings(settingsData)

      if (response.success) {
        // 更新本地设置
        Object.entries(settingsData).forEach(([key, value]) => {
          if (settings.value[key]) {
            settings.value[key].value = value
            settings.value[key].updated_at = new Date().toISOString()
          }
        })
        console.log('[SettingsStore] Batch settings updated successfully')
        return response
      } else {
        throw new Error(response.message || '批量更新设置失败')
      }
    } catch (error) {
      console.error('[SettingsStore] Failed to update batch settings:', error)
      errors.value.updating = error.message || '批量更新设置失败'
      throw error
    } finally {
      loading.value.updating = false
    }
  }

  // 重置单个设置
  const resetSetting = async (key) => {
    loading.value.resetting = true
    errors.value.resetting = null

    try {
      console.log('[SettingsStore] Resetting setting:', key)
      const response = await settingsApi.resetSetting(key)

      if (response.success && response.data) {
        // 更新本地设置为默认值
        settings.value[key] = response.data
        console.log('[SettingsStore] Setting reset successfully:', key)
        return response
      } else {
        throw new Error(response.message || '重置设置失败')
      }
    } catch (error) {
      console.error('[SettingsStore] Failed to reset setting:', error)
      errors.value.resetting = error.message || '重置设置失败'
      throw error
    } finally {
      loading.value.resetting = false
    }
  }

  // 重置分类设置
  const resetCategorySettings = async (category) => {
    loading.value.resetting = true
    errors.value.resetting = null

    try {
      console.log('[SettingsStore] Resetting category settings:', category)
      const response = await settingsApi.resetCategorySettings(category)

      if (response.success) {
        // 重新加载该分类的设置
        await loadSettingsByCategory(category)
        console.log('[SettingsStore] Category settings reset successfully:', category)
        return response
      } else {
        throw new Error(response.message || '重置分类设置失败')
      }
    } catch (error) {
      console.error('[SettingsStore] Failed to reset category settings:', error)
      errors.value.resetting = error.message || '重置分类设置失败'
      throw error
    } finally {
      loading.value.resetting = false
    }
  }

  // 重置所有设置
  const resetAllSettings = async () => {
    loading.value.resetting = true
    errors.value.resetting = null

    try {
      console.log('[SettingsStore] Resetting all settings')
      const response = await settingsApi.resetAllSettings()

      if (response.success) {
        // 重新加载所有设置
        await loadSettings()
        console.log('[SettingsStore] All settings reset successfully')
        return response
      } else {
        throw new Error(response.message || '重置所有设置失败')
      }
    } catch (error) {
      console.error('[SettingsStore] Failed to reset all settings:', error)
      errors.value.resetting = error.message || '重置所有设置失败'
      throw error
    } finally {
      loading.value.resetting = false
    }
  }

  // 导出设置
  const exportSettings = async (params = {}) => {
    try {
      console.log('[SettingsStore] Exporting settings:', params)
      const response = await settingsApi.exportSettings(params)

      if (response.success) {
        console.log('[SettingsStore] Settings exported successfully')
        return response
      } else {
        throw new Error(response.message || '导出设置失败')
      }
    } catch (error) {
      console.error('[SettingsStore] Failed to export settings:', error)
      throw error
    }
  }

  return {
    // 状态
    settings,
    categories,
    loading,
    errors,

    // 计算属性
    isLoading,
    hasErrors,
    getSettingsByCategory,
    getSettingValue,
    getSetting,

    // 方法
    clearError,
    loadSettings,
    loadSettingsByCategory,
    updateSetting,
    updateBatchSettings,
    resetSetting,
    resetCategorySettings,
    resetAllSettings,
    exportSettings,
  }
})
