/**
 * 管理员API服务
 */
import apiClient, { retryRequest } from '../client.js'
import { API_ENDPOINTS } from '../config.js'

/**
 * 管理员API类
 */
class AdminApi {
  /**
   * 获取系统统计信息
   * @returns {Promise<Object>} API响应
   */
  async getSystemStats() {
    try {
      const response = await retryRequest(() => apiClient.get(API_ENDPOINTS.ADMIN.STATS))

      return {
        success: true,
        data: response.data.data,
        message: '获取系统统计成功',
      }
    } catch (error) {
      console.error('[AdminApi] Get system stats failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取系统统计失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 获取签到统计信息
   * @param {string} date - 查询日期，格式"YYYY-MM-DD"
   * @returns {Promise<Object>} API响应
   */
  async getSigninStats(date = null) {
    try {
      const params = date ? { date } : {}
      const response = await retryRequest(() =>
        apiClient.get(API_ENDPOINTS.ADMIN.SIGNIN_STATS, { params })
      )

      return {
        success: true,
        data: response.data.data,
        message: '获取签到统计成功',
      }
    } catch (error) {
      console.error('[AdminApi] Get signin stats failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取签到统计失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 获取VIP统计信息
   * @returns {Promise<Object>} API响应
   */
  async getVipStats() {
    try {
      const response = await retryRequest(() => apiClient.get(API_ENDPOINTS.ADMIN.VIP_STATS))

      return {
        success: true,
        data: response.data.data,
        message: '获取VIP统计成功',
      }
    } catch (error) {
      console.error('[AdminApi] Get VIP stats failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取VIP统计失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 获取数据库状态
   * @returns {Promise<Object>} API响应
   */
  async getDatabaseStatus() {
    try {
      const response = await retryRequest(() => apiClient.get(API_ENDPOINTS.ADMIN.DATABASE_STATUS))

      return {
        success: true,
        data: response.data.data,
        message: '获取数据库状态成功',
      }
    } catch (error) {
      console.error('[AdminApi] Get database status failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取数据库状态失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 获取综合统计信息
   * @returns {Promise<Object>} 综合统计数据
   */
  async getComprehensiveStats() {
    try {
      // 并行获取所有统计信息
      const [systemStats, signinStats, vipStats, dbStatus] = await Promise.allSettled([
        this.getSystemStats(),
        this.getSigninStats(),
        this.getVipStats(),
        this.getDatabaseStatus(),
      ])

      // 处理结果
      const result = {
        success: true,
        data: {
          system: systemStats.status === 'fulfilled' ? systemStats.value.data : null,
          signin: signinStats.status === 'fulfilled' ? signinStats.value.data : null,
          vip: vipStats.status === 'fulfilled' ? vipStats.value.data : null,
          database: dbStatus.status === 'fulfilled' ? dbStatus.value.data : null,
        },
        errors: [],
      }

      // 收集错误信息
      if (systemStats.status === 'rejected') {
        result.errors.push({ type: 'system', error: systemStats.reason })
      }
      if (signinStats.status === 'rejected') {
        result.errors.push({ type: 'signin', error: signinStats.reason })
      }
      if (vipStats.status === 'rejected') {
        result.errors.push({ type: 'vip', error: vipStats.reason })
      }
      if (dbStatus.status === 'rejected') {
        result.errors.push({ type: 'database', error: dbStatus.reason })
      }

      return result
    } catch (error) {
      console.error('[AdminApi] Get comprehensive stats failed:', error)
      throw {
        success: false,
        message: '获取综合统计失败',
        error: error,
      }
    }
  }
}

// 创建实例
export const adminApi = new AdminApi()

// 默认导出
export default adminApi
