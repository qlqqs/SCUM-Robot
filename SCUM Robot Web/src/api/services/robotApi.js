/**
 * Robot控制API服务
 */
import apiClient, { retryRequest } from '../client.js'
import { API_ENDPOINTS } from '../config.js'

/**
 * Robot API类
 */
class RobotApi {
  /**
   * 获取Robot API状态
   * @returns {Promise<Object>} API响应
   */
  async getStatus() {
    try {
      const response = await retryRequest(() => apiClient.get(API_ENDPOINTS.ROBOT.STATUS))

      return {
        success: true,
        data: response.data,
        message: '获取Robot状态成功',
      }
    } catch (error) {
      console.error('[RobotApi] Get status failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取Robot状态失败',
        error: error.response?.data,
      }
    }
  }

  // ==================== 玩家货币管理 ====================

  /**
   * 改变玩家货币
   * @param {string} steamId - Steam ID
   * @param {string} currencyType - 货币类型
   * @param {number} amount - 金额
   * @param {string} reason - 原因
   * @returns {Promise<Object>} API响应
   */
  async changePlayerCurrency(steamId, currencyType, amount, reason = '') {
    try {
      const response = await retryRequest(() =>
        apiClient.post(API_ENDPOINTS.ROBOT.PLAYER_CURRENCY_CHANGE, {
          steam_id: steamId,
          currency_type: currencyType,
          amount: amount,
          reason: reason,
        }),
      )

      return {
        success: true,
        data: response.data.data,
        message: '改变玩家货币成功',
      }
    } catch (error) {
      console.error('[RobotApi] Change player currency failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '改变玩家货币失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 设置玩家货币
   * @param {string} steamId - Steam ID
   * @param {string} currencyType - 货币类型
   * @param {number} amount - 金额
   * @param {string} reason - 原因
   * @returns {Promise<Object>} API响应
   */
  async setPlayerCurrency(steamId, currencyType, amount, reason = '') {
    try {
      const response = await retryRequest(() =>
        apiClient.post(API_ENDPOINTS.ROBOT.PLAYER_CURRENCY_SET, {
          steam_id: steamId,
          currency_type: currencyType,
          amount: amount,
          reason: reason,
        }),
      )

      return {
        success: true,
        data: response.data.data,
        message: '设置玩家货币成功',
      }
    } catch (error) {
      console.error('[RobotApi] Set player currency failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '设置玩家货币失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 改变所有玩家货币
   * @param {string} currencyType - 货币类型
   * @param {number} amount - 金额
   * @param {string} reason - 原因
   * @returns {Promise<Object>} API响应
   */
  async changeAllPlayersCurrency(currencyType, amount, reason = '') {
    try {
      const response = await retryRequest(() =>
        apiClient.post(API_ENDPOINTS.ROBOT.PLAYER_CURRENCY_CHANGE_ALL, {
          currency_type: currencyType,
          amount: amount,
          reason: reason,
        }),
      )

      return {
        success: true,
        data: response.data.data,
        message: '改变所有玩家货币成功',
      }
    } catch (error) {
      console.error('[RobotApi] Change all players currency failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '改变所有玩家货币失败',
        error: error.response?.data,
      }
    }
  }

  // ==================== 玩家声望管理 ====================

  /**
   * 改变玩家声望
   * @param {string} steamId - Steam ID
   * @param {number} amount - 声望值
   * @param {string} reason - 原因
   * @returns {Promise<Object>} API响应
   */
  async changePlayerFame(steamId, amount, reason = '') {
    try {
      const response = await retryRequest(() =>
        apiClient.post(API_ENDPOINTS.ROBOT.PLAYER_FAME_CHANGE, {
          steam_id: steamId,
          amount: amount,
          reason: reason,
        }),
      )

      return {
        success: true,
        data: response.data.data,
        message: '改变玩家声望成功',
      }
    } catch (error) {
      console.error('[RobotApi] Change player fame failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '改变玩家声望失败',
        error: error.response?.data,
      }
    }
  }

  // ==================== 管理员功能 ====================

  /**
   * 发送公告
   * @param {string} message - 公告内容
   * @param {number} duration - 显示时长(秒)
   * @returns {Promise<Object>} API响应
   */
  async sendAnnouncement(message, duration = 10) {
    try {
      const response = await retryRequest(() =>
        apiClient.post(API_ENDPOINTS.ROBOT.ADMIN_ANNOUNCE, {
          message: message,
          duration: duration,
        }),
      )

      return {
        success: true,
        data: response.data.data,
        message: '发送公告成功',
      }
    } catch (error) {
      console.error('[RobotApi] Send announcement failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '发送公告失败',
        error: error.response?.data,
      }
    }
  }

  // ==================== 传送功能 ====================

  /**
   * 传送到坐标
   * @param {string} steamId - Steam ID
   * @param {number} x - X坐标
   * @param {number} y - Y坐标
   * @param {number} z - Z坐标
   * @returns {Promise<Object>} API响应
   */
  async teleportToCoordinates(steamId, x, y, z) {
    try {
      const response = await retryRequest(() =>
        apiClient.post(API_ENDPOINTS.ROBOT.TELEPORT_COORDINATES, {
          steam_id: steamId,
          x: x,
          y: y,
          z: z,
        }),
      )

      return {
        success: true,
        data: response.data.data,
        message: '传送成功',
      }
    } catch (error) {
      console.error('[RobotApi] Teleport to coordinates failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '传送失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 传送玩家到玩家
   * @param {string} fromSteamId - 源玩家Steam ID
   * @param {string} toSteamId - 目标玩家Steam ID
   * @returns {Promise<Object>} API响应
   */
  async teleportPlayerToPlayer(fromSteamId, toSteamId) {
    try {
      const response = await retryRequest(() =>
        apiClient.post(API_ENDPOINTS.ROBOT.TELEPORT_PLAYER, {
          from_steam_id: fromSteamId,
          to_steam_id: toSteamId,
        }),
      )

      return {
        success: true,
        data: response.data.data,
        message: '传送成功',
      }
    } catch (error) {
      console.error('[RobotApi] Teleport player to player failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '传送失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 传送玩家到我
   * @param {string} steamId - Steam ID
   * @returns {Promise<Object>} API响应
   */
  async teleportPlayerToMe(steamId) {
    try {
      const response = await retryRequest(() =>
        apiClient.post(API_ENDPOINTS.ROBOT.TELEPORT_TO_ME, {
          steam_id: steamId,
        }),
      )

      return {
        success: true,
        data: response.data.data,
        message: '传送成功',
      }
    } catch (error) {
      console.error('[RobotApi] Teleport player to me failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '传送失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 随机传送
   * @param {string} steamId - Steam ID
   * @returns {Promise<Object>} API响应
   */
  async teleportRandom(steamId) {
    try {
      const response = await retryRequest(() =>
        apiClient.post(API_ENDPOINTS.ROBOT.TELEPORT_RANDOM, {
          steam_id: steamId,
        }),
      )

      return {
        success: true,
        data: response.data.data,
        message: '随机传送成功',
      }
    } catch (error) {
      console.error('[RobotApi] Random teleport failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '随机传送失败',
        error: error.response?.data,
      }
    }
  }

  // ==================== 生成功能 ====================

  /**
   * 生成物品
   * @param {string} steamId - Steam ID
   * @param {string} itemCode - 物品代码
   * @param {number} quantity - 数量
   * @returns {Promise<Object>} API响应
   */
  async spawnItem(steamId, itemCode, quantity = 1) {
    try {
      const response = await retryRequest(() =>
        apiClient.post(API_ENDPOINTS.ROBOT.SPAWN_ITEM, {
          steam_id: steamId,
          item_code: itemCode,
          quantity: quantity,
        }),
      )

      return {
        success: true,
        data: response.data.data,
        message: '生成物品成功',
      }
    } catch (error) {
      console.error('[RobotApi] Spawn item failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '生成物品失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 生成动物
   * @param {string} steamId - Steam ID
   * @param {string} animalType - 动物类型
   * @param {number} quantity - 数量
   * @returns {Promise<Object>} API响应
   */
  async spawnAnimal(steamId, animalType, quantity = 1) {
    try {
      const response = await retryRequest(() =>
        apiClient.post(API_ENDPOINTS.ROBOT.SPAWN_ANIMAL, {
          steam_id: steamId,
          animal_type: animalType,
          quantity: quantity,
        }),
      )

      return {
        success: true,
        data: response.data.data,
        message: '生成动物成功',
      }
    } catch (error) {
      console.error('[RobotApi] Spawn animal failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '生成动物失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 生成僵尸
   * @param {string} steamId - Steam ID
   * @param {string} zombieType - 僵尸类型
   * @param {number} quantity - 数量
   * @returns {Promise<Object>} API响应
   */
  async spawnZombie(steamId, zombieType, quantity = 1) {
    try {
      const response = await retryRequest(() =>
        apiClient.post(API_ENDPOINTS.ROBOT.SPAWN_ZOMBIE, {
          steam_id: steamId,
          zombie_type: zombieType,
          quantity: quantity,
        }),
      )

      return {
        success: true,
        data: response.data.data,
        message: '生成僵尸成功',
      }
    } catch (error) {
      console.error('[RobotApi] Spawn zombie failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '生成僵尸失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 生成载具
   * @param {string} steamId - Steam ID
   * @param {string} vehicleType - 载具类型
   * @returns {Promise<Object>} API响应
   */
  async spawnVehicle(steamId, vehicleType) {
    try {
      const response = await retryRequest(() =>
        apiClient.post(API_ENDPOINTS.ROBOT.SPAWN_VEHICLE, {
          steam_id: steamId,
          vehicle_type: vehicleType,
        }),
      )

      return {
        success: true,
        data: response.data.data,
        message: '生成载具成功',
      }
    } catch (error) {
      console.error('[RobotApi] Spawn vehicle failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '生成载具失败',
        error: error.response?.data,
      }
    }
  }

  // ==================== 预设功能 ====================

  /**
   * 发放新手礼包
   * @param {string} steamId - Steam ID
   * @returns {Promise<Object>} API响应
   */
  async giveStarterPackage(steamId) {
    try {
      const response = await retryRequest(() =>
        apiClient.post(API_ENDPOINTS.ROBOT.STARTER_PACKAGE, {
          steam_id: steamId,
        }),
      )

      return {
        success: true,
        data: response.data.data,
        message: '发放新手礼包成功',
      }
    } catch (error) {
      console.error('[RobotApi] Give starter package failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '发放新手礼包失败',
        error: error.response?.data,
      }
    }
  }

  // ==================== 命令功能 ====================

  /**
   * 发送自定义命令
   * @param {string} command - 命令内容
   * @returns {Promise<Object>} API响应
   */
  async sendCommand(command) {
    try {
      const response = await retryRequest(() =>
        apiClient.post(API_ENDPOINTS.ROBOT.COMMAND_SEND, {
          command: command,
        }),
      )

      return {
        success: true,
        data: response.data.data,
        message: '发送命令成功',
      }
    } catch (error) {
      console.error('[RobotApi] Send command failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '发送命令失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 发送SCUM命令
   * @param {string} command - SCUM命令
   * @param {Object} params - 命令参数
   * @returns {Promise<Object>} API响应
   */
  async sendScumCommand(command, params = {}) {
    try {
      const response = await retryRequest(() =>
        apiClient.post(API_ENDPOINTS.ROBOT.COMMAND_SCUM, {
          command: command,
          params: params,
        }),
      )

      return {
        success: true,
        data: response.data.data,
        message: '发送SCUM命令成功',
      }
    } catch (error) {
      console.error('[RobotApi] Send SCUM command failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '发送SCUM命令失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 发送单个SCUM命令（简化版本）
   * @param {string} command - 完整的SCUM命令字符串
   * @returns {Promise<Object>} API响应
   */
  async sendSingleScumCommand(command) {
    try {
      const response = await retryRequest(() =>
        apiClient.post(API_ENDPOINTS.ROBOT.COMMAND_SCUM, {
          command: command,
        }),
      )

      return {
        success: true,
        data: response.data.data || response.data,
        message: '发送SCUM命令成功',
      }
    } catch (error) {
      console.error('[RobotApi] Send single SCUM command failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '发送SCUM命令失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 发送Windows命令
   * @param {string} command - Windows命令
   * @returns {Promise<Object>} API响应
   */
  async sendWindowsCommand(command) {
    try {
      const response = await retryRequest(() =>
        apiClient.post(API_ENDPOINTS.ROBOT.COMMAND_WINDOWS, {
          command: command,
        }),
      )

      return {
        success: true,
        data: response.data.data,
        message: '发送Windows命令成功',
      }
    } catch (error) {
      console.error('[RobotApi] Send Windows command failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '发送Windows命令失败',
        error: error.response?.data,
      }
    }
  }

  // ==================== 工具功能 ====================

  /**
   * 获取货币类型列表
   * @returns {Promise<Object>} API响应
   */
  async getCurrencyTypes() {
    try {
      const response = await retryRequest(() =>
        apiClient.get(API_ENDPOINTS.ROBOT.TOOLS_CURRENCY_TYPES),
      )

      return {
        success: true,
        data: response.data.data,
        message: '获取货币类型成功',
      }
    } catch (error) {
      console.error('[RobotApi] Get currency types failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取货币类型失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 获取修饰符类型列表
   * @returns {Promise<Object>} API响应
   */
  async getModifierTypes() {
    try {
      const response = await retryRequest(() =>
        apiClient.get(API_ENDPOINTS.ROBOT.TOOLS_MODIFIER_TYPES),
      )

      return {
        success: true,
        data: response.data.data,
        message: '获取修饰符类型成功',
      }
    } catch (error) {
      console.error('[RobotApi] Get modifier types failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取修饰符类型失败',
        error: error.response?.data,
      }
    }
  }

  /**
   * 获取示例数据
   * @returns {Promise<Object>} API响应
   */
  async getExamples() {
    try {
      const response = await retryRequest(() => apiClient.get(API_ENDPOINTS.ROBOT.TOOLS_EXAMPLES))

      return {
        success: true,
        data: response.data.data,
        message: '获取示例数据成功',
      }
    } catch (error) {
      console.error('[RobotApi] Get examples failed:', error)
      throw {
        success: false,
        message: error.response?.data?.detail || error.message || '获取示例数据失败',
        error: error.response?.data,
      }
    }
  }
}

// 创建实例
export const robotApi = new RobotApi()

// 默认导出
export default robotApi
