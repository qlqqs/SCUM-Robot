/**
 * 礼包系统API服务
 * 提供礼包管理、领取、历史查询等功能
 */
import apiClient, { retryRequest } from '../client.js'
import { API_ENDPOINTS } from '../config.js'

/**
 * 礼包API类
 */
export class GiftsApi {
  // ==================== 用户接口 ====================

  /**
   * 获取可领取的礼包列表
   * @returns {Promise<Object>} 可领取礼包列表
   */
  async getAvailableGifts() {
    try {
      const response = await retryRequest(() => apiClient.get(API_ENDPOINTS.GIFTS.AVAILABLE))

      // 根据API文档，响应格式是 { success: true, data: { gifts: [...] } }
      return {
        success: true,
        data: response.data.data.gifts || [], // 注意这里是 data.gifts
        message: response.data.message || '获取礼包列表成功',
      }
    } catch (error) {
      console.error('[GiftsApi] Get available gifts failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取礼包列表失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 领取指定礼包
   * @param {number} giftId - 礼包ID
   * @returns {Promise<Object>} 领取结果
   */
  async claimGift(giftId) {
    try {
      const url = API_ENDPOINTS.GIFTS.CLAIM.replace('{gift_id}', giftId)
      const response = await retryRequest(() => apiClient.post(url))

      return {
        success: true,
        data: response.data.data,
        message: response.data.message || '礼包领取成功',
      }
    } catch (error) {
      console.error('[GiftsApi] Claim gift failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '礼包领取失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 获取礼包领取历史
   * @param {Object} params - 查询参数
   * @param {number} params.limit - 每页数量，默认20
   * @param {number} params.offset - 偏移量，默认0
   * @returns {Promise<Object>} 领取历史
   */
  async getGiftHistory(params = {}) {
    try {
      const { limit = 20, offset = 0 } = params
      const response = await retryRequest(() =>
        apiClient.get(API_ENDPOINTS.GIFTS.HISTORY, {
          params: { limit, offset },
        }),
      )

      // 根据API文档，响应格式是 { success: true, data: { history: [...], total_count: n } }
      return {
        success: true,
        data: {
          history: response.data.data.history || [],
          total_count: response.data.data.total_count || 0,
        },
        message: response.data.message || '获取领取历史成功',
      }
    } catch (error) {
      console.error('[GiftsApi] Get gift history failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取领取历史失败',
        error: error.response?.data,
      }
    }
  }

  // ==================== 管理员接口 ====================

  /**
   * 创建新礼包（管理员）
   * @param {Object} giftData - 礼包数据
   * @param {string} giftData.name - 礼包名称
   * @param {string} giftData.description - 礼包描述
   * @param {string} giftData.gift_type - 礼包类型
   * @param {Object} giftData.items_config - 物品配置
   * @param {boolean} giftData.is_active - 是否启用
   * @param {number} giftData.max_claims - 最大领取次数
   * @param {number} giftData.cooldown_hours - 冷却时间（小时）
   * @param {number} giftData.required_level - 所需等级
   * @param {number|null} giftData.total_quantity - 总数量（限量礼包）
   * @param {string|null} giftData.start_time - 开始时间（限时礼包）
   * @param {string|null} giftData.end_time - 结束时间（限时礼包）
   * @returns {Promise<Object>} 创建结果
   */
  async createGift(giftData) {
    try {
      const response = await retryRequest(() =>
        apiClient.post(API_ENDPOINTS.GIFTS.CREATE, giftData),
      )

      return {
        success: true,
        data: response.data.data,
        message: response.data.message || '礼包创建成功',
      }
    } catch (error) {
      console.error('[GiftsApi] Create gift failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '礼包创建失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 获取所有礼包（管理员）
   * @returns {Promise<Object>} 所有礼包列表
   */
  async getAllGifts() {
    try {
      const response = await retryRequest(() => apiClient.get(API_ENDPOINTS.GIFTS.GET_ALL))

      // 根据API文档，响应格式是 { success: true, data: { gifts: [...] } }
      return {
        success: true,
        data: response.data.data || {}, // 返回完整的data对象，包含gifts数组
        message: response.data.message || '获取礼包列表成功',
      }
    } catch (error) {
      console.error('[GiftsApi] Get all gifts failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取礼包列表失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 获取单个礼包详情（管理员）
   * @param {number} giftId - 礼包ID
   * @returns {Promise<Object>} 礼包详情
   */
  async getGift(giftId) {
    try {
      const url = API_ENDPOINTS.GIFTS.GET_ONE.replace('{gift_id}', giftId)
      const response = await retryRequest(() => apiClient.get(url))

      // 检查响应结构
      if (!response.data) {
        throw new Error('响应中没有data字段')
      }

      let giftData
      let message = '获取礼包详情成功'

      if (response.data.data && typeof response.data.data === 'object') {
        // 标准格式: { success: true, data: { id, name, ... }, message: "..." }
        giftData = response.data.data
        message = response.data.message || message
      } else if (response.data.id) {
        // 直接格式: { id, name, ... }
        giftData = response.data
      } else if (response.data.success && response.data.data) {
        // 可能的嵌套格式: { success: true, data: { data: { id, name, ... } } }
        giftData = response.data.data.data || response.data.data
        message = response.data.message || message
      } else {
        console.error('[GiftsApi] 无法识别的响应格式:', response.data)
        throw new Error('无法识别响应格式')
      }

      return {
        success: true,
        data: giftData,
        message: message,
      }
    } catch (error) {
      console.error('[GiftsApi] Get gift failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取礼包详情失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 更新礼包（管理员）
   * @param {number} giftId - 礼包ID
   * @param {Object} updateData - 更新数据
   * @returns {Promise<Object>} 更新结果
   */
  async updateGift(giftId, updateData) {
    try {
      const url = API_ENDPOINTS.GIFTS.UPDATE.replace('{gift_id}', giftId)
      const response = await retryRequest(() => apiClient.put(url, updateData))

      return {
        success: true,
        data: response.data.data,
        message: response.data.message || '礼包更新成功',
      }
    } catch (error) {
      console.error('[GiftsApi] Update gift failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '礼包更新失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 删除礼包（管理员）
   * @param {number} giftId - 礼包ID
   * @returns {Promise<Object>} 删除结果
   */
  async deleteGift(giftId) {
    try {
      const url = API_ENDPOINTS.GIFTS.DELETE.replace('{gift_id}', giftId)
      const response = await retryRequest(() => apiClient.delete(url))

      return {
        success: true,
        data: response.data.data,
        message: response.data.message || '礼包删除成功',
      }
    } catch (error) {
      console.error('[GiftsApi] Delete gift failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '礼包删除失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 上传礼包图片
   * @param {number} giftId - 礼包ID
   * @param {File} file - 图片文件
   * @returns {Promise<Object>} 上传结果
   */
  async uploadGiftImage(giftId, file) {
    try {
      // 验证文件
      if (!file) {
        throw new Error('请选择要上传的图片文件')
      }

      // 验证文件类型
      const allowedTypes = [
        'image/jpeg',
        'image/jpg',
        'image/png',
        'image/gif',
        'image/webp',
        'image/bmp',
      ]
      if (!allowedTypes.includes(file.type)) {
        throw new Error('不支持的文件格式，请上传 JPG、PNG、GIF、WebP 或 BMP 格式的图片')
      }

      // 验证文件大小 (5MB)
      const maxSize = 5 * 1024 * 1024
      if (file.size > maxSize) {
        throw new Error('文件大小不能超过5MB')
      }

      // 验证文件名长度
      if (file.name.length > 255) {
        throw new Error('文件名长度不能超过255字符')
      }

      // 创建FormData
      const formData = new FormData()
      formData.append('file', file)

      const url = API_ENDPOINTS.GIFTS.UPLOAD_IMAGE.replace('{gift_id}', giftId)
      const response = await retryRequest(() =>
        apiClient.post(url, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }),
      )

      return {
        success: true,
        data: response.data.data,
        message: response.data.message || '礼包图片上传成功',
      }
    } catch (error) {
      console.error('[GiftsApi] Upload gift image failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '礼包图片上传失败',
        error: error.response?.data,
      }
    }
  }

  // ==================== 工具方法 ====================

  /**
   * 验证礼包类型
   * @param {string} giftType - 礼包类型
   * @returns {boolean} 是否有效
   */
  validateGiftType(giftType) {
    const validTypes = [
      'one_time',
      'daily',
      'limited_quantity',
      'limited_time',
      'limited_time_quantity',
    ]
    return validTypes.includes(giftType)
  }

  /**
   * 验证礼包配置
   * @param {Object} giftData - 礼包数据
   * @returns {Object} 验证结果
   */
  validateGiftConfig(giftData) {
    const result = {
      isValid: true,
      errors: [],
    }

    // 基础字段验证
    if (!giftData.name || giftData.name.trim().length === 0) {
      result.isValid = false
      result.errors.push('礼包名称不能为空')
    }

    if (!giftData.gift_type || !this.validateGiftType(giftData.gift_type)) {
      result.isValid = false
      result.errors.push('礼包类型无效')
    }

    if (!giftData.items_config || Object.keys(giftData.items_config).length === 0) {
      result.isValid = false
      result.errors.push('物品配置不能为空')
    }

    // 根据礼包类型进行特定验证
    switch (giftData.gift_type) {
      case 'limited_quantity':
      case 'limited_time_quantity':
        if (!giftData.total_quantity || giftData.total_quantity <= 0) {
          result.isValid = false
          result.errors.push('限量礼包必须设置有效的总数量')
        }
        break

      case 'limited_time':
      case 'limited_time_quantity':
        if (!giftData.start_time || !giftData.end_time) {
          result.isValid = false
          result.errors.push('限时礼包必须设置开始和结束时间')
        } else if (new Date(giftData.start_time) >= new Date(giftData.end_time)) {
          result.isValid = false
          result.errors.push('开始时间必须早于结束时间')
        }
        break
    }

    return result
  }

  /**
   * 格式化礼包数据用于显示
   * @param {Object} gift - 礼包数据
   * @returns {Object} 格式化后的礼包数据
   */
  formatGiftForDisplay(gift) {
    return {
      ...gift,
      items_display: this.formatItemsConfig(gift.items_config),
      type_display: this.getGiftTypeDisplay(gift.gift_type),
      status_display: gift.is_active ? '启用' : '禁用',
      remaining_display:
        gift.remaining_quantity !== null
          ? `${gift.remaining_quantity}/${gift.total_quantity}`
          : '无限制',
    }
  }

  /**
   * 格式化物品配置用于显示
   * @param {Object} itemsConfig - 物品配置（字典格式）
   * @returns {string} 格式化后的物品列表
   */
  formatItemsConfig(itemsConfig) {
    if (!itemsConfig) return ''

    try {
      if (typeof itemsConfig === 'object' && !Array.isArray(itemsConfig)) {
        // 字典格式：{"item_name": quantity}
        return Object.entries(itemsConfig)
          .map(([itemCode, quantity]) => `${itemCode} x${quantity}`)
          .join(', ')
      }
    } catch (error) {
      console.error('格式化物品配置失败:', error)
      return '配置格式错误'
    }

    return ''
  }

  /**
   * 获取礼包类型显示名称
   * @param {string} giftType - 礼包类型
   * @returns {string} 显示名称
   */
  getGiftTypeDisplay(giftType) {
    const typeMap = {
      one_time: '一次性礼包',
      daily: '每日礼包',
      limited_quantity: '限量礼包',
      limited_time: '限时礼包',
      limited_time_quantity: '限时限量礼包',
    }
    return typeMap[giftType] || giftType
  }
}

// 创建实例
export const giftsApi = new GiftsApi()

// 默认导出
export default giftsApi
