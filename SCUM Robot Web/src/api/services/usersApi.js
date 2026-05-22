/**
 * 用户管理API服务
 * 提供用户信息查询、更新、管理等功能
 */
import apiClient, { retryRequest } from '../client.js'
import { API_ENDPOINTS } from '../config.js'

/**
 * 用户管理API类
 */
export class UsersApi {
  /**
   * 获取用户信息
   * @param {number} userId - 用户ID
   * @returns {Promise<Object>} 用户信息
   */
  async getUser(userId) {
    try {
      const url = API_ENDPOINTS.USERS.GET_USER.replace('{user_id}', userId)
      const response = await retryRequest(() => apiClient.get(url))

      return {
        success: true,
        data: response.data.data,
        message: '获取用户信息成功',
      }
    } catch (error) {
      console.error('[UsersApi] Get user failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取用户信息失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 更新用户信息
   * @param {number} userId - 用户ID
   * @param {Object} userData - 用户数据
   * @returns {Promise<Object>} 更新结果
   */
  async updateUser(userId, userData) {
    try {
      const url = API_ENDPOINTS.USERS.UPDATE_USER.replace('{user_id}', userId)
      const response = await retryRequest(() => apiClient.put(url, userData))

      return {
        success: true,
        data: response.data.data,
        message: '用户信息更新成功',
      }
    } catch (error) {
      console.error('[UsersApi] Update user failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '用户信息更新失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 获取用户列表
   * @param {Object} params - 查询参数
   * @param {number} params.page - 页码
   * @param {number} params.size - 每页数量
   * @param {string} params.search - 搜索关键词
   * @param {string} params.user_type - 用户类型
   * @returns {Promise<Object>} 用户列表
   */
  async listUsers(params = {}) {
    try {
      const response = await retryRequest(() =>
        apiClient.get(API_ENDPOINTS.USERS.LIST_USERS, {
          params,
        }),
      )

      return {
        success: true,
        data: response.data.data,
        pagination: response.data.pagination,
        message: '获取用户列表成功',
      }
    } catch (error) {
      console.error('[UsersApi] List users failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取用户列表失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 删除用户
   * @param {number} userId - 用户ID
   * @returns {Promise<Object>} 删除结果
   */
  async deleteUser(userId) {
    try {
      const url = API_ENDPOINTS.USERS.DELETE_USER.replace('{user_id}', userId)
      const response = await retryRequest(() => apiClient.delete(url))

      return {
        success: true,
        data: response.data,
        message: '用户删除成功',
      }
    } catch (error) {
      console.error('[UsersApi] Delete user failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '用户删除失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 更新用户权限
   * @param {number} userId - 用户ID
   * @param {Object} permissions - 权限数据
   * @param {string} permissions.user_type - 用户类型
   * @param {boolean} permissions.is_admin - 是否管理员
   * @param {boolean} permissions.is_super_admin - 是否超级管理员
   * @returns {Promise<Object>} 更新结果
   */
  async updatePermissions(userId, permissions) {
    try {
      const url = API_ENDPOINTS.USERS.UPDATE_PERMISSIONS.replace('{user_id}', userId)
      const response = await retryRequest(() => apiClient.post(url, permissions))

      return {
        success: true,
        data: response.data.data,
        message: '用户权限更新成功',
      }
    } catch (error) {
      console.error('[UsersApi] Update permissions failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '用户权限更新失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 搜索用户
   * @param {string} query - 搜索关键词
   * @param {Object} filters - 过滤条件
   * @returns {Promise<Object>} 搜索结果
   */
  async searchUsers(query, filters = {}) {
    try {
      const params = {
        search: query,
        ...filters,
      }

      return await this.listUsers(params)
    } catch (error) {
      console.error('[UsersApi] Search users failed:', error)
      throw error
    }
  }

  /**
   * 批量操作用户
   * @param {Array} userIds - 用户ID列表
   * @param {string} action - 操作类型
   * @param {Object} data - 操作数据
   * @returns {Promise<Object>} 操作结果
   */
  async batchOperation(userIds, action, data = {}) {
    try {
      const response = await retryRequest(() =>
        apiClient.post('/api/v1/users/batch', {
          user_ids: userIds,
          action,
          data,
        }),
      )

      return {
        success: true,
        data: response.data.data,
        message: '批量操作成功',
      }
    } catch (error) {
      console.error('[UsersApi] Batch operation failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '批量操作失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 切换用户状态（激活/停用）
   * @param {number} userId - 用户ID
   * @param {boolean} isActive - 是否激活
   * @param {string} reason - 操作原因
   * @returns {Promise<Object>} 操作结果
   */
  async toggleUserStatus(userId, isActive, reason = '') {
    try {
      const url = API_ENDPOINTS.USERS.TOGGLE_STATUS.replace('{user_id}', userId)
      const response = await retryRequest(() =>
        apiClient.post(url, {
          is_active: isActive,
          reason,
        }),
      )

      return {
        success: true,
        data: response.data.data,
        message: `用户${isActive ? '激活' : '停用'}成功`,
      }
    } catch (error) {
      console.error('[UsersApi] Toggle user status failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '用户状态切换失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 重置用户密码
   * @param {number} userId - 用户ID
   * @param {string} newPassword - 新密码
   * @returns {Promise<Object>} 操作结果
   */
  async resetUserPassword(userId, newPassword) {
    try {
      const url = API_ENDPOINTS.USERS.RESET_USER_PASSWORD.replace('{user_id}', userId)
      const response = await retryRequest(() =>
        apiClient.post(url, {
          new_password: newPassword,
        }),
      )

      return {
        success: true,
        data: response.data.data,
        message: '密码重置成功',
      }
    } catch (error) {
      console.error('[UsersApi] Reset password failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '密码重置失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 验证用户权限
   * @param {number} userId - 用户ID
   * @param {string} permission - 权限名称
   * @returns {Promise<Object>} 验证结果
   */
  async checkPermission(userId, permission) {
    try {
      const response = await retryRequest(() =>
        apiClient.get(`/api/v1/users/${userId}/permissions/${permission}`),
      )

      return {
        success: true,
        data: response.data.data,
        message: '权限验证成功',
      }
    } catch (error) {
      console.error('[UsersApi] Check permission failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '权限验证失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 获取当前用户信息
   * @returns {Promise<Object>} API响应
   */
  async getCurrentUser() {
    try {
      const response = await retryRequest(() => apiClient.get(API_ENDPOINTS.AUTH.ME))

      return {
        success: true,
        data: response.data,
        message: '获取当前用户信息成功',
      }
    } catch (error) {
      console.error('[UsersApi] Get current user failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取当前用户信息失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 获取当前用户统计信息
   * @returns {Promise<Object>} API响应
   */
  async getUserStats() {
    try {
      const response = await retryRequest(() => apiClient.get(API_ENDPOINTS.USERS.GET_USER_STATS))

      return {
        success: true,
        data: response.data,
        message: '获取用户统计成功',
      }
    } catch (error) {
      console.error('[UsersApi] Get user stats failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取用户统计失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 获取当前用户资产信息
   * @returns {Promise<Object>} API响应
   */
  async getUserAssets() {
    try {
      const response = await retryRequest(() => apiClient.get(API_ENDPOINTS.USERS.GET_USER_ASSETS))

      return {
        success: true,
        data: response.data,
        message: '获取用户资产成功',
      }
    } catch (error) {
      console.error('[UsersApi] Get user assets failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取用户资产失败',
        error: error.response?.data,
      }
    }
  }
}

// 创建实例
export const usersApi = new UsersApi()

// 默认导出
export default usersApi
