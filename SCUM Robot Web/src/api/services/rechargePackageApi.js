/**
 * 充值套餐 API 服务
 */

import client from '../client.js'

/**
 * 获取充值套餐列表
 * @param {Object} params - 查询参数
 * @param {boolean} params.active_only - 只返回启用的套餐（默认：true）
 * @returns {Promise<Object>} 套餐列表
 */
export const getPackages = async (params = {}) => {
  try {
    console.log('[RechargePackageAPI] Getting packages with params:', params)
    const response = await client.get('/api/v1/recharge/packages', { params })
    console.log('[RechargePackageAPI] Get packages response:', response.data)
    return {
      success: true,
      data: response.data,
    }
  } catch (error) {
    console.error('[RechargePackageAPI] Failed to get packages:', error)
    return {
      success: false,
      message: error.response?.data?.message || error.message || '获取套餐列表失败',
      error,
    }
  }
}

/**
 * 获取热门套餐
 * @param {number} limit - 返回数量（默认：3，最大：10）
 * @returns {Promise<Object>} 热门套餐列表
 */
export const getHotPackages = async (limit = 3) => {
  try {
    console.log('[RechargePackageAPI] Getting hot packages, limit:', limit)
    const response = await client.get('/api/v1/recharge/packages/hot', {
      params: { limit },
    })
    console.log('[RechargePackageAPI] Get hot packages response:', response.data)
    return {
      success: true,
      data: response.data,
    }
  } catch (error) {
    console.error('[RechargePackageAPI] Failed to get hot packages:', error)
    return {
      success: false,
      message: error.response?.data?.message || error.message || '获取热门套餐失败',
      error,
    }
  }
}

/**
 * 获取推荐套餐
 * @param {number} limit - 返回数量（默认：3，最大：10）
 * @returns {Promise<Object>} 推荐套餐列表
 */
export const getRecommendedPackages = async (limit = 3) => {
  try {
    console.log('[RechargePackageAPI] Getting recommended packages, limit:', limit)
    const response = await client.get('/api/v1/recharge/packages/recommended', {
      params: { limit },
    })
    console.log('[RechargePackageAPI] Get recommended packages response:', response.data)
    return {
      success: true,
      data: response.data,
    }
  } catch (error) {
    console.error('[RechargePackageAPI] Failed to get recommended packages:', error)
    return {
      success: false,
      message: error.response?.data?.message || error.message || '获取推荐套餐失败',
      error,
    }
  }
}

/**
 * 获取套餐详情
 * @param {number} packageId - 套餐ID
 * @returns {Promise<Object>} 套餐详情
 */
export const getPackageDetail = async (packageId) => {
  try {
    console.log('[RechargePackageAPI] Getting package detail, id:', packageId)
    const response = await client.get(`/api/v1/recharge/packages/${packageId}`)
    console.log('[RechargePackageAPI] Get package detail response:', response.data)
    return {
      success: true,
      data: response.data,
    }
  } catch (error) {
    console.error('[RechargePackageAPI] Failed to get package detail:', error)
    return {
      success: false,
      message: error.response?.data?.message || error.message || '获取套餐详情失败',
      error,
    }
  }
}

/**
 * 创建充值套餐（管理员）
 * @param {Object} packageData - 套餐数据
 * @returns {Promise<Object>} 创建结果
 */
export const createPackage = async (packageData) => {
  try {
    console.log('[RechargePackageAPI] Creating package:', packageData)
    const response = await client.post('/api/v1/recharge/packages', packageData)
    console.log('[RechargePackageAPI] Create package response:', response.data)
    return {
      success: true,
      data: response.data,
      message: '套餐创建成功',
    }
  } catch (error) {
    console.error('[RechargePackageAPI] Failed to create package:', error)
    return {
      success: false,
      message: error.response?.data?.message || error.message || '创建套餐失败',
      error,
    }
  }
}

/**
 * 更新充值套餐（管理员）
 * @param {number} packageId - 套餐ID
 * @param {Object} packageData - 套餐数据
 * @returns {Promise<Object>} 更新结果
 */
export const updatePackage = async (packageId, packageData) => {
  try {
    console.log('[RechargePackageAPI] Updating package:', packageId, packageData)
    const response = await client.put(`/api/v1/recharge/packages/${packageId}`, packageData)
    console.log('[RechargePackageAPI] Update package response:', response.data)
    return {
      success: true,
      data: response.data,
      message: '套餐更新成功',
    }
  } catch (error) {
    console.error('[RechargePackageAPI] Failed to update package:', error)
    return {
      success: false,
      message: error.response?.data?.message || error.message || '更新套餐失败',
      error,
    }
  }
}

/**
 * 删除充值套餐（管理员）
 * @param {number} packageId - 套餐ID
 * @returns {Promise<Object>} 删除结果
 */
export const deletePackage = async (packageId) => {
  try {
    console.log('[RechargePackageAPI] Deleting package:', packageId)
    const response = await client.delete(`/api/v1/recharge/packages/${packageId}`)
    console.log('[RechargePackageAPI] Delete package response:', response.data)
    return {
      success: true,
      data: response.data,
      message: '套餐删除成功',
    }
  } catch (error) {
    console.error('[RechargePackageAPI] Failed to delete package:', error)
    return {
      success: false,
      message: error.response?.data?.message || error.message || '删除套餐失败',
      error,
    }
  }
}

// 导出所有API方法
export const rechargePackageApi = {
  getPackages,
  getHotPackages,
  getRecommendedPackages,
  getPackageDetail,
  createPackage,
  updatePackage,
  deletePackage,
}

export default rechargePackageApi
