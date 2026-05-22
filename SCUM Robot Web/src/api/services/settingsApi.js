/**
 * 系统设置API服务
 * 提供系统配置的CRUD操作
 */
import apiClient, { retryRequest } from '../client.js'
import { API_ENDPOINTS } from '../config.js'
import { authApi } from './authApi.js'

/**
 * 系统设置API类
 */
export class SettingsApi {
  /**
   * 获取所有系统设置
   * @param {Object} params - 查询参数
   * @param {string} params.category - 按分类筛选
   * @param {string} params.search - 搜索关键词
   * @returns {Promise<Object>} 设置列表
   */
  async getAllSettings(params = {}) {
    try {
      const response = await retryRequest(() =>
        apiClient.get(API_ENDPOINTS.SETTINGS.GET_ALL, {
          params,
          headers: authApi.getAuthHeaders(),
        }),
      )

      const responseData = response.data

      return {
        success: responseData.success || true,
        data: responseData.data || [],
        message: responseData.message || '获取系统设置成功',
      }
    } catch (error) {
      console.error('[SettingsApi] Get all settings failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取系统设置失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 按分类获取系统设置
   * @param {string} category - 设置分类
   * @returns {Promise<Object>} 分类设置列表
   */
  async getSettingsByCategory(category) {
    try {
      const url = API_ENDPOINTS.SETTINGS.GET_BY_CATEGORY.replace('{category}', category)
      const response = await retryRequest(() =>
        apiClient.get(url, {
          headers: authApi.getAuthHeaders(),
        }),
      )

      const responseData = response.data

      return {
        success: responseData.success || true,
        data: responseData.data || [],
        message: responseData.message || `获取${category}分类设置成功`,
      }
    } catch (error) {
      console.error('[SettingsApi] Get settings by category failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取分类设置失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 获取单个设置项
   * @param {string} key - 设置键名
   * @returns {Promise<Object>} 设置项详情
   */
  async getSetting(key) {
    try {
      const url = API_ENDPOINTS.SETTINGS.GET_BY_KEY.replace('{key}', key)
      const response = await retryRequest(() =>
        apiClient.get(url, {
          headers: authApi.getAuthHeaders(),
        }),
      )

      const responseData = response.data

      return {
        success: responseData.success || true,
        data: responseData.data,
        message: responseData.message || '获取设置项成功',
      }
    } catch (error) {
      console.error('[SettingsApi] Get setting failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取设置项失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 更新单个设置项
   * @param {string} key - 设置键名
   * @param {any} value - 设置值
   * @returns {Promise<Object>} 更新结果
   */
  async updateSetting(key, value) {
    try {
      const url = API_ENDPOINTS.SETTINGS.UPDATE_SETTING.replace('{key}', key)
      const response = await retryRequest(() =>
        apiClient.put(
          url,
          { value },
          {
            headers: authApi.getAuthHeaders(),
          },
        ),
      )

      const responseData = response.data

      return {
        success: responseData.success || true,
        data: responseData.data,
        message: responseData.message || '设置更新成功',
      }
    } catch (error) {
      console.error('[SettingsApi] Update setting failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '设置更新失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 批量更新设置
   * @param {Object} settings - 设置键值对
   * @returns {Promise<Object>} 更新结果
   */
  async updateBatchSettings(settings) {
    try {
      const response = await retryRequest(() =>
        apiClient.put(
          API_ENDPOINTS.SETTINGS.UPDATE_BATCH,
          { settings },
          {
            headers: authApi.getAuthHeaders(),
          },
        ),
      )

      const responseData = response.data

      return {
        success: responseData.success || true,
        data: responseData.data,
        message: responseData.message || '批量设置更新成功',
      }
    } catch (error) {
      console.error('[SettingsApi] Update batch settings failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '批量设置更新失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 重置单个设置项到默认值
   * @param {string} key - 设置键名
   * @returns {Promise<Object>} 重置结果
   */
  async resetSetting(key) {
    try {
      const url = API_ENDPOINTS.SETTINGS.RESET_SETTING.replace('{key}', key)
      const response = await retryRequest(() =>
        apiClient.post(url, {}, {
          headers: authApi.getAuthHeaders(),
        }),
      )

      const responseData = response.data

      return {
        success: responseData.success || true,
        data: responseData.data,
        message: responseData.message || '设置重置成功',
      }
    } catch (error) {
      console.error('[SettingsApi] Reset setting failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '设置重置失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 重置分类下的所有设置到默认值
   * @param {string} category - 设置分类
   * @returns {Promise<Object>} 重置结果
   */
  async resetCategorySettings(category) {
    try {
      const url = API_ENDPOINTS.SETTINGS.RESET_CATEGORY.replace('{category}', category)
      const response = await retryRequest(() =>
        apiClient.post(url, {}, {
          headers: authApi.getAuthHeaders(),
        }),
      )

      const responseData = response.data

      return {
        success: responseData.success || true,
        data: responseData.data,
        message: responseData.message || `${category}分类设置重置成功`,
      }
    } catch (error) {
      console.error('[SettingsApi] Reset category settings failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '分类设置重置失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 重置所有设置到默认值
   * @returns {Promise<Object>} 重置结果
   */
  async resetAllSettings() {
    try {
      const response = await retryRequest(() =>
        apiClient.post(API_ENDPOINTS.SETTINGS.RESET_ALL, {}, {
          headers: authApi.getAuthHeaders(),
        }),
      )

      const responseData = response.data

      return {
        success: responseData.success || true,
        data: responseData.data,
        message: responseData.message || '所有设置重置成功',
      }
    } catch (error) {
      console.error('[SettingsApi] Reset all settings failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '重置所有设置失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 导出系统设置
   * @param {Object} params - 导出参数
   * @param {string} params.format - 导出格式 (json, yaml)
   * @param {string[]} params.categories - 要导出的分类
   * @returns {Promise<Object>} 导出结果
   */
  async exportSettings(params = {}) {
    try {
      const response = await retryRequest(() =>
        apiClient.get(API_ENDPOINTS.SETTINGS.EXPORT, {
          params,
          headers: authApi.getAuthHeaders(),
        }),
      )

      const responseData = response.data

      return {
        success: responseData.success || true,
        data: responseData.data,
        message: responseData.message || '设置导出成功',
      }
    } catch (error) {
      console.error('[SettingsApi] Export settings failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '设置导出失败',
        error: error.response?.data,
      }
    }
  }
}

// 创建并导出API实例
export const settingsApi = new SettingsApi()
