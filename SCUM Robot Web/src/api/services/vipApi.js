/**
 * VIP系统API服务
 */
import apiClient, { retryRequest } from '../client.js'
import { API_ENDPOINTS } from '../config.js'

/**
 * VIP API类
 */
class VipApi {
  /**
   * 获取用户VIP状态
   * @returns {Promise<Object>} API响应
   */
  async getUserVipStatus() {
    try {
      const response = await retryRequest(() => apiClient.get(API_ENDPOINTS.VIP.STATUS))

      return {
        success: true,
        data: response.data.data,
        message: response.data.message || '获取VIP状态成功',
      }
    } catch (error) {
      console.error('[VipApi] Get user VIP status failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取VIP状态失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 获取所有VIP配置
   * @returns {Promise<Object>} API响应
   */
  async getAllVipConfigs() {
    try {
      const response = await retryRequest(() => apiClient.get(API_ENDPOINTS.VIP.CONFIGS))

      return {
        success: true,
        data: response.data.data || [],
        message: response.data.message || '获取VIP配置列表成功',
      }
    } catch (error) {
      console.error('[VipApi] Get all VIP configs failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取VIP配置列表失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 获取指定VIP配置
   * @param {number} level - VIP等级
   * @returns {Promise<Object>} API响应
   */
  async getVipConfig(level) {
    try {
      const url = API_ENDPOINTS.VIP.CONFIG_BY_LEVEL.replace('{level}', level)
      const response = await retryRequest(() => apiClient.get(url))

      return {
        success: true,
        data: response.data.data,
        message: response.data.message || '获取VIP配置成功',
      }
    } catch (error) {
      console.error('[VipApi] Get VIP config failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取VIP配置失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 创建VIP配置
   * @param {Object} configData - VIP配置数据
   * @returns {Promise<Object>} API响应
   */
  async createVipConfig(configData) {
    try {
      const response = await retryRequest(() =>
        apiClient.post(API_ENDPOINTS.VIP.CREATE_CONFIG, configData),
      )

      return {
        success: true,
        data: response.data.data,
        message: response.data.message || 'VIP配置创建成功',
      }
    } catch (error) {
      console.error('[VipApi] Create VIP config failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || 'VIP配置创建失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 更新VIP配置
   * @param {number} level - VIP等级
   * @param {Object} configData - VIP配置数据
   * @returns {Promise<Object>} API响应
   */
  async updateVipConfig(level, configData) {
    try {
      const url = API_ENDPOINTS.VIP.UPDATE_CONFIG.replace('{level}', level)
      const response = await retryRequest(() => apiClient.put(url, configData))

      return {
        success: true,
        data: response.data.data,
        message: response.data.message || 'VIP配置更新成功',
      }
    } catch (error) {
      console.error('[VipApi] Update VIP config failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || 'VIP配置更新失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 删除VIP配置
   * @param {number} level - VIP等级
   * @returns {Promise<Object>} API响应
   */
  async deleteVipConfig(level) {
    try {
      const url = API_ENDPOINTS.VIP.DELETE_CONFIG.replace('{level}', level)
      const response = await retryRequest(() => apiClient.delete(url))

      return {
        success: true,
        message: response.data.message || 'VIP配置删除成功',
      }
    } catch (error) {
      console.error('[VipApi] Delete VIP config failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || 'VIP配置删除失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 升级用户VIP
   * @param {Object} upgradeData - 升级数据
   * @returns {Promise<Object>} API响应
   */
  async upgradeUserVip(upgradeData) {
    try {
      const response = await retryRequest(() =>
        apiClient.post(API_ENDPOINTS.VIP.UPGRADE_USER, upgradeData),
      )

      return {
        success: true,
        data: response.data.data,
        message: response.data.message || '用户VIP升级成功',
      }
    } catch (error) {
      console.error('[VipApi] Upgrade user VIP failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '用户VIP升级失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 批量升级VIP
   * @param {Object} batchData - 批量升级数据
   * @returns {Promise<Object>} API响应
   */
  async batchUpgradeVip(batchData) {
    try {
      const response = await retryRequest(() =>
        apiClient.post(API_ENDPOINTS.VIP.BATCH_UPGRADE, batchData),
      )

      return {
        success: true,
        data: response.data.data,
        message: response.data.message || '批量VIP升级成功',
      }
    } catch (error) {
      console.error('[VipApi] Batch upgrade VIP failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '批量VIP升级失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 获取VIP统计
   * @param {number} minLevel - 最低VIP等级
   * @returns {Promise<Object>} API响应
   */
  async getVipStatistics(minLevel = 2) {
    try {
      const response = await retryRequest(() =>
        apiClient.get(API_ENDPOINTS.VIP.STATISTICS, {
          params: { min_level: minLevel },
        }),
      )

      return {
        success: true,
        data: response.data.data,
        message: response.data.message || '获取VIP统计成功',
      }
    } catch (error) {
      console.error('[VipApi] Get VIP statistics failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取VIP统计失败',
        error: error.response?.data,
      }
    }
  }
}

// 创建实例
export const vipApi = new VipApi()

// 默认导出
export default vipApi
