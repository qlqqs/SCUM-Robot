import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { itemsApi } from '@/api/services/itemsApi.js'

export const useGameStore = defineStore('gameStore', () => {
  // 状态
  const categories = ref([])
  const subcategories = ref([])
  const items = ref([])

  // 加载状态
  const loading = ref({
    categories: false,
    subcategories: false,
    items: false,
    init: false,
  })

  // 错误状态
  const errors = ref({
    categories: null,
    subcategories: null,
    items: null,
    init: null,
  })

  // 计算属性
  const isLoading = computed(() => Object.values(loading.value).some(Boolean))
  const hasErrors = computed(() => Object.values(errors.value).some(Boolean))

  // 统计信息计算属性
  const getStats = computed(() => ({
    totalCategories: categories.value.length,
    activeCategories: categories.value.filter((cat) => cat.is_active !== false).length,
    totalSubcategories: subcategories.value.length,
    activeSubcategories: subcategories.value.filter((sub) => sub.is_active !== false).length,
    totalItems: items.value.length,
    activeItems: items.value.filter((item) => item.is_active !== false).length,
    lowStockItems: items.value.filter((item) => item.stock_quantity < 10).length,
    outOfStockItems: items.value.filter((item) => item.stock_quantity === 0).length,
  }))

  // 清除错误
  const clearError = (type) => {
    if (type) {
      errors.value[type] = null
    } else {
      Object.keys(errors.value).forEach((key) => {
        errors.value[key] = null
      })
    }
  }

  // 初始化默认数据
  const initializeFallbackData = async () => {
    categories.value = [
      { id: 1, name: '武器', description: '各种武器装备' },
      { id: 2, name: '食物', description: '食物和饮料' },
      { id: 3, name: '工具', description: '工具和设备' },
    ]

    subcategories.value = [
      { id: 1, category_id: 1, name: '近战武器' },
      { id: 2, category_id: 1, name: '远程武器' },
      { id: 3, category_id: 2, name: '肉类' },
      { id: 4, category_id: 2, name: '蔬菜' },
    ]

    items.value = [
      { id: 1, name: '步枪', category_id: 1, subcategory_id: 2, price: 100, stock: 10 },
      { id: 2, name: '牛肉', category_id: 2, subcategory_id: 3, price: 20, stock: 50 },
    ]
  }

  // 初始化数据 - 从API获取
  const initializeData = async () => {
    loading.value.init = true
    errors.value.init = null

    try {
      // 并行加载类目、子类目和物品数据
      await Promise.all([loadCategories(), loadSubcategories(), loadItems()])
      console.log('[GameStore] Data initialized successfully')
    } catch (error) {
      console.error('[GameStore] Failed to initialize data:', error)
      errors.value.init = error.message || '初始化数据失败'
      // 如果API失败，使用本地默认数据
      await initializeFallbackData()
    } finally {
      loading.value.init = false
    }
  }

  // 加载类目数据
  const loadCategories = async (params = {}) => {
    loading.value.categories = true
    errors.value.categories = null

    try {
      console.log('[GameStore] Loading categories...')
      // 设置默认参数，确保包含非活跃类目
      const finalParams = {
        include_inactive: true,
        page: 1,
        page_size: 100, // 加载更多类目
        ...params,
      }
      const response = await itemsApi.getCategories(finalParams)
      console.log('[GameStore] Categories API response:', response)

      if (response.success && response.data) {
        // 根据最新API文档处理响应数据
        categories.value = Array.isArray(response.data) ? response.data : []
        console.log('[GameStore] Loaded categories:', categories.value.length, 'categories')
        console.log('[GameStore] Categories data:', categories.value)

        // 如果有分页信息，记录日志
        if (response.pagination) {
          console.log('[GameStore] Categories pagination:', response.pagination)
        }
      } else {
        console.warn('[GameStore] Categories response not successful or no data:', response)
        categories.value = []
      }
    } catch (error) {
      console.error('[GameStore] Failed to load categories:', error)
      errors.value.categories = error.message || '加载类目失败'
      // 确保在错误时categories仍然是数组
      categories.value = []
      throw error
    } finally {
      loading.value.categories = false
    }
  }

  // 加载子类目数据
  const loadSubcategories = async () => {
    loading.value.subcategories = true
    errors.value.subcategories = null

    try {
      console.log('[GameStore] Loading subcategories...')
      const response = await itemsApi.getSubcategories({ include_inactive: true })
      console.log('[GameStore] Subcategories API response:', response)

      if (response.success && response.data) {
        // 确保subcategories是数组
        subcategories.value = Array.isArray(response.data) ? response.data : []
        console.log(
          '[GameStore] Loaded subcategories:',
          subcategories.value.length,
          'subcategories',
        )
        console.log('[GameStore] Subcategories data:', subcategories.value)
      } else {
        console.warn('[GameStore] Subcategories response not successful or no data:', response)
        subcategories.value = []
      }
    } catch (error) {
      console.error('[GameStore] Failed to load subcategories:', error)
      errors.value.subcategories = error.message || '加载子类目失败'
      // 确保在错误时subcategories仍然是数组
      subcategories.value = []
      throw error
    } finally {
      loading.value.subcategories = false
    }
  }

  // 加载物品数据
  const loadItems = async (params = {}) => {
    loading.value.items = true
    errors.value.items = null

    try {
      console.log('[GameStore] Loading items...')
      // 设置默认参数，确保包含非活跃物品和缺货物品
      const finalParams = {
        include_inactive: true,
        include_out_of_stock: true,
        page: 1,
        page_size: 100, // 加载更多物品
        ...params,
      }
      const response = await itemsApi.getItems(finalParams)
      console.log('[GameStore] Items API response:', response)

      if (response.success && response.data) {
        // 根据最新API文档处理响应数据
        items.value = Array.isArray(response.data) ? response.data : []
        console.log('[GameStore] Loaded items:', items.value.length, 'items')
        console.log('[GameStore] Items data:', items.value)

        // 如果有分页信息，记录日志
        if (response.pagination) {
          console.log('[GameStore] Items pagination:', response.pagination)
        }
      } else {
        console.warn('[GameStore] Items response not successful or no data:', response)
        items.value = []
      }
    } catch (error) {
      console.error('[GameStore] Failed to load items:', error)
      errors.value.items = error.message || '加载物品失败'
      // 确保在错误时items仍然是数组
      items.value = []
      throw error
    } finally {
      loading.value.items = false
    }
  }

  // 刷新所有数据
  const refreshData = async () => {
    try {
      await Promise.all([loadCategories(), loadSubcategories(), loadItems()])
    } catch (error) {
      console.error('[GameStore] Failed to refresh data:', error)
    }
  }

  // 搜索物品
  const searchItems = async (keyword, params = {}) => {
    try {
      const searchParams = { keyword, ...params }
      const response = await itemsApi.searchItems(searchParams)
      if (response.success && response.data) {
        return response.data
      }
      return []
    } catch (error) {
      console.error('[GameStore] Failed to search items:', error)
      return []
    }
  }

  // 获取指定类目的物品
  const getItemsByCategory = (categoryId) => {
    return items.value.filter((item) => item.category_id === categoryId)
  }

  // 获取指定子类目的物品
  const getItemsBySubcategory = (subcategoryId) => {
    return items.value.filter((item) => item.subcategory_id === subcategoryId)
  }

  // 获取类目名称
  const getCategoryName = (categoryId) => {
    const category = categories.value.find((c) => c.id === categoryId)
    return category ? category.name : '未分类'
  }

  // 获取子类目名称
  const getSubcategoryName = (subcategoryId) => {
    const subcategory = subcategories.value.find((s) => s.id === subcategoryId)
    return subcategory ? subcategory.name : '未分类'
  }

  // 更新类目
  const updateCategory = async (categoryId, categoryData) => {
    try {
      const response = await itemsApi.updateCategory(categoryId, categoryData)
      if (response.success) {
        // 重新加载类目数据
        await loadCategories()
      }
      return response
    } catch (error) {
      console.error('[GameStore] Failed to update category:', error)
      throw error
    }
  }

  // 更新子类目
  const updateSubcategory = async (subcategoryId, subcategoryData) => {
    try {
      const response = await itemsApi.updateSubcategory(subcategoryId, subcategoryData)
      if (response.success) {
        // 重新加载子类目数据
        await loadSubcategories()
      }
      return response
    } catch (error) {
      console.error('[GameStore] Failed to update subcategory:', error)
      throw error
    }
  }

  // 添加类目
  const addCategory = async (name, description = '') => {
    try {
      console.log('[GameStore] Creating category:', { name, description })
      const response = await itemsApi.createCategory({ name, description })
      console.log('[GameStore] Create category response:', response)

      if (response.success) {
        console.log('[GameStore] Category created successfully, reloading categories...')
        // 重新加载类目数据
        await loadCategories()
        console.log('[GameStore] Categories reloaded, current count:', categories.value.length)
      }
      return response
    } catch (error) {
      console.error('[GameStore] Failed to add category:', error)
      throw error
    }
  }

  // 添加子类目
  const addSubcategory = async (categoryId, name, description = '') => {
    try {
      const response = await itemsApi.createSubcategory({
        category_id: categoryId,
        name,
        description,
      })
      if (response.success) {
        // 重新加载子类目数据
        await loadSubcategories()
      }
      return response
    } catch (error) {
      console.error('[GameStore] Failed to add subcategory:', error)
      throw error
    }
  }

  // 添加物品
  const addItem = async (itemData) => {
    try {
      console.log('[GameStore] Creating item:', itemData)

      // 验证必填字段
      if (!itemData.name || !itemData.item_code || !itemData.category_id) {
        throw new Error('缺少必填字段：name, item_code, category_id')
      }

      // 如果物品代码是JSON格式，记录日志
      if (itemData.item_code.startsWith('{') && itemData.item_code.endsWith('}')) {
        console.log('[GameStore] Creating item with JSON item_code')
        try {
          const parsedCode = JSON.parse(itemData.item_code)
          console.log('[GameStore] Parsed JSON item_code:', parsedCode)
        } catch (error) {
          console.warn('[GameStore] Invalid JSON in item_code:', error)
        }
      }

      const response = await itemsApi.createItem(itemData)
      console.log('[GameStore] Create item response:', response)

      if (response.success) {
        console.log('[GameStore] Item created successfully, reloading items...')
        // 重新加载物品数据
        await loadItems()
        console.log('[GameStore] Items reloaded, current count:', items.value.length)
      }
      return response
    } catch (error) {
      console.error('[GameStore] Failed to add item:', error)
      throw error
    }
  }

  // 更新物品
  const updateItem = async (itemId, itemData) => {
    try {
      console.log('[GameStore] Updating item:', itemId, itemData)
      const response = await itemsApi.updateItem(itemId, itemData)
      console.log('[GameStore] Update item response:', response)

      if (response.success) {
        console.log('[GameStore] Item updated successfully, reloading items...')
        // 重新加载物品数据
        await loadItems()
        console.log('[GameStore] Items reloaded, current count:', items.value.length)
      }
      return response
    } catch (error) {
      console.error('[GameStore] Failed to update item:', error)
      throw error
    }
  }

  // 删除物品
  const deleteItem = async (itemId) => {
    try {
      console.log('[GameStore] Deleting item:', itemId)
      const response = await itemsApi.deleteItem(itemId)
      console.log('[GameStore] Delete item response:', response)

      if (response.success) {
        console.log('[GameStore] Item deleted successfully, reloading items...')
        // 重新加载物品数据
        await loadItems()
        console.log('[GameStore] Items reloaded, current count:', items.value.length)
      }
      return response
    } catch (error) {
      console.error('[GameStore] Failed to delete item:', error)
      throw error
    }
  }

  // 上传物品图片
  const uploadItemImage = async (itemCode, file) => {
    try {
      console.log('[GameStore] Uploading item image:', itemCode, file.name)
      const response = await itemsApi.uploadItemImage(itemCode, file)
      console.log('[GameStore] Upload image response:', response)

      if (response.success) {
        console.log('[GameStore] Image uploaded successfully')
        // 可以选择重新加载物品数据以获取新的图片URL
        await loadItems()
      }
      return response
    } catch (error) {
      console.error('[GameStore] Failed to upload item image:', error)
      throw error
    }
  }

  // 更新类目激活状态
  const updateCategoryActiveStatus = async (categoryId, isActive) => {
    try {
      console.log('[GameStore] Updating category active status:', categoryId, isActive)
      const response = await itemsApi.updateCategoryActiveStatus(categoryId, isActive)
      console.log('[GameStore] Update category status response:', response)

      if (response.success) {
        console.log('[GameStore] Category status updated successfully, reloading categories...')
        // 重新加载类目数据
        await loadCategories()
        console.log('[GameStore] Categories reloaded, current count:', categories.value.length)
      }
      return response
    } catch (error) {
      console.error('[GameStore] Failed to update category active status:', error)
      throw error
    }
  }

  // 删除类目
  const deleteCategory = async (categoryId) => {
    try {
      console.log('[GameStore] Deleting category:', categoryId)
      const response = await itemsApi.deleteCategory(categoryId)
      console.log('[GameStore] Delete category response:', response)

      if (response.success) {
        console.log('[GameStore] Category deleted successfully, reloading categories...')
        // 重新加载类目数据
        await loadCategories()
        console.log('[GameStore] Categories reloaded, current count:', categories.value.length)
      }
      return response
    } catch (error) {
      console.error('[GameStore] Failed to delete category:', error)
      throw error
    }
  }

  // 更新子类目激活状态
  const updateSubcategoryActiveStatus = async (subcategoryId, isActive) => {
    try {
      console.log('[GameStore] Updating subcategory active status:', subcategoryId, isActive)
      const response = await itemsApi.updateSubcategoryActiveStatus(subcategoryId, isActive)
      console.log('[GameStore] Update subcategory status response:', response)

      if (response.success) {
        console.log(
          '[GameStore] Subcategory status updated successfully, reloading subcategories...',
        )
        // 重新加载子类目数据
        await loadSubcategories()
        console.log(
          '[GameStore] Subcategories reloaded, current count:',
          subcategories.value.length,
        )
      }
      return response
    } catch (error) {
      console.error('[GameStore] Failed to update subcategory active status:', error)
      throw error
    }
  }

  // 删除子类目
  const deleteSubcategory = async (subcategoryId) => {
    try {
      console.log('[GameStore] Deleting subcategory:', subcategoryId)
      const response = await itemsApi.deleteSubcategory(subcategoryId)
      console.log('[GameStore] Delete subcategory response:', response)

      if (response.success) {
        console.log('[GameStore] Subcategory deleted successfully, reloading subcategories...')
        // 重新加载子类目数据
        await loadSubcategories()
        console.log(
          '[GameStore] Subcategories reloaded, current count:',
          subcategories.value.length,
        )
      }
      return response
    } catch (error) {
      console.error('[GameStore] Failed to delete subcategory:', error)
      throw error
    }
  }

  return {
    // 状态
    categories,
    subcategories,
    items,
    loading,
    errors,

    // 计算属性
    isLoading,
    hasErrors,
    getStats,

    // 方法
    clearError,
    initializeData,
    loadCategories,
    loadSubcategories,
    loadItems,
    refreshData,
    searchItems,
    getItemsByCategory,
    getItemsBySubcategory,
    getCategoryName,
    getSubcategoryName,
    updateCategory,
    updateSubcategory,
    addCategory,
    addSubcategory,
    addItem,
    updateItem,
    deleteItem,
    uploadItemImage,
    updateCategoryActiveStatus,
    deleteCategory,
    updateSubcategoryActiveStatus,
    deleteSubcategory,
  }
})
