import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { robotApi } from '@/api/services/robotApi.js'
import { usersApi } from '@/api/services/usersApi.js'
import userManagementApi from '@/api/services/userManagementApi.js'
import { authApi } from '@/api/services/authApi.js'

export const useCartStore = defineStore('cart', () => {
  // 购物车商品列表
  const items = ref([])

  // 计算属性
  const itemCount = computed(() => items.value.reduce((total, item) => total + item.quantity, 0))
  const totalPrice = computed(() =>
    items.value.reduce((total, item) => total + item.price * item.quantity, 0),
  )
  const isEmpty = computed(() => items.value.length === 0)

  // 添加商品到购物车
  const addItem = (product) => {
    // 验证商品价格
    if (!product.isPriceValid || product.price == null || product.price <= 0) {
      console.error('[CartStore] 拒绝添加无效价格商品:', product.name, '价格:', product.price)
      throw new Error(`商品"${product.name}"价格无效，无法添加到购物车`)
    }

    const existingItem = items.value.find((item) => item.id === product.id)

    if (existingItem) {
      // 如果商品已存在，增加数量
      if (existingItem.quantity < existingItem.stock) {
        existingItem.quantity += product.quantity || 1
      }
    } else {
      // 如果商品不存在，添加新商品
      items.value.push({
        ...product,
        quantity: product.quantity || 1,
      })
    }
  }

  // 更新商品数量
  const updateQuantity = (productId, quantity) => {
    const item = items.value.find((item) => item.id === productId)
    if (item) {
      if (quantity <= 0) {
        removeItem(productId)
      } else if (quantity <= item.stock) {
        item.quantity = quantity
      }
    }
  }

  // 增加商品数量
  const increaseQuantity = (productId) => {
    const item = items.value.find((item) => item.id === productId)
    if (item) {
      // 检查库存限制：-1表示无限库存
      if (item.stock === -1 || item.quantity < item.stock) {
        item.quantity++
        console.log(`[CartStore] 增加商品数量: ${item.name}, 当前数量: ${item.quantity}`)
      } else {
        console.warn(`[CartStore] 无法增加商品数量: ${item.name}, 已达库存上限: ${item.stock}`)
      }
    }
  }

  // 减少商品数量
  const decreaseQuantity = (productId) => {
    const item = items.value.find((item) => item.id === productId)
    if (item) {
      if (item.quantity > 1) {
        item.quantity--
        console.log(`[CartStore] 减少商品数量: ${item.name}, 当前数量: ${item.quantity}`)
      } else {
        // 数量为1时，减少会移除商品
        console.log(`[CartStore] 商品数量为1，减少将移除商品: ${item.name}`)
        removeItem(productId)
      }
    }
  }

  // 移除商品
  const removeItem = (productId) => {
    const index = items.value.findIndex((item) => item.id === productId)
    if (index > -1) {
      items.value.splice(index, 1)
    }
  }

  // 清空购物车
  const clearCart = () => {
    items.value = []
  }

  // 获取特定商品在购物车中的数量
  const getItemQuantity = (productId) => {
    const item = items.value.find((item) => item.id === productId)
    return item ? item.quantity : 0
  }

  // 检查商品是否在购物车中
  const isInCart = (productId) => {
    return items.value.some((item) => item.id === productId)
  }

  // 将JSON格式的物品代码转换为原始命令格式
  const convertJsonToCommands = (itemCode) => {
    if (!itemCode) return ''

    try {
      const parsed = JSON.parse(itemCode)

      // 如果是数组格式
      if (Array.isArray(parsed)) {
        const commands = []
        for (const item of parsed) {
          if (item.command && item.item) {
            const amount = item.amount || 1
            commands.push(`${item.command} ${item.item} ${amount}`)
          }
        }
        return commands.join('\n')
      }

      // 如果是对象格式，转换为命令格式
      if (typeof parsed === 'object' && parsed !== null) {
        // 如果有item字段，转换为命令格式
        if (parsed.item) {
          const amount = parsed.amount || 1
          const command = parsed.command || '#spawnitem'
          return `${command} ${parsed.item} ${amount}`
        }

        // 如果是字典格式 {"item_name": quantity}
        const entries = Object.entries(parsed)
        if (entries.length > 0) {
          const commands = entries.map(([itemName, quantity]) => {
            return `#spawnitem ${itemName} ${quantity || 1}`
          })
          return commands.join('\n')
        }
      }
    } catch {
      // JSON解析失败，返回原始字符串
    }

    // 普通字符串或解析失败，直接返回
    return itemCode
  }

  // 解析物品代码，提取spawn命令
  const parseItemCode = (itemCode) => {
    console.log('[CartStore] parseItemCode 输入:', itemCode)
    console.log('[CartStore] parseItemCode 输入类型:', typeof itemCode)

    if (!itemCode || !itemCode.trim()) {
      console.log('[CartStore] parseItemCode 输入为空，返回空数组')
      return []
    }

    // 首先尝试将JSON格式转换为原始命令格式
    let processedItemCode = itemCode.trim()

    // 检查是否是JSON格式
    if (
      (processedItemCode.startsWith('[') && processedItemCode.endsWith(']')) ||
      (processedItemCode.startsWith('{') && processedItemCode.endsWith('}'))
    ) {
      console.log('[CartStore] 检测到JSON格式物品代码，转换为原始命令格式')
      processedItemCode = convertJsonToCommands(processedItemCode)
      console.log('[CartStore] 转换后的命令格式:', processedItemCode)
    }

    const lines = processedItemCode.split('\n').filter((line) => line.trim())
    console.log('[CartStore] 分割后的行数:', lines.length)
    lines.forEach((line, i) => {
      console.log(`[CartStore] 行 ${i + 1}: "${line}"`)
    })

    const commands = []

    for (const line of lines) {
      const trimmedLine = line.trim()
      console.log(`[CartStore] 处理行: "${trimmedLine}"`)

      if (trimmedLine.startsWith('#')) {
        console.log('[CartStore] 检测到#命令')
        // 解析所有#命令格式：#命令 参数1 参数2 ...
        const parts = trimmedLine.split(/\s+/)
        console.log('[CartStore] 分割后的部分:', parts)

        if (parts.length >= 2) {
          const command = parts[0] // #命令
          const item = parts[1] // 物品名称或货币类型
          const amount = parts.length >= 3 ? parseInt(parts[2]) || 1 : 1 // 数量，默认为1

          const cmdObj = {
            command: command,
            item: item,
            amount: amount,
          }

          console.log('[CartStore] 添加命令:', cmdObj)
          commands.push(cmdObj)
        } else {
          console.log('[CartStore] 命令格式不正确，跳过')
        }
      } else if (trimmedLine && !trimmedLine.startsWith('#')) {
        console.log('[CartStore] 检测到单个物品格式')
        // 单个物品格式，转换为 #spawnitem 命令
        const cmdObj = {
          command: '#spawnitem',
          item: trimmedLine,
          amount: 1,
        }
        console.log('[CartStore] 添加spawnitem命令:', cmdObj)
        commands.push(cmdObj)
      } else {
        console.log('[CartStore] 行不匹配任何格式，跳过')
      }
    }

    console.log('[CartStore] parseItemCode 最终解析结果:', commands)
    return commands
  }

  // 购买商品
  const purchase = async () => {
    try {
      console.log('[CartStore] 开始购买流程，购物车商品:', items.value)

      // 1. 检查购物车是否为空
      if (items.value.length === 0) {
        return {
          success: false,
          message: '购物车为空，无法购买',
        }
      }

      // 2. 计算总价并验证
      const totalCost = totalPrice.value
      console.log('[CartStore] 购买总价:', totalCost)

      // 验证总价是否有效
      if (totalCost <= 0) {
        console.error('[CartStore] 购买总价无效:', totalCost, '购物车商品:', items.value)
        return {
          success: false,
          message: `购买总价无效（¥${totalCost}），请检查商品价格或联系管理员`,
        }
      }

      // 检查购物车中是否有无效价格的商品
      const invalidPriceItems = items.value.filter(
        (item) => !item.isPriceValid || item.price == null || item.price <= 0,
      )
      if (invalidPriceItems.length > 0) {
        console.error('[CartStore] 发现无效价格商品:', invalidPriceItems)
        return {
          success: false,
          message: `购物车中包含价格无效的商品，请移除后重试`,
        }
      }

      // 3. 获取用户信息和资产
      const userInfo = authApi.getCurrentUserFromStorage()
      if (!userInfo || !userInfo.steam_id) {
        return {
          success: false,
          message: '无法获取用户信息，请重新登录',
        }
      }

      const userAssets = await usersApi.getUserAssets()
      if (!userAssets.success) {
        return {
          success: false,
          message: '无法获取用户资产信息',
        }
      }

      const currentShopCoins = userAssets.data?.data?.shop_coins || userAssets.data?.shop_coins || 0
      console.log('[CartStore] 当前商城币:', currentShopCoins)

      // 4. 检查商城币是否足够
      if (currentShopCoins < totalCost) {
        return {
          success: false,
          message: `商城币不足！需要 ${totalCost} 商城币，当前只有 ${currentShopCoins} 商城币`,
        }
      }

      // 5. 处理购物车中的每个商品
      const allCommands = []

      for (const item of items.value) {
        console.log('[CartStore] 处理商品:', item.name, '数量:', item.quantity)

        // 解析物品代码
        const commands = parseItemCode(item.item_code)

        // 根据购物车数量调整命令
        for (const cmd of commands) {
          const adjustedAmount = cmd.amount * item.quantity

          // 根据命令类型生成不同格式的命令
          let fullCommand
          if (cmd.command === '#ChangeCurrencyBalance') {
            // #ChangeCurrencyBalance 命令格式：#ChangeCurrencyBalance 货币类型 数量 SteamID
            fullCommand = `${cmd.command} ${cmd.item} ${adjustedAmount} ${userInfo.steam_id}`
          } else {
            // 其他命令格式：#命令 物品 数量 Location SteamID
            fullCommand = `${cmd.command} ${cmd.item} ${adjustedAmount} Location ${userInfo.steam_id}`
          }

          allCommands.push(fullCommand)
        }
      }

      console.log('[CartStore] 生成的SCUM命令:', allCommands)

      // 6. 逐个发送SCUM命令
      const commandResults = []
      for (let i = 0; i < allCommands.length; i++) {
        const command = allCommands[i]
        console.log(`[CartStore] 发送命令 ${i + 1}/${allCommands.length}:`, command)

        try {
          const result = await robotApi.sendSingleScumCommand(command)
          commandResults.push({ command, success: true, result })

          // 命令之间添加小延迟，避免服务器压力
          if (i < allCommands.length - 1) {
            await new Promise((resolve) => setTimeout(resolve, 500))
          }
        } catch (error) {
          console.error(`[CartStore] 命令发送失败:`, command, error)
          commandResults.push({ command, success: false, error })
          // 继续发送其他命令，不中断流程
        }
      }

      // 7. 扣除商城币
      try {
        const newShopCoins = currentShopCoins - totalCost
        await userManagementApi.updateUserAssets(userInfo.user_id || userInfo.id, {
          asset_type: 'shop_coins',
          amount: newShopCoins,
          operation: 'set',
        })
        console.log('[CartStore] 商城币扣除成功，剩余:', newShopCoins)
      } catch (error) {
        console.error('[CartStore] 扣除商城币失败:', error)
        return {
          success: false,
          message: '物品发放成功，但扣除商城币失败，请联系管理员',
        }
      }

      // 8. 统计结果
      const successCount = commandResults.filter((r) => r.success).length
      const failCount = commandResults.filter((r) => !r.success).length

      console.log('[CartStore] 购买完成，成功:', successCount, '失败:', failCount)

      // 9. 购买成功后清空购物车
      clearCart()

      return {
        success: true,
        message: `购买成功！共发送 ${allCommands.length} 个命令，成功 ${successCount} 个${failCount > 0 ? `，失败 ${failCount} 个` : ''}。已扣除 ${totalCost} 商城币。`,
        details: {
          totalCommands: allCommands.length,
          successCount,
          failCount,
          costDeducted: totalCost,
          remainingCoins: currentShopCoins - totalCost,
        },
      }
    } catch (error) {
      console.error('[CartStore] 购买失败:', error)
      return {
        success: false,
        message: error.message || '购买失败，请重试',
      }
    }
  }

  // 赠送商品
  const gift = async (recipientSteamId, message = '') => {
    try {
      console.log('[CartStore] 开始赠送流程，收件人:', recipientSteamId)

      // 1. 检查购物车是否为空
      if (items.value.length === 0) {
        return {
          success: false,
          message: '购物车为空，无法赠送',
        }
      }

      // 2. 验证收件人Steam ID格式
      if (!recipientSteamId || !recipientSteamId.trim()) {
        return {
          success: false,
          message: '请输入好友的Steam ID',
        }
      }

      // 简单的Steam ID格式验证（17位数字，以7656开头）
      const steamIdPattern = /^7656\d{13}$/
      if (!steamIdPattern.test(recipientSteamId.trim())) {
        return {
          success: false,
          message: 'Steam ID格式不正确，应为17位数字且以7656开头',
        }
      }

      // 3. 计算总价并验证
      const totalCost = totalPrice.value
      console.log('[CartStore] 赠送总价:', totalCost)

      // 验证总价是否有效
      if (totalCost <= 0) {
        return {
          success: false,
          message: `赠送总价无效（¥${totalCost}），请检查商品价格或联系管理员`,
        }
      }

      // 检查购物车中是否有无效价格的商品
      const invalidPriceItems = items.value.filter(
        (item) => !item.isPriceValid || item.price == null || item.price <= 0,
      )
      if (invalidPriceItems.length > 0) {
        return {
          success: false,
          message: `购物车中包含价格无效的商品，请移除后重试`,
        }
      }

      // 4. 获取用户信息和资产
      const userInfo = authApi.getCurrentUserFromStorage()
      if (!userInfo || !userInfo.steam_id) {
        return {
          success: false,
          message: '无法获取用户信息，请重新登录',
        }
      }

      const userAssets = await usersApi.getUserAssets()
      if (!userAssets.success) {
        return {
          success: false,
          message: '无法获取用户资产信息',
        }
      }

      const currentShopCoins = userAssets.data?.data?.shop_coins || userAssets.data?.shop_coins || 0
      console.log('[CartStore] 当前商城币:', currentShopCoins)

      // 5. 检查商城币是否足够
      if (currentShopCoins < totalCost) {
        return {
          success: false,
          message: `商城币不足！需要 ${totalCost} 商城币，当前只有 ${currentShopCoins} 商城币`,
        }
      }

      // 6. 处理购物车中的每个商品（使用好友的Steam ID）
      const allCommands = []

      for (const item of items.value) {
        console.log('[CartStore] 处理赠送商品:', item.name, '数量:', item.quantity)

        // 解析物品代码
        const commands = parseItemCode(item.item_code)

        // 根据购物车数量调整命令，使用好友的Steam ID
        for (const cmd of commands) {
          const adjustedAmount = cmd.amount * item.quantity

          // 根据命令类型生成不同格式的命令
          let fullCommand
          if (cmd.command === '#ChangeCurrencyBalance') {
            // #ChangeCurrencyBalance 命令格式：#ChangeCurrencyBalance 货币类型 数量 SteamID
            fullCommand = `${cmd.command} ${cmd.item} ${adjustedAmount} ${recipientSteamId.trim()}`
          } else {
            // 其他命令格式：#命令 物品 数量 Location SteamID
            fullCommand = `${cmd.command} ${cmd.item} ${adjustedAmount} Location ${recipientSteamId.trim()}`
          }

          allCommands.push(fullCommand)
        }
      }

      console.log('[CartStore] 生成的赠送SCUM命令:', allCommands)

      // 7. 逐个发送SCUM命令
      const commandResults = []
      for (let i = 0; i < allCommands.length; i++) {
        const command = allCommands[i]
        console.log(`[CartStore] 发送赠送命令 ${i + 1}/${allCommands.length}:`, command)

        try {
          const result = await robotApi.sendSingleScumCommand(command)
          commandResults.push({ command, success: true, result })

          // 命令之间添加小延迟，避免服务器压力
          if (i < allCommands.length - 1) {
            await new Promise((resolve) => setTimeout(resolve, 500))
          }
        } catch (error) {
          console.error(`[CartStore] 赠送命令发送失败:`, command, error)
          commandResults.push({ command, success: false, error })
          // 继续发送其他命令，不中断流程
        }
      }

      // 7.5. 如果有赠送留言，发送全图广播
      if (message && message.trim()) {
        console.log('[CartStore] 发送赠送留言广播:', message.trim())

        try {
          // 在所有命令发送完后添加延迟，然后发送广播
          await new Promise((resolve) => setTimeout(resolve, 1000))

          const announceCommand = `#Announce ${message.trim()}`
          console.log('[CartStore] 发送广播命令:', announceCommand)

          const announceResult = await robotApi.sendSingleScumCommand(announceCommand)
          commandResults.push({ command: announceCommand, success: true, result: announceResult })
          console.log('[CartStore] 赠送留言广播发送成功')
        } catch (error) {
          console.error('[CartStore] 赠送留言广播发送失败:', error)
          commandResults.push({ command: `#Announce ${message.trim()}`, success: false, error })
          // 广播失败不影响整体赠送流程
        }
      }

      // 8. 扣除相应商城币
      try {
        const newShopCoins = currentShopCoins - totalCost
        await userManagementApi.updateUserAssets(userInfo.user_id || userInfo.id, {
          asset_type: 'shop_coins',
          amount: newShopCoins,
          operation: 'set',
        })
        console.log('[CartStore] 赠送商城币扣除成功，剩余:', newShopCoins)
      } catch (error) {
        console.error('[CartStore] 扣除商城币失败:', error)
        return {
          success: false,
          message: '物品赠送成功，但扣除商城币失败，请联系管理员',
        }
      }

      // 9. 统计结果
      const successCount = commandResults.filter((r) => r.success).length
      const failCount = commandResults.filter((r) => !r.success).length
      const totalCommandsSent = commandResults.length

      console.log(
        '[CartStore] 赠送完成，总命令:',
        totalCommandsSent,
        '成功:',
        successCount,
        '失败:',
        failCount,
      )

      // 10. 清空购物车并返回结果
      clearCart()

      // 构建结果消息
      let resultMessage = `赠送成功！已发送给 ${recipientSteamId}，共发送 ${totalCommandsSent} 个命令，成功 ${successCount} 个${failCount > 0 ? `，失败 ${failCount} 个` : ''}。已扣除 ${totalCost} 商城币。`

      if (message && message.trim()) {
        resultMessage += `\n留言已全图广播：${message.trim()}`
      }

      return {
        success: true,
        message: resultMessage,
        details: {
          recipient: recipientSteamId,
          message: message,
          itemCommands: allCommands.length,
          totalCommands: totalCommandsSent,
          successCount,
          failCount,
          costDeducted: totalCost,
          remainingCoins: currentShopCoins - totalCost,
          announceSent: message && message.trim() ? true : false,
        },
      }
    } catch (error) {
      console.error('[CartStore] 赠送失败:', error)
      return {
        success: false,
        message: '赠送失败，请重试',
      }
    }
  }

  // 从localStorage加载购物车数据
  const loadFromStorage = () => {
    try {
      const savedCart = localStorage.getItem('cart')
      if (savedCart) {
        items.value = JSON.parse(savedCart)
      }
    } catch (error) {
      console.error('加载购物车数据失败:', error)
    }
  }

  // 保存购物车数据到localStorage
  const saveToStorage = () => {
    try {
      localStorage.setItem('cart', JSON.stringify(items.value))
    } catch (error) {
      console.error('保存购物车数据失败:', error)
    }
  }

  // 监听购物车变化，自动保存到localStorage
  const startAutoSave = () => {
    // 使用watch监听items变化
    import('vue').then(({ watch }) => {
      watch(
        items,
        () => {
          saveToStorage()
        },
        { deep: true },
      )
    })
  }

  return {
    // 状态
    items,

    // 计算属性
    itemCount,
    totalPrice,
    isEmpty,

    // 方法
    addItem,
    updateQuantity,
    increaseQuantity,
    decreaseQuantity,
    removeItem,
    clearCart,
    getItemQuantity,
    isInCart,
    purchase,
    gift,
    loadFromStorage,
    saveToStorage,
    startAutoSave,
  }
})
