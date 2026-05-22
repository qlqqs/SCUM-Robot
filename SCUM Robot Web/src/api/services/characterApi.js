/**
 * 人物能力系统API服务
 */
import apiClient, { retryRequest } from '../client.js'
import { API_ENDPOINTS } from '../config.js'

/**
 * 人物能力API类
 */
class CharacterApi {
  /**
   * 获取当前用户人物能力
   * @returns {Promise<Object>} API响应
   */
  async getStats() {
    try {
      const response = await retryRequest(() => apiClient.get(API_ENDPOINTS.CHARACTER.STATS))

      return {
        success: true,
        data: response.data.data,
        message: '获取人物能力成功',
      }
    } catch (error) {
      console.error('[CharacterApi] Get stats failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取人物能力失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 根据Steam ID获取人物能力
   * @param {string} steamId - Steam ID
   * @returns {Promise<Object>} API响应
   */
  async getStatsBySteam(steamId) {
    try {
      const url = API_ENDPOINTS.CHARACTER.STATS_BY_STEAM.replace('{steam_id}', steamId)
      const response = await retryRequest(() => apiClient.get(url))

      return {
        success: true,
        data: response.data.data,
        message: '获取人物能力成功',
      }
    } catch (error) {
      console.error('[CharacterApi] Get stats by steam failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取人物能力失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 获取能力排行榜
   * @param {string} type - 排行榜类型 ('strength' | 'stamina' | 'intelligence' | 'agility' | 'total')
   * @param {number} limit - 返回数量限制
   * @returns {Promise<Object>} API响应
   */
  async getLeaderboard(type = 'total', limit = 50) {
    try {
      const params = { type, limit }
      const response = await retryRequest(() =>
        apiClient.get(API_ENDPOINTS.CHARACTER.LEADERBOARD, { params })
      )

      return {
        success: true,
        data: response.data.data,
        message: '获取能力排行榜成功',
      }
    } catch (error) {
      console.error('[CharacterApi] Get leaderboard failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取能力排行榜失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 获取能力统计摘要
   * @returns {Promise<Object>} API响应
   */
  async getSummary() {
    try {
      const response = await retryRequest(() => apiClient.get(API_ENDPOINTS.CHARACTER.SUMMARY))

      return {
        success: true,
        data: response.data.data,
        message: '获取能力统计成功',
      }
    } catch (error) {
      console.error('[CharacterApi] Get summary failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取能力统计失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 管理员 - 更新用户能力数据
   * @param {string} steamId - Steam ID
   * @param {Object} stats - 能力数据
   * @param {string} reason - 更新原因
   * @returns {Promise<Object>} API响应
   */
  async adminUpdateStats(steamId, stats, reason = '') {
    try {
      const url = API_ENDPOINTS.CHARACTER.ADMIN_UPDATE_STATS.replace('{steam_id}', steamId)
      const response = await retryRequest(() =>
        apiClient.put(url, { ...stats, reason })
      )

      return {
        success: true,
        data: response.data.data,
        message: '更新人物能力成功',
      }
    } catch (error) {
      console.error('[CharacterApi] Admin update stats failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '更新人物能力失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 管理员 - 同步游戏数据
   * @param {Array<string>} steamIds - Steam ID列表 (可选)
   * @returns {Promise<Object>} API响应
   */
  async adminSyncData(steamIds = null) {
    try {
      const data = steamIds ? { steam_ids: steamIds } : {}
      const response = await retryRequest(() =>
        apiClient.post(API_ENDPOINTS.CHARACTER.ADMIN_SYNC, data)
      )

      return {
        success: true,
        data: response.data.data,
        message: '同步游戏数据成功',
      }
    } catch (error) {
      console.error('[CharacterApi] Admin sync data failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '同步游戏数据失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 管理员 - 获取能力统计信息
   * @param {string} steamId - Steam ID (可选)
   * @returns {Promise<Object>} API响应
   */
  async getAdminStats(steamId = null) {
    try {
      const url = steamId 
        ? `/api/v1/character/admin/stats/${steamId}`
        : '/api/v1/character/admin/stats'
      
      const response = await retryRequest(() => apiClient.get(url))

      return {
        success: true,
        data: response.data.data,
        message: '获取能力统计成功',
      }
    } catch (error) {
      console.error('[CharacterApi] Get admin stats failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取能力统计失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 管理员 - 批量更新能力数据
   * @param {Array<Object>} updates - 更新列表
   * @returns {Promise<Object>} API响应
   */
  async batchUpdateStats(updates) {
    try {
      const response = await retryRequest(() =>
        apiClient.post('/api/v1/character/admin/batch-update', { updates })
      )

      return {
        success: true,
        data: response.data.data,
        message: '批量更新能力数据成功',
      }
    } catch (error) {
      console.error('[CharacterApi] Batch update stats failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '批量更新能力数据失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 管理员 - 重置用户能力数据
   * @param {string} steamId - Steam ID
   * @param {string} reason - 重置原因
   * @returns {Promise<Object>} API响应
   */
  async resetStats(steamId, reason = '') {
    try {
      const response = await retryRequest(() =>
        apiClient.post(`/api/v1/character/admin/reset/${steamId}`, { reason })
      )

      return {
        success: true,
        data: response.data.data,
        message: '重置能力数据成功',
      }
    } catch (error) {
      console.error('[CharacterApi] Reset stats failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '重置能力数据失败',
        error: error.response?.data,
      }
    }
  }
}

// 创建实例
export const characterApi = new CharacterApi()

// 默认导出
export default characterApi
