/**
 * 物品管理API服务
 * 提供物品、类目、子类目的CRUD操作
 */
import apiClient, { retryRequest } from '../client.js'
import { API_ENDPOINTS } from '../config.js'
import { authApi } from './authApi.js'

/**
 * 物品管理API类
 */
export class ItemsApi {
  // ==================== 类目管理 ====================

  /**
   * 获取所有类目
   * @param {Object} params - 查询参数
   * @param {boolean} params.include_inactive - 是否包含非活跃类目
   * @param {number} params.page - 页码（默认1）
   * @param {number} params.page_size - 每页数量（默认50，最大100）
   * @returns {Promise<Object>} 类目列表
   */
  async getCategories(params = {}) {
    try {
      // 设置默认参数
      const finalParams = {
        include_inactive: true, // 管理界面默认显示所有类目
        page: 1,
        page_size: 50,
        ...params,
      }

      const response = await retryRequest(() =>
        apiClient.get(API_ENDPOINTS.ITEMS.CATEGORIES, { params: finalParams }),
      )

      // 根据最新API文档处理响应格式
      const responseData = response.data

      return {
        success: responseData.success || true,
        data: responseData.data?.categories || responseData.data || [],
        pagination: responseData.data?.pagination || null,
        message: responseData.message || '获取类目列表成功',
      }
    } catch (error) {
      console.error('[ItemsApi] Get categories failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取类目列表失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 获取类目详情
   * @param {number} categoryId - 类目ID
   * @returns {Promise<Object>} 类目详情
   */
  async getCategoryById(categoryId) {
    try {
      const url = API_ENDPOINTS.ITEMS.CATEGORY_BY_ID.replace('{category_id}', categoryId)
      const response = await retryRequest(() => apiClient.get(url))

      return {
        success: true,
        data: response.data.data,
        message: '获取类目详情成功',
      }
    } catch (error) {
      console.error('[ItemsApi] Get category failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取类目详情失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 获取类目及其子类目
   * @returns {Promise<Object>} 类目树
   */
  async getCategoriesWithSubcategories() {
    try {
      const response = await retryRequest(() =>
        apiClient.get(API_ENDPOINTS.ITEMS.CATEGORIES_WITH_SUBCATEGORIES),
      )

      return {
        success: true,
        data: response.data.data,
        message: '获取类目树成功',
      }
    } catch (error) {
      console.error('[ItemsApi] Get categories with subcategories failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取类目树失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 创建类目
   * @param {Object} categoryData - 类目数据
   * @param {string} categoryData.name - 类目名称
   * @param {string} categoryData.description - 类目描述
   * @returns {Promise<Object>} 创建结果
   */
  async createCategory(categoryData) {
    try {
      const response = await retryRequest(() =>
        apiClient.post(API_ENDPOINTS.ITEMS.CATEGORIES, categoryData, {
          headers: authApi.getAuthHeaders(),
        }),
      )

      // 根据最新API文档处理响应格式
      const responseData = response.data

      return {
        success: responseData.success || true,
        data: responseData.data,
        message: responseData.message || '类目创建成功',
      }
    } catch (error) {
      console.error('[ItemsApi] Create category failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '类目创建失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 更新类目
   * @param {number} categoryId - 类目ID
   * @param {Object} categoryData - 类目数据
   * @returns {Promise<Object>} 更新结果
   */
  async updateCategory(categoryId, categoryData) {
    try {
      const url = API_ENDPOINTS.ITEMS.CATEGORY_BY_ID.replace('{category_id}', categoryId)
      const response = await retryRequest(() =>
        apiClient.put(url, categoryData, {
          headers: authApi.getAuthHeaders(),
        }),
      )

      return {
        success: true,
        data: response.data.data,
        message: response.data.message || '类目更新成功',
      }
    } catch (error) {
      console.error('[ItemsApi] Update category failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '类目更新失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 更新类目激活状态
   * @param {number} categoryId - 类目ID
   * @param {boolean} isActive - 激活状态
   * @returns {Promise<Object>} 更新结果
   */
  async updateCategoryActiveStatus(categoryId, isActive) {
    try {
      const url = API_ENDPOINTS.ITEMS.CATEGORY_BY_ID.replace('{category_id}', categoryId)
      const response = await retryRequest(() =>
        apiClient.put(
          url,
          { is_active: isActive },
          {
            headers: authApi.getAuthHeaders(),
          },
        ),
      )

      return {
        success: true,
        data: response.data.data,
        message: response.data.message || `类目${isActive ? '启用' : '停用'}成功`,
      }
    } catch (error) {
      console.error('[ItemsApi] Update category active status failed:', error)
      throw {
        success: false,
        message:
          error.response?.data?.detail || error.message || `类目${isActive ? '启用' : '停用'}失败`,
        error: error.response?.data,
      }
    }
  }

  /**
   * 删除类目（硬删除）
   * @param {number} categoryId - 类目ID
   * @returns {Promise<Object>} 删除结果
   */
  async deleteCategory(categoryId) {
    try {
      const url = API_ENDPOINTS.ITEMS.CATEGORY_BY_ID.replace('{category_id}', categoryId)
      const response = await retryRequest(() =>
        apiClient.delete(url, {
          headers: authApi.getAuthHeaders(),
          params: {
            soft_delete: false, // 使用硬删除
            force: true, // 强制删除
          },
        }),
      )

      return {
        success: true,
        data: response.data,
        message: '类目删除成功',
      }
    } catch (error) {
      console.error('[ItemsApi] Delete category failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '类目删除失败',
        error: error.response?.data,
      }
    }
  }

  // ==================== 子类目管理 ====================

  /**
   * 获取所有子类目
   * @param {Object} params - 查询参数
   * @param {number} params.category_id - 父类目ID（可选）
   * @param {boolean} params.include_inactive - 是否包含非活跃子类目
   * @param {number} params.page - 页码
   * @param {number} params.page_size - 每页数量
   * @returns {Promise<Object>} 子类目列表
   */
  async getSubcategories(params = {}) {
    try {
      const response = await retryRequest(() =>
        apiClient.get(API_ENDPOINTS.ITEMS.SUBCATEGORIES, { params }),
      )

      return {
        success: true,
        data: response.data.data.subcategories || response.data.data, // 兼容新旧格式
        pagination: response.data.data.pagination,
        message: '获取子类目列表成功',
      }
    } catch (error) {
      console.error('[ItemsApi] Get subcategories failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取子类目列表失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 创建子类目
   * @param {Object} subcategoryData - 子类目数据
   * @returns {Promise<Object>} 创建结果
   */
  async createSubcategory(subcategoryData) {
    try {
      const response = await retryRequest(() =>
        apiClient.post(API_ENDPOINTS.ITEMS.SUBCATEGORIES, subcategoryData, {
          headers: authApi.getAuthHeaders(),
        }),
      )

      return {
        success: true,
        data: response.data.data,
        message: response.data.message || '子类目创建成功',
      }
    } catch (error) {
      console.error('[ItemsApi] Create subcategory failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '子类目创建失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 更新子类目
   * @param {number} subcategoryId - 子类目ID
   * @param {Object} subcategoryData - 子类目数据
   * @returns {Promise<Object>} 更新结果
   */
  async updateSubcategory(subcategoryId, subcategoryData) {
    try {
      const url = API_ENDPOINTS.ITEMS.SUBCATEGORY_BY_ID.replace('{subcategory_id}', subcategoryId)
      const response = await retryRequest(() =>
        apiClient.put(url, subcategoryData, {
          headers: authApi.getAuthHeaders(),
        }),
      )

      return {
        success: true,
        data: response.data.data,
        message: '子类目更新成功',
      }
    } catch (error) {
      console.error('[ItemsApi] Update subcategory failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '子类目更新失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 删除子类目（硬删除）
   * @param {number} subcategoryId - 子类目ID
   * @returns {Promise<Object>} 删除结果
   */
  async deleteSubcategory(subcategoryId) {
    try {
      const url = API_ENDPOINTS.ITEMS.SUBCATEGORY_BY_ID.replace('{subcategory_id}', subcategoryId)
      const response = await retryRequest(() =>
        apiClient.delete(url, {
          headers: authApi.getAuthHeaders(),
          params: {
            soft_delete: false, // 使用硬删除
            force: true, // 强制删除
          },
        }),
      )

      return {
        success: true,
        data: response.data,
        message: '子类目删除成功',
      }
    } catch (error) {
      console.error('[ItemsApi] Delete subcategory failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '子类目删除失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 更新子类目激活状态
   * @param {number} subcategoryId - 子类目ID
   * @param {boolean} isActive - 激活状态
   * @returns {Promise<Object>} 更新结果
   */
  async updateSubcategoryActiveStatus(subcategoryId, isActive) {
    try {
      const url = API_ENDPOINTS.ITEMS.SUBCATEGORY_BY_ID.replace('{subcategory_id}', subcategoryId)
      const response = await retryRequest(() =>
        apiClient.put(
          url,
          { is_active: isActive },
          {
            headers: authApi.getAuthHeaders(),
          },
        ),
      )

      return {
        success: true,
        data: response.data.data,
        message: response.data.message || `子类目${isActive ? '启用' : '停用'}成功`,
      }
    } catch (error) {
      console.error('[ItemsApi] Update subcategory active status failed:', error)
      throw {
        success: false,
        message:
          error.response?.data?.detail ||
          error.message ||
          `子类目${isActive ? '启用' : '停用'}失败`,
        error: error.response?.data,
      }
    }
  }

  // ==================== 物品管理 ====================

  /**
   * 获取物品列表
   * @param {Object} params - 查询参数
   * @param {number} params.category_id - 类目ID
   * @param {number} params.subcategory_id - 子类目ID
   * @param {boolean} params.include_inactive - 是否包含非活跃物品
   * @param {boolean} params.include_out_of_stock - 是否包含缺货物品
   * @param {number} params.page - 页码（默认1）
   * @param {number} params.page_size - 每页数量（默认50，最大100）
   * @returns {Promise<Object>} 物品列表
   */
  async getItems(params = {}) {
    try {
      // 设置默认参数
      const finalParams = {
        include_inactive: true, // 管理界面默认显示所有物品
        include_out_of_stock: true, // 管理界面默认显示缺货物品
        sort_by: 'sort_order', // 默认按排序值排序
        page: 1,
        page_size: 50,
        ...params,
      }

      const response = await retryRequest(() =>
        apiClient.get(API_ENDPOINTS.ITEMS.ITEMS_LIST, { params: finalParams }),
      )

      // 根据最新API文档处理响应格式
      const responseData = response.data

      return {
        success: responseData.success || true,
        data: responseData.data?.items || responseData.data || [],
        pagination: responseData.data?.pagination || null,
        message: responseData.message || '获取物品列表成功',
      }
    } catch (error) {
      console.error('[ItemsApi] Get items failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取物品列表失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 创建物品
   * @param {Object} itemData - 物品数据
   * @param {string} itemData.name - 物品名称
   * @param {string} itemData.item_code - 物品代码（支持普通字符串和JSON格式，最大2000字符）
   * @param {string} itemData.description - 物品描述
   * @param {number} itemData.category_id - 类目ID
   * @param {number} itemData.subcategory_id - 子类目ID（可选）
   * @param {number} itemData.price - 价格
   * @param {number} itemData.stock - 库存（-1表示无限库存）
   * @param {string} itemData.image_url - 图片URL（可选）
   * @returns {Promise<Object>} 创建结果
   */
  async createItem(itemData) {
    try {
      // 验证必填字段
      if (!itemData.name || !itemData.item_code || !itemData.category_id) {
        throw new Error('缺少必填字段：name, item_code, category_id')
      }

      // 验证物品代码长度（根据API文档最大2000字符）
      if (itemData.item_code.length > 2000) {
        throw new Error('物品代码长度不能超过2000字符')
      }

      // 如果是JSON格式，验证JSON有效性
      if (itemData.item_code.startsWith('{') && itemData.item_code.endsWith('}')) {
        try {
          JSON.parse(itemData.item_code)
        } catch (jsonError) {
          throw new Error('物品代码JSON格式无效')
        }
      }

      const response = await retryRequest(() =>
        apiClient.post(API_ENDPOINTS.ITEMS.ITEMS_LIST, itemData, {
          headers: authApi.getAuthHeaders(),
        }),
      )

      // 根据最新API文档处理响应格式
      const responseData = response.data

      return {
        success: responseData.success || true,
        data: responseData.data,
        message: responseData.message || '物品创建成功',
      }
    } catch (error) {
      console.error('[ItemsApi] Create item failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '物品创建失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 更新物品
   * @param {number} itemId - 物品ID
   * @param {Object} itemData - 物品数据
   * @param {string} itemData.name - 物品名称（可选）
   * @param {string} itemData.item_code - 物品代码（可选，支持JSON格式）
   * @param {string} itemData.description - 物品描述（可选）
   * @param {number} itemData.price - 价格（可选）
   * @param {number} itemData.stock - 库存（可选）
   * @param {boolean} itemData.is_active - 激活状态（可选）
   * @returns {Promise<Object>} 更新结果
   */
  async updateItem(itemId, itemData) {
    try {
      // 如果更新物品代码，验证JSON格式
      if (itemData.item_code) {
        // 验证物品代码长度
        if (itemData.item_code.length > 2000) {
          throw new Error('物品代码长度不能超过2000字符')
        }

        // 如果是JSON格式，验证JSON有效性
        if (itemData.item_code.startsWith('{') && itemData.item_code.endsWith('}')) {
          try {
            JSON.parse(itemData.item_code)
          } catch {
            throw new Error('物品代码JSON格式无效')
          }
        }
      }

      const url = API_ENDPOINTS.ITEMS.ITEM_BY_ID.replace('{item_id}', itemId)
      const response = await retryRequest(() =>
        apiClient.put(url, itemData, {
          headers: authApi.getAuthHeaders(),
        }),
      )

      // 根据最新API文档处理响应格式
      const responseData = response.data

      return {
        success: responseData.success || true,
        data: responseData.data,
        message: responseData.message || '物品更新成功',
      }
    } catch (error) {
      console.error('[ItemsApi] Update item failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '物品更新失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 删除物品（硬删除）
   * @param {number} itemId - 物品ID
   * @returns {Promise<Object>} 删除结果
   */
  async deleteItem(itemId) {
    try {
      const url = API_ENDPOINTS.ITEMS.ITEM_BY_ID.replace('{item_id}', itemId)
      const response = await retryRequest(() =>
        apiClient.delete(url, {
          headers: authApi.getAuthHeaders(),
          params: {
            soft_delete: false, // 使用硬删除
          },
        }),
      )

      return {
        success: true,
        data: response.data.data,
        message: response.data.message || '物品删除成功',
      }
    } catch (error) {
      console.error('[ItemsApi] Delete item failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '物品删除失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 更新物品激活状态
   * @param {number} itemId - 物品ID
   * @param {boolean} isActive - 激活状态
   * @returns {Promise<Object>} 更新结果
   */
  async updateItemActiveStatus(itemId, isActive) {
    try {
      const url = API_ENDPOINTS.ITEMS.ITEM_BY_ID.replace('{item_id}', itemId)
      const response = await retryRequest(() =>
        apiClient.put(
          url,
          { is_active: isActive },
          {
            headers: authApi.getAuthHeaders(),
          },
        ),
      )

      return {
        success: true,
        data: response.data.data,
        message: response.data.message || `物品${isActive ? '上架' : '下架'}成功`,
      }
    } catch (error) {
      console.error('[ItemsApi] Update item active status failed:', error)
      throw {
        success: false,
        message:
          error.response?.data?.detail || error.message || `物品${isActive ? '上架' : '下架'}失败`,
        error: error.response?.data,
      }
    }
  }

  /**
   * 搜索物品
   * @param {Object} params - 搜索参数
   * @param {string} params.keyword - 搜索关键词（必填）
   * @param {number} params.category_id - 类目ID（可选）
   * @param {number} params.subcategory_id - 子类目ID（可选）
   * @param {boolean} params.include_inactive - 是否包含非活跃物品
   * @param {number} params.page - 页码
   * @param {number} params.page_size - 每页数量
   * @returns {Promise<Object>} 搜索结果
   */
  async searchItems(params) {
    try {
      // 验证必填参数
      if (!params.keyword || !params.keyword.trim()) {
        throw new Error('搜索关键词不能为空')
      }

      // 设置默认参数
      const finalParams = {
        include_inactive: true,
        page: 1,
        page_size: 50,
        ...params,
      }

      const response = await retryRequest(() =>
        apiClient.get(API_ENDPOINTS.ITEMS.ITEMS_SEARCH, { params: finalParams }),
      )

      // 根据最新API文档处理响应格式
      const responseData = response.data

      return {
        success: responseData.success || true,
        data: responseData.data?.items || responseData.data || [],
        pagination: responseData.data?.pagination || null,
        search_keyword: finalParams.keyword,
        message: responseData.message || '搜索物品成功',
      }
    } catch (error) {
      console.error('[ItemsApi] Search items failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '搜索物品失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 上传物品图片
   * @param {string} itemCode - 物品代码（支持多行JSON格式）
   * @param {File} file - 图片文件
   * @returns {Promise<Object>} 上传结果
   */
  async uploadItemImage(itemCode, file) {
    try {
      // 验证参数
      if (!itemCode || !itemCode.trim()) {
        throw new Error('物品代码不能为空')
      }
      if (!file) {
        throw new Error('请选择要上传的图片文件')
      }

      const formData = new FormData()
      formData.append('file', file)

      // 对物品代码进行URL编码，处理多行和特殊字符
      const encodedItemCode = encodeURIComponent(itemCode.trim())

      const response = await retryRequest(() =>
        apiClient.post(
          API_ENDPOINTS.ITEMS.ITEM_UPLOAD_IMAGE.replace('{item_code}', encodedItemCode),
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
              ...authApi.getAuthHeaders(),
            },
          },
        ),
      )

      // 根据最新API文档处理响应格式
      const responseData = response.data

      return {
        success: responseData.success || true,
        data: responseData.data,
        message: responseData.message || '图片上传成功',
      }
    } catch (error) {
      console.error('[ItemsApi] Upload item image failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '图片上传失败',
        error: error.response?.data,
      }
    }
  }

  // ==================== 排序管理 ====================

  /**
   * 批量更新物品排序
   * @param {Object} sortData - 排序数据
   * @param {Array} sortData.items - 物品排序数组 [{"id": 1, "sort_order": 100}, ...]
   * @param {number} sortData.category_id - 可选的分类ID限制
   * @returns {Promise<Object>} 更新结果
   */
  async updateItemsSort(sortData) {
    try {
      // 验证必填参数
      if (!sortData.items || !Array.isArray(sortData.items) || sortData.items.length === 0) {
        throw new Error('物品排序数据不能为空')
      }

      // 验证每个物品数据格式
      for (const item of sortData.items) {
        if (!item.id || typeof item.sort_order !== 'number') {
          throw new Error('物品排序数据格式错误，需要包含id和sort_order字段')
        }
      }

      // 清理数据，确保类型正确
      const cleanData = {
        items: sortData.items.map((item) => {
          const id = typeof item.id === 'number' ? item.id : parseInt(item.id)
          const sort_order =
            typeof item.sort_order === 'number' ? item.sort_order : parseInt(item.sort_order)

          // 验证转换结果
          if (isNaN(id) || id <= 0) {
            throw new Error(`Invalid item ID: ${item.id}`)
          }
          if (isNaN(sort_order)) {
            throw new Error(`Invalid sort_order: ${item.sort_order}`)
          }

          return {
            id: id,
            sort_order: sort_order,
          }
        }),
      }

      // 只有在category_id有值时才添加
      if (
        sortData.category_id !== undefined &&
        sortData.category_id !== null &&
        sortData.category_id !== ''
      ) {
        const categoryId =
          typeof sortData.category_id === 'number'
            ? sortData.category_id
            : parseInt(sortData.category_id)

        if (isNaN(categoryId) || categoryId <= 0) {
          throw new Error(`Invalid category_id: ${sortData.category_id}`)
        }

        cleanData.category_id = categoryId
      }

      const headers = authApi.getAuthHeaders()

      const response = await retryRequest(() =>
        apiClient.put(API_ENDPOINTS.ITEMS.SORT_UPDATE, cleanData, {
          headers: {
            'Content-Type': 'application/json',
            ...headers,
          },
        }),
      )

      // 根据API文档处理响应格式
      const responseData = response.data

      return {
        success: responseData.success || true,
        data: responseData.data,
        message: responseData.message || '物品排序更新成功',
      }
    } catch (error) {
      console.error('[ItemsApi] Update items sort failed:', error)

      // 提取详细错误信息
      let errorMessage = '物品排序更新失败'
      if (error.response?.data?.detail) {
        if (Array.isArray(error.response.data.detail)) {
          errorMessage = error.response.data.detail.map((err) => err.msg || err).join(', ')
        } else {
          errorMessage = error.response.data.detail
        }
      } else if (error.message) {
        errorMessage = error.message
      }

      throw {
        success: false,
        message: errorMessage,
        error: error.response?.data,
      }
    }
  }

  /**
   * 重置物品排序
   * @param {Object} resetData - 重置参数
   * @param {number} resetData.category_id - 可选的分类ID
   * @param {number} resetData.subcategory_id - 可选的子分类ID
   * @param {number} resetData.start_value - 起始值，默认100
   * @param {number} resetData.interval - 间隔值，默认100
   * @returns {Promise<Object>} 重置结果
   */
  async resetItemsSort(resetData = {}) {
    try {
      const finalData = {
        start_value: 100,
        interval: 100,
        ...resetData,
      }

      const response = await retryRequest(() =>
        apiClient.post(API_ENDPOINTS.ITEMS.SORT_RESET, finalData, {
          headers: authApi.getAuthHeaders(),
        }),
      )

      // 根据API文档处理响应格式
      const responseData = response.data

      return {
        success: responseData.success || true,
        data: responseData.data,
        message: responseData.message || '物品排序重置成功',
      }
    } catch (error) {
      console.error('[ItemsApi] Reset items sort failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '物品排序重置失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 获取排序信息
   * @param {Object} params - 查询参数
   * @param {number} params.category_id - 可选的分类ID
   * @returns {Promise<Object>} 排序信息
   */
  async getSortInfo(params = {}) {
    try {
      const response = await retryRequest(() =>
        apiClient.get(API_ENDPOINTS.ITEMS.SORT_INFO, {
          params,
          headers: authApi.getAuthHeaders(),
        }),
      )

      // 根据API文档处理响应格式
      const responseData = response.data

      return {
        success: responseData.success || true,
        data: responseData.data,
        message: responseData.message || '获取排序信息成功',
      }
    } catch (error) {
      console.error('[ItemsApi] Get sort info failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取排序信息失败',
        error: error.response?.data,
      }
    }
  }
}

// 创建实例
export const itemsApi = new ItemsApi()

// 为了兼容性，导出类目和子类目API的别名
export const categoriesApi = itemsApi
export const subcategoriesApi = itemsApi

// 默认导出
export default itemsApi
