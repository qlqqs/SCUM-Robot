/**
 * 系统配置状态管理
 * 提供响应式的系统配置数据
 *
 * 注意：所有配置现在从后端API获取，不再使用localStorage
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { API_CONFIG } from '@/api/config.js'
import { settingsApi } from '@/api/services/settingsApi.js'

export const useSystemConfigStore = defineStore('systemConfig', () => {
  // 配置数据（默认值）
  const config = ref({
    site: {
      name: 'SCUM Robot Web',
      description: 'SCUM游戏机器人管理系统',
      maintenanceMode: false,
      debugMode: false,
    },
    currency: {
      gameCurrency: '游戏币',
      shopCurrency: '商城币',
    },
    pagination: {
      storeItems: 3,
      categories: 10,
      subcategories: 10,
      items: 10,
    },
    api: {
      baseUrl: API_CONFIG.BASE_URL,
      timeout: 10000,
    },
    user: {
      registrationEnabled: true,
      defaultCurrency: 1000,
      defaultShopCurrency: 100,
      maxCartItems: 50,
      sessionTimeout: 1440,
      passwordMinLength: 6,
      autoLogoutEnabled: true,
    },
    features: {
      passEnabled: true,
      teleportEnabled: true,
      giftsEnabled: true,
    },
    exchange: {
      rmbToShopCurrency: 10,
      gameToShopCurrency: 100,
      rmbToPoints: 100,
    },
    messages: {
      publicScreenEnabled: true,
      giftPrefix: '[系统礼包]',
    },
  })

  // 加载状态
  const loading = ref(false)
  const lastUpdated = ref(null)
  const error = ref(null)

  // 计算属性
  const gameCurrencyName = computed(() => config.value.currency.gameCurrency)
  const shopCurrencyName = computed(() => config.value.currency.shopCurrency)
  const storeItemsPerPage = computed(() => config.value.pagination.storeItems)
  const categoriesPerPage = computed(() => config.value.pagination.categories)
  const subcategoriesPerPage = computed(() => config.value.pagination.subcategories)
  const itemsPerPage = computed(() => config.value.pagination.items)
  const siteName = computed(() => config.value.site.name)
  const siteDescription = computed(() => config.value.site.description)
  const isMaintenanceMode = computed(() => config.value.site.maintenanceMode)
  const isDebugMode = computed(() => config.value.site.debugMode)
  const apiBaseUrl = computed(() => config.value.api.baseUrl)
  const apiTimeout = computed(() => config.value.api.timeout)

  // 用户配置计算属性
  const userRegistrationEnabled = computed(() => config.value.user.registrationEnabled)
  const userDefaultCurrency = computed(() => config.value.user.defaultCurrency)
  const userDefaultShopCurrency = computed(() => config.value.user.defaultShopCurrency)
  const userMaxCartItems = computed(() => config.value.user.maxCartItems)
  const userSessionTimeout = computed(() => config.value.user.sessionTimeout)
  const userPasswordMinLength = computed(() => config.value.user.passwordMinLength)
  const userAutoLogoutEnabled = computed(() => config.value.user.autoLogoutEnabled)

  // 功能开关配置
  const passEnabled = computed(() => config.value.features?.passEnabled !== false)
  const teleportEnabled = computed(() => config.value.features?.teleportEnabled !== false)
  const giftsEnabled = computed(() => config.value.features?.giftsEnabled !== false)

  // 货币兑换配置
  const rmbToShopCurrencyRate = computed(() => config.value.exchange?.rmbToShopCurrency || 10)
  const gameToShopCurrencyRate = computed(() => config.value.exchange?.gameToShopCurrency || 100)
  const rmbToPointsRate = computed(() => config.value.exchange?.rmbToPoints || 100)

  // 消息配置
  const publicScreenEnabled = computed(() => config.value.messages?.publicScreenEnabled !== false)
  const giftMessagePrefix = computed(() => config.value.messages?.giftPrefix || '[系统礼包]')

  /**
   * 从后端加载系统配置
   */
  const loadConfig = async () => {
    loading.value = true
    error.value = null
    try {
      console.log('[SystemConfigStore] Loading config from backend...')
      const response = await settingsApi.getAllSettings()

      if (response.success && response.data) {
        // 将后端返回的设置数组转换为配置对象
        const settings = response.data
        console.log('[SystemConfigStore] Received settings:', settings.length)

        // 映射后端设置到前端配置结构
        const newConfig = {
          site: {
            name: getSetting(settings, 'site_name', 'SCUM Robot Web'),
            description: getSetting(settings, 'site_description', 'SCUM游戏机器人管理系统'),
            maintenanceMode: getSetting(settings, 'maintenance_mode', false),
            debugMode: getSetting(settings, 'debug_mode', false),
          },
          currency: {
            gameCurrency: getSetting(settings, 'game_currency_name', '游戏币'),
            shopCurrency: getSetting(settings, 'shop_currency_name', '商城币'),
          },
          pagination: {
            storeItems: getSetting(settings, 'store_items_per_page', 3),
            categories: getSetting(settings, 'categories_per_page', 10),
            subcategories: getSetting(settings, 'subcategories_per_page', 10),
            items: getSetting(settings, 'items_per_page', 10),
          },
          api: {
            baseUrl: getSetting(settings, 'api_base_url', API_CONFIG.BASE_URL),
            timeout: getSetting(settings, 'api_timeout', 10000),
          },
          user: {
            registrationEnabled: getSetting(settings, 'user_registration_enabled', true),
            defaultCurrency: getSetting(settings, 'user_default_currency', 1000),
            defaultShopCurrency: getSetting(settings, 'user_default_shop_currency', 100),
            maxCartItems: getSetting(settings, 'user_max_cart_items', 50),
            sessionTimeout: getSetting(settings, 'user_session_timeout', 1440),
            passwordMinLength: getSetting(settings, 'user_password_min_length', 6),
            autoLogoutEnabled: getSetting(settings, 'user_auto_logout_enabled', true),
          },
          features: {
            passEnabled: getSetting(settings, 'feature_pass_enabled', true),
            teleportEnabled: getSetting(settings, 'feature_teleport_enabled', true),
            giftsEnabled: getSetting(settings, 'feature_gifts_enabled', true),
          },
          exchange: {
            rmbToShopCurrency: getSetting(settings, 'exchange_rmb_to_shop_currency', 10),
            gameToShopCurrency: getSetting(settings, 'exchange_game_to_shop_currency', 100),
            rmbToPoints: getSetting(settings, 'exchange_rmb_to_points', 100),
          },
          messages: {
            publicScreenEnabled: getSetting(settings, 'message_public_screen_enabled', true),
            giftPrefix: getSetting(settings, 'message_gift_prefix', '[系统礼包]'),
          },
        }

        config.value = newConfig
        lastUpdated.value = new Date()
        console.log('[SystemConfigStore] Config loaded successfully')
      } else {
        throw new Error(response.message || '获取配置失败')
      }
    } catch (err) {
      console.error('[SystemConfigStore] Failed to load config:', err)
      error.value = err.message || '加载配置失败'
      // 保持使用默认配置
    } finally {
      loading.value = false
    }
  }

  /**
   * 从设置数组中获取指定键的值
   * @param {Array} settings - 设置数组
   * @param {string} key - 设置键名
   * @param {any} defaultValue - 默认值
   * @returns {any} 设置值
   */
  const getSetting = (settings, key, defaultValue) => {
    const setting = settings.find((s) => s.key === key)
    return setting?.value ?? defaultValue
  }

  /**
   * 刷新配置
   */
  const refreshConfig = async () => {
    await loadConfig()
  }

  /**
   * 获取货币配置
   */
  const getCurrencyConfig = () => {
    return {
      gameCurrency: gameCurrencyName.value,
      shopCurrency: shopCurrencyName.value,
    }
  }

  /**
   * 获取分页配置
   */
  const getPaginationConfig = () => {
    return {
      storeItems: storeItemsPerPage.value,
      categories: categoriesPerPage.value,
      subcategories: subcategoriesPerPage.value,
      items: itemsPerPage.value,
    }
  }

  /**
   * 获取站点配置
   */
  const getSiteConfig = () => {
    return {
      name: siteName.value,
      description: siteDescription.value,
      maintenanceMode: isMaintenanceMode.value,
      debugMode: isDebugMode.value,
    }
  }

  /**
   * 获取API配置
   */
  const getApiConfig = () => {
    return {
      baseUrl: apiBaseUrl.value,
      timeout: apiTimeout.value,
    }
  }

  /**
   * 更新单个配置项
   */
  const updateConfigItem = (path, value) => {
    const keys = path.split('.')
    let target = config.value

    for (let i = 0; i < keys.length - 1; i++) {
      if (!target[keys[i]]) {
        target[keys[i]] = {}
      }
      target = target[keys[i]]
    }

    target[keys[keys.length - 1]] = value
    lastUpdated.value = new Date()
  }

  /**
   * 批量更新配置
   */
  const updateConfig = (newConfig) => {
    config.value = { ...config.value, ...newConfig }
    lastUpdated.value = new Date()
  }

  /**
   * 重置配置到默认值
   */
  const resetConfig = async () => {
    await loadConfig()
  }

  return {
    // 状态
    config,
    loading,
    lastUpdated,
    error,

    // 计算属性
    gameCurrencyName,
    shopCurrencyName,
    storeItemsPerPage,
    categoriesPerPage,
    subcategoriesPerPage,
    itemsPerPage,
    siteName,
    siteDescription,
    isMaintenanceMode,
    isDebugMode,
    apiBaseUrl,
    apiTimeout,

    // 用户配置
    userRegistrationEnabled,
    userDefaultCurrency,
    userDefaultShopCurrency,
    userMaxCartItems,
    userSessionTimeout,
    userPasswordMinLength,
    userAutoLogoutEnabled,

    // 功能开关配置
    passEnabled,
    teleportEnabled,
    giftsEnabled,

    // 货币兑换配置
    rmbToShopCurrencyRate,
    gameToShopCurrencyRate,
    rmbToPointsRate,

    // 消息配置
    publicScreenEnabled,
    giftMessagePrefix,

    // 方法
    loadConfig,
    refreshConfig,
    getCurrencyConfig,
    getPaginationConfig,
    getSiteConfig,
    getApiConfig,
    updateConfigItem,
    updateConfig,
    resetConfig,
  }
})

// 导出便捷的组合式函数
export const useSystemConfig = () => {
  const store = useSystemConfigStore()

  return {
    // 货币配置
    gameCurrencyName: store.gameCurrencyName,
    shopCurrencyName: store.shopCurrencyName,
    getCurrencyConfig: store.getCurrencyConfig,

    // 分页配置
    storeItemsPerPage: store.storeItemsPerPage,
    categoriesPerPage: store.categoriesPerPage,
    subcategoriesPerPage: store.subcategoriesPerPage,
    itemsPerPage: store.itemsPerPage,
    getPaginationConfig: store.getPaginationConfig,

    // 站点配置
    siteName: store.siteName,
    siteDescription: store.siteDescription,
    isMaintenanceMode: store.isMaintenanceMode,
    isDebugMode: store.isDebugMode,
    getSiteConfig: store.getSiteConfig,

    // API配置
    apiBaseUrl: store.apiBaseUrl,
    apiTimeout: store.apiTimeout,
    getApiConfig: store.getApiConfig,

    // 用户配置
    userRegistrationEnabled: store.userRegistrationEnabled,
    userDefaultCurrency: store.userDefaultCurrency,
    userDefaultShopCurrency: store.userDefaultShopCurrency,
    userMaxCartItems: store.userMaxCartItems,
    userSessionTimeout: store.userSessionTimeout,
    userPasswordMinLength: store.userPasswordMinLength,
    userAutoLogoutEnabled: store.userAutoLogoutEnabled,

    // 工具方法
    loadConfig: store.loadConfig,
    refreshConfig: store.refreshConfig,
    updateConfig: store.updateConfig,
    resetConfig: store.resetConfig,
  }
}
