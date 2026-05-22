/**
 * 认证API服务
 * 提供用户注册、登录、令牌管理等功能
 */
import apiClient, { retryRequest } from '../client.js'
import { API_ENDPOINTS } from '../config.js'

/**
 * 认证API类
 */
export class AuthApi {
  /**
   * 用户注册
   * @param {Object} userData - 用户数据
   * @param {string} userData.steam_id - Steam ID (字符串格式，避免精度丢失)
   * @param {string} userData.username - 用户名
   * @param {string} userData.email - 邮箱地址
   * @param {string} userData.password - 密码
   * @returns {Promise<Object>} 注册结果
   */
  async register(userData) {
    try {
      const response = await retryRequest(() =>
        apiClient.post(API_ENDPOINTS.AUTH.REGISTER, userData),
      )
      return {
        success: true,
        data: response.data,
        message: '注册成功',
      }
    } catch (error) {
      console.error('[AuthApi] Register failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '注册失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 用户登录
   * @param {Object} credentials - 登录凭据
   * @param {string} credentials.username - 用户名
   * @param {string} credentials.password - 密码
   * @param {boolean} credentials.remember_me - 记住我选项，默认false
   * @returns {Promise<Object>} 登录结果
   */
  async login(credentials) {
    try {
      // 构建登录请求数据，确保包含remember_me参数
      const loginData = {
        username: credentials.username,
        password: credentials.password,
        remember_me: credentials.remember_me || false,
      }

      const response = await retryRequest(() => apiClient.post(API_ENDPOINTS.AUTH.LOGIN, loginData))

      // 保存token和相关信息到localStorage
      if (response.data.access_token) {
        localStorage.setItem('access_token', response.data.access_token)
        localStorage.setItem('refresh_token', response.data.refresh_token)
        localStorage.setItem('user_info', JSON.stringify(response.data.user_info))

        // 保存Token过期时间信息
        const expiresIn = response.data.expires_in || 43200 // 默认12小时
        const expiresAt = Date.now() + expiresIn * 1000 // 转换为毫秒时间戳
        localStorage.setItem('token_expires_at', expiresAt.toString())
        localStorage.setItem('token_expires_in', expiresIn.toString())

        // 保存记住我状态
        localStorage.setItem('remember_me_status', credentials.remember_me ? 'true' : 'false')
      }

      return {
        success: true,
        data: response.data,
        message: '登录成功',
      }
    } catch (error) {
      console.error('[AuthApi] Login failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '登录失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 刷新令牌
   * @param {string} refreshToken - 刷新令牌
   * @returns {Promise<Object>} 刷新结果
   */
  async refreshToken(refreshToken) {
    try {
      const response = await retryRequest(() =>
        apiClient.post(API_ENDPOINTS.AUTH.REFRESH, { refresh_token: refreshToken }),
      )

      // 更新token
      if (response.data.access_token) {
        localStorage.setItem('access_token', response.data.access_token)
      }

      return {
        success: true,
        data: response.data,
        message: '令牌刷新成功',
      }
    } catch (error) {
      console.error('[AuthApi] Refresh token failed:', error)
      // 刷新失败，清除本地token
      this.logout()
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '令牌刷新失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 获取当前用户信息
   * @returns {Promise<Object>} 用户信息
   */
  async getCurrentUser() {
    try {
      const response = await retryRequest(() => apiClient.get(API_ENDPOINTS.AUTH.ME))

      return {
        success: true,
        data: response.data,
        message: '获取用户信息成功',
      }
    } catch (error) {
      console.error('[AuthApi] Get current user failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取用户信息失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 注销
   */
  logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_info')
    localStorage.removeItem('token_expires_at')
    localStorage.removeItem('token_expires_in')
    localStorage.removeItem('remember_me_status')
  }

  /**
   * 检查是否已登录
   * @returns {boolean} 是否已登录
   */
  isLoggedIn() {
    return !!localStorage.getItem('access_token')
  }

  /**
   * 获取认证头
   * @returns {Object} 认证头
   */
  getAuthHeaders() {
    const token = localStorage.getItem('access_token')
    return token ? { Authorization: `Bearer ${token}` } : {}
  }

  /**
   * 获取当前用户信息（从localStorage）
   * @returns {Object|null} 用户信息
   */
  getCurrentUserFromStorage() {
    const userInfo = localStorage.getItem('user_info')
    return userInfo ? JSON.parse(userInfo) : null
  }

  /**
   * 验证SteamID格式
   * @param {string} steamId - Steam ID
   * @returns {boolean} 是否有效
   */
  validateSteamId(steamId) {
    // SteamID64格式验证 (17位数字，以7656开头)
    const steamId64Regex = /^7656\d{13}$/
    return steamId64Regex.test(steamId)
  }

  /**
   * 验证密码强度
   * @param {string} password - 密码
   * @returns {Object} 验证结果
   */
  validatePassword(password) {
    const result = {
      isValid: true,
      errors: [],
    }

    if (password.length < 8) {
      result.isValid = false
      result.errors.push('密码长度至少为8位')
    }

    if (!/[a-zA-Z]/.test(password)) {
      result.isValid = false
      result.errors.push('密码必须包含字母')
    }

    if (!/\d/.test(password)) {
      result.isValid = false
      result.errors.push('密码必须包含数字')
    }

    return result
  }

  /**
   * 检查Token是否即将过期
   * @param {number} bufferMinutes - 提前多少分钟判断为即将过期，默认5分钟
   * @returns {boolean} 是否即将过期
   */
  isTokenExpiringSoon(bufferMinutes = 5) {
    const expiresAt = localStorage.getItem('token_expires_at')
    if (!expiresAt) return true

    const expirationTime = parseInt(expiresAt)
    const bufferTime = bufferMinutes * 60 * 1000 // 转换为毫秒
    return Date.now() + bufferTime >= expirationTime
  }

  /**
   * 获取Token剩余有效时间（秒）
   * @returns {number} 剩余秒数，如果已过期返回0
   */
  getTokenRemainingTime() {
    const expiresAt = localStorage.getItem('token_expires_at')
    if (!expiresAt) return 0

    const expirationTime = parseInt(expiresAt)
    const remainingMs = expirationTime - Date.now()
    return Math.max(0, Math.floor(remainingMs / 1000))
  }

  /**
   * 获取记住我状态
   * @returns {boolean} 记住我状态
   */
  getRememberMeStatus() {
    const status = localStorage.getItem('remember_me_status')
    return status === 'true'
  }
}

// 创建实例
export const authApi = new AuthApi()

// 默认导出
export default authApi
