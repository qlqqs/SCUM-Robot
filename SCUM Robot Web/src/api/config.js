/**
 * API配置文件
 */

export const DEFAULT_API_BASE_URL = 'http://localhost:8000'

function normalizeBaseUrl(baseUrl) {
  return baseUrl.replace(/\/+$/, '')
}

export function resolveApiBaseUrl(baseUrl = import.meta.env.VITE_API_BASE_URL) {
  const normalizedValue = (baseUrl || '').trim()
  return normalizeBaseUrl(normalizedValue || DEFAULT_API_BASE_URL)
}

export function buildApiUrl(path = '') {
  const baseUrl = API_CONFIG.BASE_URL
  if (!path) {
    return baseUrl
  }

  if (/^https?:\/\//i.test(path)) {
    return path
  }

  return path.startsWith('/') ? `${baseUrl}${path}` : `${baseUrl}/${path}`
}

// API基础配置
export const API_CONFIG = {
  // 后端API基础URL
  BASE_URL: resolveApiBaseUrl(),

  // API版本
  API_VERSION: 'v1',

  // 请求超时时间（毫秒）
  TIMEOUT: 10000,

  // 重试次数
  RETRY_COUNT: 3,

  // 重试延迟（毫秒）
  RETRY_DELAY: 1000,
}

// API端点配置
export const API_ENDPOINTS = {
  // 认证系统
  AUTH: {
    REGISTER: '/api/v1/auth/register',
    LOGIN: '/api/v1/auth/login',
    REFRESH: '/api/v1/auth/refresh',
    ME: '/api/v1/auth/me',
  },

  // 用户管理
  USERS: {
    GET_USER: '/api/v1/users/{user_id}',
    UPDATE_USER: '/api/v1/users/{user_id}',
    LIST_USERS: '/api/v1/users',
    DELETE_USER: '/api/v1/users/{user_id}',
    UPDATE_PERMISSIONS: '/api/v1/users/{user_id}/permissions',
    TOGGLE_STATUS: '/api/v1/users/{user_id}/toggle-status',
    RESET_USER_PASSWORD: '/api/v1/users/{user_id}/reset-password',
    GET_USER_STATS: '/api/v1/character/stats',
    GET_USER_ASSETS: '/api/v1/users/assets',
    UPDATE_USER_ASSETS: '/api/v1/users/{user_id}/assets',
    SEARCH_USERS: '/api/v1/users/search',
    GET_ONLINE_USERS: '/api/v1/users/online',

    // 管理员专用端点
    LIST: '/api/v1/admin/users',
    DETAIL: '/api/v1/admin/users/{user_id}',
    UPDATE: '/api/v1/admin/users/{user_id}',
    DELETE: '/api/v1/admin/users/{user_id}',
    BATCH_OPERATE: '/api/v1/admin/users/batch',
    RESET_PASSWORD: '/api/v1/admin/users/{user_id}/reset-password',
    STATISTICS: '/api/v1/admin/users/statistics',
  },

  // 签到系统
  SIGNIN: {
    STATUS: '/api/v1/signin/status',
    DAILY: '/api/v1/signin/daily',
    HISTORY: '/api/v1/signin/history',
    LEADERBOARD: '/api/v1/signin/leaderboard',
  },

  // 礼包系统
  GIFTS: {
    // 用户接口
    AVAILABLE: '/api/v1/gifts/available',
    CLAIM: '/api/v1/gifts/{gift_id}/claim',
    HISTORY: '/api/v1/gifts/history',

    // 管理员接口
    CREATE: '/api/v1/gifts',
    GET_ALL: '/api/v1/gifts/admin/all',
    GET_ONE: '/api/v1/gifts/{gift_id}',
    UPDATE: '/api/v1/gifts/{gift_id}',
    DELETE: '/api/v1/gifts/{gift_id}',
    UPLOAD_IMAGE: '/api/v1/gifts/{gift_id}/upload-image',
  },

  // VIP系统
  VIP: {
    // 用户接口
    STATUS: '/api/v1/vip/status',
    CONFIGS: '/api/v1/vip/configs',
    CONFIG_BY_LEVEL: '/api/v1/vip/config/{level}',
    PERMISSIONS_SHOP: '/api/v1/vip/permissions/shop',
    TELEPORT_PERMISSION: '/api/v1/vip/shop/teleport-permission',

    // 管理员接口
    CREATE_CONFIG: '/api/v1/vip/config',
    UPDATE_CONFIG: '/api/v1/vip/config/{level}',
    DELETE_CONFIG: '/api/v1/vip/config/{level}',
    UPGRADE_USER: '/api/v1/vip/upgrade',
    BATCH_UPGRADE: '/api/v1/vip/batch-upgrade',
    ADMIN_UPGRADE: '/api/v1/vip/admin/upgrade',
    STATISTICS: '/api/v1/vip/statistics',
  },

  // 人物能力
  CHARACTER: {
    STATS: '/api/v1/character/stats',
    STATS_BY_STEAM: '/api/v1/character/stats/steam/{steam_id}',
    LEADERBOARD: '/api/v1/character/leaderboard',
    SUMMARY: '/api/v1/character/summary',
    ADMIN_UPDATE_STATS: '/api/v1/character/admin/stats/{steam_id}',
    ADMIN_SYNC: '/api/v1/character/admin/sync',
  },

  // 物品管理
  ITEMS: {
    // 类目相关
    CATEGORIES: '/api/v1/items/categories',
    CATEGORY_BY_ID: '/api/v1/items/categories/{category_id}',
    CATEGORIES_WITH_SUBCATEGORIES: '/api/v1/items/categories-with-subcategories',

    // 子类目相关
    SUBCATEGORIES: '/api/v1/items/subcategories',
    SUBCATEGORY_BY_ID: '/api/v1/items/subcategories/{subcategory_id}',

    // 物品相关
    ITEMS_LIST: '/api/v1/items/items',
    ITEM_BY_ID: '/api/v1/items/items/{item_id}',
    ITEMS_SEARCH: '/api/v1/items/items/search',
    ITEM_UPLOAD_IMAGE: '/api/v1/items/{item_code}/upload-image', // 修复：根据API文档，图片上传端点不包含 /items

    // 排序相关
    SORT_UPDATE: '/api/v1/items/items/batch-sort',
    SORT_RESET: '/api/v1/items/items/sort/reset',
    SORT_INFO: '/api/v1/items/items/sort/info',
  },

  // 管理员功能
  ADMIN: {
    STATS: '/api/v1/admin/stats',
    SIGNIN_STATS: '/api/v1/signin/admin/stats',
    VIP_STATS: '/api/v1/vip/admin/stats',
  },

  // 系统设置 (使用configs端点)
  SETTINGS: {
    GET_ALL: '/api/v1/configs',
    GET_BY_CATEGORY: '/api/v1/configs/category/{category}',
    GET_BY_KEY: '/api/v1/configs/{key}',
    UPDATE_SETTING: '/api/v1/configs/{key}',
    UPDATE_BATCH: '/api/v1/configs/batch',
    RESET_SETTING: '/api/v1/configs/{key}/reset',
    RESET_CATEGORY: '/api/v1/configs/category/{category}/reset',
    RESET_ALL: '/api/v1/configs/reset',
    EXPORT: '/api/v1/configs/export',
    IMPORT: '/api/v1/configs/import',
  },

  // Robot API端点
  ROBOT: {
    STATUS: '/api/v1/robot/',

    // 玩家货币相关
    PLAYER_CURRENCY_CHANGE: '/api/v1/robot/player/currency/change',
    PLAYER_CURRENCY_SET: '/api/v1/robot/player/currency/set',
    PLAYER_CURRENCY_CHANGE_ALL: '/api/v1/robot/player/currency/change-all',

    // 玩家声望相关
    PLAYER_FAME_CHANGE: '/api/v1/robot/player/fame/change',

    // 管理员功能
    ADMIN_ANNOUNCE: '/api/v1/robot/admin/announce',

    // 传送相关
    TELEPORT_COORDINATES: '/api/v1/robot/teleport/coordinates',
    TELEPORT_PLAYER: '/api/v1/robot/teleport/player',
    TELEPORT_TO_ME: '/api/v1/robot/teleport/to-me',
    TELEPORT_RANDOM: '/api/v1/robot/teleport/random',

    // 生成相关
    SPAWN_ITEM: '/api/v1/robot/spawn/item',
    SPAWN_ANIMAL: '/api/v1/robot/spawn/animal',
    SPAWN_ZOMBIE: '/api/v1/robot/spawn/zombie',
    SPAWN_VEHICLE: '/api/v1/robot/spawn/vehicle',

    // 预设功能
    STARTER_PACKAGE: '/api/v1/robot/preset/starter-package',

    // 命令相关
    COMMAND_SEND: '/api/v1/robot/command/send',
    COMMAND_SCUM: '/api/v1/robot/command/scum',
    COMMAND_WINDOWS: '/api/v1/robot/command/windows',

    // 工具相关
    TOOLS_CURRENCY_TYPES: '/api/v1/robot/tools/currency-types',
    TOOLS_MODIFIER_TYPES: '/api/v1/robot/tools/modifier-types',
    TOOLS_EXAMPLES: '/api/v1/robot/tools/examples',
  },

  // 数据库/SQL相关
  SQL: {
    DATABASE_INIT: '/api/v1/items/database/init',
    DATABASE_STATUS: '/api/v1/items/database/status',
    DATABASE_RESET: '/api/v1/items/database/reset',
    DATABASE_BACKUP: '/api/v1/items/database/backup',
    DATABASE_RESTORE: '/api/v1/items/database/restore',
    DATABASE_STATISTICS: '/api/v1/items/database/statistics',
    DATABASE_CLEANUP: '/api/v1/items/database/cleanup',
    DATABASE_OPTIMIZE: '/api/v1/items/database/optimize',
    DATABASE_INTEGRITY: '/api/v1/items/database/integrity',
    DATABASE_REPAIR: '/api/v1/items/database/repair',
    DATABASE_CONFIG: '/api/v1/items/database/config',
    DATABASE_LOGS: '/api/v1/items/database/logs',
    DATABASE_QUERY: '/api/v1/items/database/query',
    DATABASE_TABLES: '/api/v1/items/database/tables',
    DATABASE_INDEXES: '/api/v1/items/database/indexes',
  },

  // 健康检查
  HEALTH: '/api/health',
}

// HTTP状态码
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  INTERNAL_SERVER_ERROR: 500,
}

// 错误消息
export const ERROR_MESSAGES = {
  NETWORK_ERROR: '网络连接错误，请检查网络连接',
  TIMEOUT_ERROR: '请求超时，请稍后重试',
  SERVER_ERROR: '服务器错误，请稍后重试',
  NOT_FOUND: '请求的资源不存在',
  UNAUTHORIZED: '未授权访问',
  FORBIDDEN: '禁止访问',
  VALIDATION_ERROR: '数据验证失败',
  UNKNOWN_ERROR: '未知错误',
}
