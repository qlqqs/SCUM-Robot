/**
 * 用户管理API服务
 * 提供用户管理相关的API接口
 */

import apiClient, { retryRequest } from '../client.js'
import { API_ENDPOINTS } from '../config.js'

/**
 * 获取用户列表
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码
 * @param {number} params.limit - 每页数量
 * @param {string} params.search - 搜索关键词
 * @param {string} params.user_type - 用户类型筛选
 * @param {boolean} params.is_active - 状态筛选
 * @returns {Promise<Object>} API响应
 */
export const getUserList = async (params = {}) => {
  try {
    const response = await retryRequest(() => apiClient.get(API_ENDPOINTS.USERS.LIST, { params }))

    return {
      success: true,
      data: response.data,
      message: '获取用户列表成功',
    }
  } catch (error) {
    console.error('获取用户列表失败:', error)
    return {
      success: false,
      message: error.response?.data?.message || '获取用户列表失败',
      error: error.response?.data || error.message,
    }
  }
}

/**
 * 创建用户
 * @param {Object} userData - 用户数据
 * @param {string} userData.username - 用户名
 * @param {string} userData.email - 邮箱
 * @param {string} userData.steam_id - SteamID
 * @param {string} userData.password - 密码
 * @param {string} userData.user_type - 用户类型
 * @param {boolean} userData.is_active - 是否激活
 * @returns {Promise<Object>} API响应
 */
export const createUser = async (userData) => {
  try {
    const response = await retryRequest(() => apiClient.post(API_ENDPOINTS.USERS.LIST, userData))

    return {
      success: true,
      data: response.data,
      message: '创建用户成功',
    }
  } catch (error) {
    console.error('创建用户失败:', error)
    return {
      success: false,
      message: error.response?.data?.message || '创建用户失败',
      error: error.response?.data || error.message,
    }
  }
}

/**
 * 获取用户详情
 * @param {number} userId - 用户ID
 * @returns {Promise<Object>} API响应
 */
export const getUserDetail = async (userId) => {
  try {
    const response = await retryRequest(() =>
      apiClient.get(API_ENDPOINTS.USERS.GET_USER.replace('{user_id}', userId)),
    )

    return {
      success: true,
      data: response.data,
      message: '获取用户详情成功',
    }
  } catch (error) {
    console.error('获取用户详情失败:', error)
    return {
      success: false,
      message: error.response?.data?.message || '获取用户详情失败',
      error: error.response?.data || error.message,
    }
  }
}

/**
 * 获取用户资产信息
 * @param {number} userId - 用户ID
 * @returns {Promise<Object>} API响应
 */
export const getUserAssets = async (userId) => {
  try {
    const response = await retryRequest(() => apiClient.get(`/api/v1/users/${userId}/assets`))

    return {
      success: true,
      data: response.data,
      message: '获取用户资产成功',
    }
  } catch (error) {
    console.error('获取用户资产失败:', error)
    return {
      success: false,
      message: error.response?.data?.message || '获取用户资产失败',
      error: error.response?.data || error.message,
    }
  }
}

/**
 * 更新用户资产信息
 * @param {number} userId - 用户ID
 * @param {Object} assetsData - 资产数据
 * @returns {Promise<Object>} API响应
 */
export const updateUserAssets = async (userId, assetsData) => {
  try {
    const response = await retryRequest(() =>
      apiClient.put(`/api/v1/users/${userId}/assets`, assetsData),
    )

    return {
      success: true,
      data: response.data,
      message: '更新用户资产成功',
    }
  } catch (error) {
    console.error('更新用户资产失败:', error)
    return {
      success: false,
      message: error.response?.data?.message || '更新用户资产失败',
      error: error.response?.data || error.message,
    }
  }
}

/**
 * 更新用户信息
 * @param {number} userId - 用户ID
 * @param {Object} userData - 用户数据
 * @returns {Promise<Object>} API响应
 */
export const updateUser = async (userId, userData) => {
  try {
    const response = await retryRequest(() =>
      apiClient.put(API_ENDPOINTS.USERS.UPDATE.replace('{user_id}', userId), userData),
    )

    return {
      success: true,
      data: response.data,
      message: '更新用户信息成功',
    }
  } catch (error) {
    console.error('更新用户信息失败:', error)

    // 处理特定错误类型
    let errorMessage = '更新用户信息失败'

    if (error.response?.status === 409) {
      // 唯一约束冲突
      if (error.response?.data?.detail?.includes('steam_id')) {
        errorMessage = 'Steam ID已被其他用户使用，请使用不同的Steam ID'
      } else if (error.response?.data?.detail?.includes('username')) {
        errorMessage = '用户名已被使用，请使用不同的用户名'
      } else if (error.response?.data?.detail?.includes('email')) {
        errorMessage = '邮箱已被使用，请使用不同的邮箱'
      } else {
        errorMessage = '数据冲突：' + (error.response?.data?.detail || '用户信息已存在')
      }
    } else if (error.response?.status === 400) {
      // 请求参数错误
      errorMessage = '请求参数错误：' + (error.response?.data?.detail || '请检查输入的数据格式')
    } else if (error.response?.status === 422) {
      // 数据验证失败
      errorMessage = '数据验证失败：' + (error.response?.data?.detail || '请检查输入的数据')
    } else {
      // 其他错误
      errorMessage = error.response?.data?.detail || error.response?.data?.message || errorMessage
    }

    return {
      success: false,
      message: errorMessage,
      error: error.response?.data || error.message,
    }
  }
}

/**
 * 删除用户
 * @param {number} userId - 用户ID
 * @returns {Promise<Object>} API响应
 */
export const deleteUser = async (userId) => {
  try {
    const response = await retryRequest(() =>
      apiClient.delete(API_ENDPOINTS.USERS.DELETE.replace('{user_id}', userId)),
    )

    return {
      success: true,
      data: response.data,
      message: '删除用户成功',
    }
  } catch (error) {
    console.error('删除用户失败:', error)
    return {
      success: false,
      message: error.response?.data?.message || '删除用户失败',
      error: error.response?.data || error.message,
    }
  }
}

/**
 * 批量操作用户
 * @param {string} action - 操作类型 ('activate', 'deactivate', 'delete')
 * @param {Array<number>} userIds - 用户ID数组
 * @returns {Promise<Object>} API响应
 */
export const batchOperateUsers = async (action, userIds) => {
  try {
    const response = await retryRequest(() =>
      apiClient.post(API_ENDPOINTS.USERS.BATCH_OPERATE, {
        action,
        user_ids: userIds,
      }),
    )

    return {
      success: true,
      data: response.data,
      message: `批量${action === 'activate' ? '激活' : action === 'deactivate' ? '停用' : '删除'}用户成功`,
    }
  } catch (error) {
    console.error('批量操作用户失败:', error)
    return {
      success: false,
      message: error.response?.data?.message || '批量操作用户失败',
      error: error.response?.data || error.message,
    }
  }
}

/**
 * 重置用户密码
 * @param {number} userId - 用户ID
 * @param {string} newPassword - 新密码
 * @returns {Promise<Object>} API响应
 */
export const resetUserPassword = async (userId, newPassword) => {
  try {
    const response = await retryRequest(() =>
      apiClient.post(API_ENDPOINTS.USERS.RESET_PASSWORD.replace('{user_id}', userId), {
        new_password: newPassword,
      }),
    )

    return {
      success: true,
      data: response.data,
      message: '重置用户密码成功',
    }
  } catch (error) {
    console.error('重置用户密码失败:', error)
    return {
      success: false,
      message: error.response?.data?.message || '重置用户密码失败',
      error: error.response?.data || error.message,
    }
  }
}

/**
 * 获取用户统计信息
 * @returns {Promise<Object>} API响应
 */
export const getUserStatistics = async () => {
  try {
    const response = await retryRequest(() => apiClient.get(API_ENDPOINTS.USERS.STATISTICS))

    return {
      success: true,
      data: response.data,
      message: '获取用户统计信息成功',
    }
  } catch (error) {
    console.error('获取用户统计信息失败:', error)
    return {
      success: false,
      message: error.response?.data?.message || '获取用户统计信息失败',
      error: error.response?.data || error.message,
    }
  }
}

export default {
  getUserList,
  getUserDetail,
  getUserAssets,
  updateUserAssets,
  updateUser,
  deleteUser,
  batchOperateUsers,
  resetUserPassword,
  getUserStatistics,
}
