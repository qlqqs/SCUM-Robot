import apiClient from '../client.js'

/**
 * 支付配置管理API
 */
export const paymentApi = {
  /**
   * 获取支付配置列表
   * @param {Object} params - 查询参数
   * @param {string} params.environment - 环境 (production/test)
   * @param {boolean} params.include_sensitive - 是否包含敏感信息
   * @returns {Promise<Object>} API响应
   */
  async getConfigs(params = {}) {
    try {
      const response = await apiClient.get('/api/v1/payment/configs', { params })
      return response.data
    } catch (error) {
      console.error('[PaymentAPI] Failed to get configs:', error)
      throw error
    }
  },

  /**
   * 创建支付配置
   * @param {Object} configData - 配置数据
   * @returns {Promise<Object>} API响应
   */
  async createConfig(configData) {
    try {
      const response = await apiClient.post('/api/v1/payment/configs', configData)
      return response.data
    } catch (error) {
      console.error('[PaymentAPI] Failed to create config:', error)
      throw error
    }
  },

  /**
   * 获取单个支付配置
   * @param {number} configId - 配置ID
   * @param {boolean} includeSensitive - 是否包含敏感信息
   * @returns {Promise<Object>} API响应
   */
  async getConfig(configId, includeSensitive = false) {
    try {
      const params = includeSensitive ? { include_sensitive: true } : {}
      const response = await apiClient.get(`/api/v1/payment/configs/${configId}`, { params })
      return response.data
    } catch (error) {
      console.error('[PaymentAPI] Failed to get config:', error)
      throw error
    }
  },

  /**
   * 更新支付配置
   * @param {number} configId - 配置ID
   * @param {Object} configData - 配置数据
   * @returns {Promise<Object>} API响应
   */
  async updateConfig(configId, configData) {
    try {
      const response = await apiClient.put(`/api/v1/payment/configs/${configId}`, configData)
      return response.data
    } catch (error) {
      console.error('[PaymentAPI] Failed to update config:', error)
      throw error
    }
  },

  /**
   * 删除支付配置
   * @param {number} configId - 配置ID
   * @returns {Promise<Object>} API响应
   */
  async deleteConfig(configId) {
    try {
      const response = await apiClient.delete(`/api/v1/payment/configs/${configId}`)
      return response.data
    } catch (error) {
      console.error('[PaymentAPI] Failed to delete config:', error)
      throw error
    }
  },

  /**
   * 测试支付配置
   * @param {number} configId - 配置ID
   * @returns {Promise<Object>} API响应
   */
  async testConfig(configId) {
    try {
      const response = await apiClient.post(`/api/v1/payment/configs/${configId}/test`)
      return response.data
    } catch (error) {
      console.error('[PaymentAPI] Failed to test config:', error)
      throw error
    }
  },

  /**
   * 获取支付配置模板
   * @returns {Promise<Object>} API响应
   */
  async getTemplates() {
    try {
      const response = await apiClient.get('/api/v1/payment/templates')
      return response.data
    } catch (error) {
      console.error('[PaymentAPI] Failed to get templates:', error)
      throw error
    }
  },

  /**
   * 获取支付提供商表单配置
   * @param {string} providerCode - 支付提供商代码
   * @returns {Promise<Object>} API响应
   */
  async getProviderForm(providerCode) {
    try {
      const response = await apiClient.get(`/api/v1/payment/providers/${providerCode}/form`)
      return response.data
    } catch (error) {
      console.error('[PaymentAPI] Failed to get provider form:', error)
      throw error
    }
  },

  /**
   * 获取可用支付方式
   * @param {string} environment - 环境
   * @returns {Promise<Object>} API响应
   */
  async getMethods(environment = 'production') {
    try {
      const response = await apiClient.get('/api/v1/payment/methods', {
        params: { environment },
      })
      return response.data
    } catch (error) {
      console.error('[PaymentAPI] Failed to get methods:', error)
      throw error
    }
  },

  /**
   * 获取支付统计
   * @param {number} userId - 用户ID（可选，仅管理员可用）
   * @returns {Promise<Object>} API响应
   */
  async getStatistics(userId = null) {
    try {
      const params = userId ? { user_id: userId } : {}
      const response = await apiClient.get('/api/v1/payment/statistics', { params })
      return response.data
    } catch (error) {
      console.error('[PaymentAPI] Failed to get statistics:', error)
      throw error
    }
  },

  /**
   * 获取订单列表
   * @param {Object} params - 查询参数
   * @param {number} params.page - 页码（从1开始）
   * @param {number} params.page_size - 每页数量（最大100）
   * @param {string} params.status - 订单状态筛选
   * @param {number} params.user_id - 用户ID筛选（仅管理员）
   * @param {string} params.start_date - 开始日期（YYYY-MM-DD）
   * @param {string} params.end_date - 结束日期（YYYY-MM-DD）
   * @returns {Promise<Object>} API响应
   */
  async getOrders(params = {}) {
    try {
      const response = await apiClient.get('/api/v1/payment/orders', { params })
      return response.data
    } catch (error) {
      console.error('[PaymentAPI] Failed to get orders:', error)
      throw error
    }
  },

  /**
   * 取消订单
   * @param {string} orderId - 订单ID
   * @returns {Promise<Object>} API响应
   */
  async cancelOrder(orderId) {
    try {
      const response = await apiClient.post(`/api/v1/payment/orders/${orderId}/cancel`)
      return response.data
    } catch (error) {
      console.error('[PaymentAPI] Failed to cancel order:', error)
      throw error
    }
  },

  /**
   * 查询订单状态
   * @param {string} orderId - 订单ID
   * @returns {Promise<Object>} API响应
   */
  async getOrderStatus(orderId) {
    try {
      const response = await apiClient.get(`/api/v1/payment/status/${orderId}`)
      return response.data
    } catch (error) {
      console.error('[PaymentAPI] Failed to get order status:', error)
      throw error
    }
  },

  /**
   * 查询回调日志
   * @param {string} orderId - 订单ID
   * @returns {Promise<Object>} API响应
   */
  async getCallbackLogs(orderId) {
    try {
      const response = await apiClient.get(`/api/v1/payment/callback/logs/${orderId}`)
      return response.data
    } catch (error) {
      console.error('[PaymentAPI] Failed to get callback logs:', error)
      throw error
    }
  },

  /**
   * 创建充值订单
   * @param {Object} orderData - 订单数据
   * @returns {Promise<Object>} API响应
   */
  async createOrder(orderData) {
    try {
      const response = await apiClient.post('/api/v1/payment/orders', orderData)
      return response.data
    } catch (error) {
      console.error('[PaymentAPI] Failed to create order:', error)
      throw error
    }
  },

  /**
   * 获取充值记录
   * @param {Object} params - 查询参数
   * @returns {Promise<Object>} API响应
   */
  async getRechargeHistory(params = {}) {
    try {
      const response = await apiClient.get('/api/v1/payment/orders', { params })
      return response.data
    } catch (error) {
      console.error('[PaymentAPI] Failed to get recharge history:', error)
      throw error
    }
  },
}
