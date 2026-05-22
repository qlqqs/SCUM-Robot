/**
 * 签到系统API服务
 */
import apiClient, { retryRequest } from '../client.js'
import { API_ENDPOINTS } from '../config.js'

/**
 * 签到API类
 */
class SigninApi {
  /**
   * 获取签到状态
   * @returns {Promise<Object>} API响应
   */
  async getStatus() {
    try {
      const response = await retryRequest(() => apiClient.get(API_ENDPOINTS.SIGNIN.STATUS))

      return {
        success: true,
        data: response.data.data,
        message: '获取签到状态成功',
      }
    } catch (error) {
      console.error('[SigninApi] Get status failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取签到状态失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 每日签到
   * @returns {Promise<Object>} API响应
   */
  async dailySignin() {
    try {
      const response = await retryRequest(() => apiClient.post(API_ENDPOINTS.SIGNIN.DAILY))

      return {
        success: true,
        data: response.data.data,
        message: '签到成功',
      }
    } catch (error) {
      console.error('[SigninApi] Daily signin failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '签到失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 获取签到历史
   * @param {number} page - 页码
   * @param {number} pageSize - 每页数量
   * @param {string} startDate - 开始日期 (YYYY-MM-DD)
   * @param {string} endDate - 结束日期 (YYYY-MM-DD)
   * @returns {Promise<Object>} API响应
   */
  async getHistory(page = 1, pageSize = 20, startDate = null, endDate = null) {
    try {
      const params = { page, page_size: pageSize }
      if (startDate) params.start_date = startDate
      if (endDate) params.end_date = endDate

      const response = await retryRequest(() =>
        apiClient.get(API_ENDPOINTS.SIGNIN.HISTORY, { params })
      )

      return {
        success: true,
        data: response.data.data,
        message: '获取签到历史成功',
      }
    } catch (error) {
      console.error('[SigninApi] Get history failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取签到历史失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 获取签到排行榜
   * @param {string} type - 排行榜类型 ('consecutive' | 'total')
   * @param {number} limit - 返回数量限制
   * @returns {Promise<Object>} API响应
   */
  async getLeaderboard(type = 'consecutive', limit = 50) {
    try {
      const params = { type, limit }
      const response = await retryRequest(() =>
        apiClient.get(API_ENDPOINTS.SIGNIN.LEADERBOARD, { params })
      )

      return {
        success: true,
        data: response.data.data,
        message: '获取签到排行榜成功',
      }
    } catch (error) {
      console.error('[SigninApi] Get leaderboard failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取签到排行榜失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 管理员 - 获取签到统计
   * @param {string} date - 查询日期 (YYYY-MM-DD)
   * @returns {Promise<Object>} API响应
   */
  async getAdminStats(date = null) {
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
      console.error('[SigninApi] Get admin stats failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取签到统计失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 管理员 - 重置用户签到状态
   * @param {number} userId - 用户ID
   * @param {string} reason - 重置原因
   * @returns {Promise<Object>} API响应
   */
  async resetUserSignin(userId, reason = '') {
    try {
      const response = await retryRequest(() =>
        apiClient.post(`/api/v1/signin/admin/reset/${userId}`, { reason })
      )

      return {
        success: true,
        data: response.data.data,
        message: '重置签到状态成功',
      }
    } catch (error) {
      console.error('[SigninApi] Reset user signin failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '重置签到状态失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 管理员 - 批量重置签到状态
   * @param {Array<number>} userIds - 用户ID列表
   * @param {string} reason - 重置原因
   * @returns {Promise<Object>} API响应
   */
  async batchResetSignin(userIds, reason = '') {
    try {
      const response = await retryRequest(() =>
        apiClient.post('/api/v1/signin/admin/batch-reset', { user_ids: userIds, reason })
      )

      return {
        success: true,
        data: response.data.data,
        message: '批量重置签到状态成功',
      }
    } catch (error) {
      console.error('[SigninApi] Batch reset signin failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '批量重置签到状态失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 管理员 - 更新签到配置
   * @param {Object} config - 签到配置
   * @returns {Promise<Object>} API响应
   */
  async updateConfig(config) {
    try {
      const response = await retryRequest(() =>
        apiClient.put('/api/v1/signin/admin/config', config)
      )

      return {
        success: true,
        data: response.data.data,
        message: '更新签到配置成功',
      }
    } catch (error) {
      console.error('[SigninApi] Update config failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '更新签到配置失败',
        error: error.response?.data,
      }
    }
  }
}

// 创建实例
export const signinApi = new SigninApi()

// 默认导出
export default signinApi
