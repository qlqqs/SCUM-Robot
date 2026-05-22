/**
 * HTTP客户端配置
 */
import axios from 'axios'
import { API_CONFIG, HTTP_STATUS, ERROR_MESSAGES } from './config.js'

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_CONFIG.BASE_URL,
  timeout: API_CONFIG.TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 在发送请求之前做些什么
    console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, config.data)

    // 添加认证token
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  },
  (error) => {
    console.error('[API Request Error]', error)
    return Promise.reject(error)
  },
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    // 对响应数据做点什么
    console.log(`[API Response] ${response.status} ${response.config.url}`, response.data)
    return response
  },
  (error) => {
    console.error('[API Response Error]', error)

    // 统一错误处理
    const errorMessage = getErrorMessage(error)

    // 处理401错误（令牌过期或无效）
    if (error.response?.status === 401) {
      console.log('[API] Token expired or invalid, redirecting to login')

      // 清除本地存储的认证信息
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user_info')

      // 跳转到登录页面
      // 使用window.location而不是router，因为这里无法访问router实例
      const currentPath = window.location.pathname
      if (currentPath !== '/login') {
        window.location.href = `/login?redirect=${encodeURIComponent(currentPath)}`
      }
    }

    return Promise.reject({
      ...error,
      message: errorMessage,
    })
  },
)

/**
 * 获取错误消息
 * @param {Error} error - 错误对象
 * @returns {string} 错误消息
 */
function getErrorMessage(error) {
  if (error.code === 'ECONNABORTED') {
    return ERROR_MESSAGES.TIMEOUT_ERROR
  }

  if (error.code === 'ERR_NETWORK') {
    return ERROR_MESSAGES.NETWORK_ERROR
  }

  if (error.response) {
    const { status, data } = error.response

    switch (status) {
      case HTTP_STATUS.BAD_REQUEST:
        return data?.message || ERROR_MESSAGES.VALIDATION_ERROR
      case HTTP_STATUS.UNAUTHORIZED:
        return ERROR_MESSAGES.UNAUTHORIZED
      case HTTP_STATUS.FORBIDDEN:
        return ERROR_MESSAGES.FORBIDDEN
      case HTTP_STATUS.NOT_FOUND:
        return ERROR_MESSAGES.NOT_FOUND
      case HTTP_STATUS.INTERNAL_SERVER_ERROR:
        return data?.message || ERROR_MESSAGES.SERVER_ERROR
      default:
        return data?.message || ERROR_MESSAGES.UNKNOWN_ERROR
    }
  }

  return error.message || ERROR_MESSAGES.UNKNOWN_ERROR
}

/**
 * 重试请求
 * @param {Function} requestFn - 请求函数
 * @param {number} retries - 重试次数
 * @param {number} delay - 重试延迟
 * @returns {Promise} 请求结果
 */
export async function retryRequest(
  requestFn,
  retries = API_CONFIG.RETRY_COUNT,
  delay = API_CONFIG.RETRY_DELAY,
) {
  try {
    return await requestFn()
  } catch (error) {
    if (retries > 0 && shouldRetry(error)) {
      console.log(`[API Retry] Retrying request in ${delay}ms, ${retries} retries left`)
      await new Promise((resolve) => setTimeout(resolve, delay))
      return retryRequest(requestFn, retries - 1, delay)
    }
    throw error
  }
}

/**
 * 判断是否应该重试
 * @param {Error} error - 错误对象
 * @returns {boolean} 是否应该重试
 */
function shouldRetry(error) {
  // 网络错误或超时错误可以重试
  if (error.code === 'ECONNABORTED' || error.code === 'ERR_NETWORK') {
    return true
  }

  // 5xx服务器错误可以重试
  if (error.response && error.response.status >= 500) {
    return true
  }

  return false
}

export default apiClient
