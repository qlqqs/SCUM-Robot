<template>
  <div
    data-cart-view
    class="flex flex-col h-screen bg-cover bg-center bg-fixed text-gray-200"
    style="
      background-image: url('https://images.unsplash.com/photo-1504829857797-ddff29c27927?q=80&w=2070&auto=format&fit=crop');
    "
  >
    <!-- Header -->
    <GameHeader
      :user-info="userInfo"
      :user-stats="userStats"
      :user-assets="userAssets"
      @logout="handleLogout"
    />

    <!-- Main Content -->
    <main class="flex-grow p-4 lg:p-6 overflow-y-auto">
      <div class="w-4/5 mx-auto bg-gray-800 bg-opacity-60 backdrop-blur-md rounded-lg p-4 lg:p-6">
        <!-- Cart Header -->
        <div class="flex flex-col sm:flex-row justify-between items-center mb-6 gap-4">
          <div class="flex items-center gap-3">
            <i class="fas fa-shopping-cart text-2xl text-orange-400"></i>
            <h1 class="text-2xl font-bold text-white">购物车</h1>
            <span class="bg-orange-600 text-white text-sm px-2 py-1 rounded-full">
              {{ cartItems.length }} 件商品
            </span>
          </div>
          <div class="flex items-center gap-2">
            <button
              @click="goToStore"
              class="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
            >
              <i class="fas fa-store mr-1"></i>
              继续购物
            </button>
            <button
              @click="clearCart"
              :disabled="cartItems.length === 0"
              class="px-4 py-2 text-sm bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors disabled:opacity-50"
            >
              <i class="fas fa-trash mr-1"></i>
              清空购物车
            </button>
          </div>
        </div>

        <!-- Cart Content -->
        <div v-if="cartItems.length === 0" class="text-center py-12">
          <i class="fas fa-shopping-cart text-6xl text-gray-500 mb-4"></i>
          <h2 class="text-xl font-semibold text-gray-400 mb-2">购物车是空的</h2>
          <p class="text-gray-500 mb-6">快去商店挑选一些商品吧！</p>
          <button
            @click="goToStore"
            class="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
          >
            <i class="fas fa-store mr-2"></i>
            前往商店
          </button>
        </div>

        <div v-else class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <!-- Cart Items -->
          <div class="lg:col-span-2">
            <div class="space-y-4">
              <div
                v-for="item in cartItems"
                :key="item.id"
                class="bg-gray-900 bg-opacity-50 rounded-lg p-4 flex items-center gap-4 transition-transform transform hover:-translate-y-1"
              >
                <!-- Item Image -->
                <div class="flex-shrink-0">
                  <img
                    :src="item.image"
                    :alt="item.name"
                    class="w-16 h-16 object-cover rounded-md"
                  />
                </div>

                <!-- Item Info -->
                <div class="flex-grow">
                  <h3 class="text-lg font-semibold text-white mb-1">{{ item.name }}</h3>
                  <p v-if="item.stock !== -1" class="text-sm text-gray-400 mb-1">
                    库存: {{ item.stock }}
                  </p>
                  <p class="text-lg font-bold text-yellow-400">¥{{ item.price.toFixed(2) }}</p>
                </div>

                <!-- Quantity Controls -->
                <div class="flex items-center gap-2">
                  <button
                    @click="decreaseQuantity(item)"
                    :disabled="item.quantity <= 1"
                    :title="item.quantity <= 1 ? '数量为1时点击将移除商品' : '减少数量'"
                    class="w-8 h-8 bg-gray-700 hover:bg-gray-600 text-white rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <i class="fas fa-minus"></i>
                  </button>

                  <!-- 数量输入框 -->
                  <input
                    v-model.number="item.quantity"
                    @blur="validateAndUpdateQuantity(item)"
                    @keyup.enter="validateAndUpdateQuantity(item)"
                    type="number"
                    min="1"
                    :max="item.stock === -1 ? 999 : item.stock"
                    class="w-16 h-8 text-center bg-gray-800 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />

                  <button
                    @click="increaseQuantity(item)"
                    :disabled="item.stock !== -1 && item.quantity >= item.stock"
                    :title="getIncreaseButtonTitle(item)"
                    class="w-8 h-8 bg-gray-700 hover:bg-gray-600 text-white rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <i class="fas fa-plus"></i>
                  </button>

                  <!-- 删除按钮 -->
                  <button
                    @click="confirmRemoveItem(item)"
                    title="移除商品"
                    class="w-8 h-8 bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors ml-2"
                  >
                    <i class="fas fa-trash"></i>
                  </button>
                </div>

                <!-- Item Total -->
                <div class="text-right">
                  <p class="text-lg font-bold text-yellow-400">
                    ¥{{ (item.price * item.quantity).toFixed(2) }}
                  </p>
                </div>

                <!-- Remove Button -->
                <button
                  @click="removeFromCart(item)"
                  class="w-8 h-8 bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors"
                  title="移除商品"
                >
                  <i class="fas fa-times"></i>
                </button>
              </div>
            </div>
          </div>

          <!-- Cart Summary -->
          <div class="lg:col-span-1">
            <div class="bg-gray-900 bg-opacity-50 rounded-lg p-6 sticky top-4">
              <h2 class="text-xl font-bold text-white mb-4">订单摘要</h2>

              <!-- Summary Details -->
              <div class="space-y-3 mb-6">
                <div class="flex justify-between text-gray-300">
                  <span>商品数量:</span>
                  <span>{{ totalItems }} 件</span>
                </div>
                <div class="flex justify-between text-gray-300">
                  <span>商品总价:</span>
                  <span>¥{{ totalPrice.toFixed(2) }}</span>
                </div>
                <div class="flex justify-between text-gray-300">
                  <span>运费:</span>
                  <span class="text-green-400">免费</span>
                </div>
                <hr class="border-gray-600" />
                <div class="flex justify-between text-xl font-bold text-yellow-400">
                  <span>总计:</span>
                  <span>¥{{ totalPrice.toFixed(2) }}</span>
                </div>
              </div>

              <!-- Action Buttons -->
              <div class="space-y-3">
                <button
                  @click="handlePurchase"
                  :disabled="cartItems.length === 0 || hasInvalidPriceItems || totalPrice <= 0"
                  :class="[
                    'w-full py-3 font-semibold rounded-md transition-colors',
                    cartItems.length === 0 || hasInvalidPriceItems || totalPrice <= 0
                      ? 'bg-gray-600 text-gray-400 cursor-not-allowed opacity-50'
                      : 'bg-green-600 hover:bg-green-700 text-white',
                  ]"
                  :title="
                    hasInvalidPriceItems
                      ? '购物车中包含价格无效的商品'
                      : totalPrice <= 0
                        ? '购买总价无效'
                        : '立即购买'
                  "
                >
                  <i class="fas fa-credit-card mr-2"></i>
                  <span v-if="hasInvalidPriceItems">价格异常</span>
                  <span v-else-if="totalPrice <= 0">总价无效</span>
                  <span v-else>立即购买</span>
                </button>
                <button
                  @click="handleGift"
                  :disabled="cartItems.length === 0"
                  class="w-full py-3 bg-purple-600 hover:bg-purple-700 text-white font-semibold rounded-md transition-colors disabled:opacity-50"
                >
                  <i class="fas fa-gift mr-2"></i>
                  赠送好友
                </button>
              </div>

              <!-- Gift Options (shown when gift is selected) -->
              <div v-if="showGiftOptions" class="mt-4 p-4 bg-gray-800 rounded-md">
                <h3 class="text-lg font-semibold text-white mb-3">赠送选项</h3>
                <div class="space-y-3">
                  <div>
                    <label class="block text-sm text-gray-300 mb-1">好友Steam ID:</label>
                    <input
                      v-model="giftRecipient"
                      type="text"
                      placeholder="输入好友的Steam ID (17位数字，以7656开头)"
                      class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-gray-200 focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  </div>
                  <div>
                    <label class="block text-sm text-gray-300 mb-1">赠送留言:</label>
                    <textarea
                      v-model="giftMessage"
                      placeholder="写一些祝福的话，将会全图广播..."
                      rows="3"
                      class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-gray-200 focus:outline-none focus:ring-2 focus:ring-purple-500"
                    ></textarea>
                  </div>
                  <div class="flex gap-2">
                    <button
                      @click="confirmGift"
                      class="flex-1 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-md transition-colors"
                    >
                      确认赠送
                    </button>
                    <button
                      @click="cancelGift"
                      class="flex-1 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
                    >
                      取消
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCartStore } from '../stores/cartStore.js'
import { authApi } from '@/api/services/authApi.js'
import { usersApi } from '@/api/services/usersApi.js'
import { vipApi } from '@/api/services/vipApi.js'
import GameHeader from '../components/GameHeader.vue'

const router = useRouter()
const cartStore = useCartStore()

// 用户信息
const userInfo = ref({
  user_id: null,
  steam_id: null,
  username: '',
  email: '',
  user_type: 'user',
  is_admin: false,
  is_super_admin: false,
})

// 用户统计信息
const userStats = ref({
  signin_stats: {},
  pass_stats: {},
  vip_stats: null,
  character_stats: {},
  vip_level: null,
})

// 用户资产信息
const userAssets = ref({
  currency: {
    normal: 0,
    gold: 0,
  },
  fame_points: 0,
  items: [],
})

// 购物车状态
const showGiftOptions = ref(false)
const giftRecipient = ref('')
const giftMessage = ref('')

// 计算属性（使用cartStore）
const cartItems = computed(() => cartStore.items)
const totalItems = computed(() => cartStore.itemCount)
const totalPrice = computed(() => cartStore.totalPrice)

// 购物车操作
const increaseQuantity = (item) => {
  cartStore.increaseQuantity(item.id)
}

const decreaseQuantity = (item) => {
  cartStore.decreaseQuantity(item.id)
}

const removeFromCart = (item) => {
  cartStore.removeItem(item.id)
}

// 获取增加按钮的提示文本
const getIncreaseButtonTitle = (item) => {
  if (item.stock === -1) {
    return '增加数量（无限库存）'
  } else if (item.quantity >= item.stock) {
    return `已达库存上限（${item.stock}）`
  } else {
    return `增加数量（库存：${item.stock}）`
  }
}

// 验证并更新数量
const validateAndUpdateQuantity = (item) => {
  let newQuantity = parseInt(item.quantity)

  // 验证数量有效性
  if (isNaN(newQuantity) || newQuantity < 1) {
    newQuantity = 1
  }

  // 检查库存限制
  if (item.stock !== -1 && newQuantity > item.stock) {
    newQuantity = item.stock
    alert(`数量不能超过库存限制（${item.stock}）`)
  }

  // 更新数量
  cartStore.updateQuantity(item.id, newQuantity)
}

// 确认移除商品
const confirmRemoveItem = (item) => {
  if (confirm(`确定要从购物车中移除"${item.name}"吗？`)) {
    removeFromCart(item)
  }
}

// 检查购物车中是否有无效价格的商品
const hasInvalidPriceItems = computed(() => {
  return cartItems.value.some((item) => !item.isPriceValid || item.price == null || item.price <= 0)
})

const clearCart = () => {
  if (confirm('确定要清空购物车吗？')) {
    cartStore.clearCart()
  }
}

// 导航
const goToStore = () => {
  router.push('/store')
}

// 购买和赠送
const handlePurchase = async () => {
  try {
    // 在购买前保存总价，因为购买成功后购物车会被清空
    const purchaseTotal = totalPrice.value
    const result = await cartStore.purchase()
    if (result.success) {
      alert(`购买成功！总计：¥${purchaseTotal.toFixed(2)}`)
    } else {
      alert(result.message)
    }
  } catch (error) {
    alert('购买失败，请重试')
  }
}

const handleGift = () => {
  showGiftOptions.value = true
}

const confirmGift = async () => {
  if (!giftRecipient.value.trim()) {
    alert('请输入好友的Steam ID')
    return
  }

  try {
    const result = await cartStore.gift(giftRecipient.value, giftMessage.value)
    if (result.success) {
      alert(`赠送成功！已发送给 ${giftRecipient.value}`)
      showGiftOptions.value = false
      giftRecipient.value = ''
      giftMessage.value = ''
    } else {
      alert(result.message)
    }
  } catch (error) {
    alert('赠送失败，请重试')
  }
}

const cancelGift = () => {
  showGiftOptions.value = false
  giftRecipient.value = ''
  giftMessage.value = ''
}

const handleLogout = async () => {
  try {
    // 调用API注销
    await authApi.logout()

    // 清除本地存储的用户信息
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('rememberedUser')

    // 清除购物车数据
    cartStore.clearCart()

    // 跳转到登录页面
    router.push('/login')
  } catch (error) {
    console.error('注销失败:', error)
    // 即使API调用失败，也要清除本地数据并跳转
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('rememberedUser')
    cartStore.clearCart()
    router.push('/login')
  }
}

// 加载用户数据
const loadUserData = async () => {
  try {
    // 获取当前用户基本信息
    console.log('[CartView] 开始获取用户信息...')
    const currentUserResponse = await usersApi.getCurrentUser()
    console.log('[CartView] 用户信息API响应:', currentUserResponse)

    if (currentUserResponse.success && currentUserResponse.data) {
      console.log('[CartView] 设置用户信息:', currentUserResponse.data)
      // 映射API响应数据到组件数据结构
      // 注意：currentUserResponse.data 是整个API响应，真正的用户数据在 data.data 中
      const apiData = currentUserResponse.data.data || currentUserResponse.data
      console.log('[CartView] 提取的用户数据:', apiData)
      userInfo.value = {
        user_id: apiData.id || apiData.user_id,
        steam_id: apiData.steam_id,
        username: apiData.username,
        email: apiData.email,
        user_type: apiData.user_type || 'user',
        is_admin: apiData.is_admin || false,
        is_super_admin: apiData.is_super_admin || false,
      }

      // 初始化用户统计数据（基本用户API不包含VIP信息）
      userStats.value = {
        ...userStats.value,
        vip_level: null,
        pass_stats: {
          level: apiData.pass_level || 0,
          exp: apiData.pass_exp || 0,
        },
        vip_stats: null,
      }

      console.log('[CartView] 映射后的用户信息:', userInfo.value)
      console.log('[CartView] 映射后的用户统计:', userStats.value)
    } else {
      console.log('[CartView] API未返回数据，尝试从localStorage获取')
      // 如果API没有返回数据，尝试从localStorage获取
      const storedUserInfo = authApi.getCurrentUserFromStorage()
      if (storedUserInfo) {
        console.log('[CartView] 从localStorage获取用户信息:', storedUserInfo)
        userInfo.value = storedUserInfo
      } else {
        console.log('[CartView] localStorage中也没有用户信息')
      }
    }

    // 额外获取详细的VIP状态信息
    try {
      const vipResponse = await vipApi.getUserVipStatus()
      if (vipResponse.success && vipResponse.data) {
        console.log('[CartView] VIP状态数据:', vipResponse.data)
        // 更新VIP相关数据
        userStats.value.vip_level = vipResponse.data.vip_level || null
        userStats.value.vip_stats = {
          level: vipResponse.data.vip_level || 0,
          name: vipResponse.data.vip_name,
          expire_date: vipResponse.data.vip_expire_date,
          is_permanent: vipResponse.data.is_permanent,
          is_expired: vipResponse.data.is_expired,
        }
        console.log('[CartView] 更新后的VIP数据:', userStats.value)
      }
    } catch (vipError) {
      console.warn('[CartView] 获取VIP状态失败:', vipError)
      // VIP API失败不影响基本功能，继续执行
    }

    // 获取用户统计信息
    try {
      console.log('[CartView] 开始获取用户统计信息...')
      const statsResponse = await usersApi.getUserStats()
      console.log('[CartView] 用户统计API响应:', statsResponse)

      if (statsResponse.success) {
        // 映射API响应数据到组件数据结构
        const apiData = statsResponse.data.data || statsResponse.data
        console.log('[CartView] 提取的用户统计数据:', apiData)
        // 保留VIP数据，只更新其他统计信息
        userStats.value = {
          ...userStats.value, // 保留现有数据（包括VIP数据）
          ...apiData, // 更新统计数据
          // 确保VIP数据不被覆盖
          vip_level: userStats.value.vip_level,
          vip_stats: userStats.value.vip_stats,
        }
        console.log('[CartView] 映射后的用户统计:', userStats.value)
      }
    } catch (error) {
      console.warn('获取用户统计信息失败:', error)
    }

    // 获取用户资产信息
    try {
      console.log('[CartView] 开始获取用户资产信息...')
      const assetsResponse = await usersApi.getUserAssets()
      console.log('[CartView] 用户资产API响应:', assetsResponse)

      if (assetsResponse.success && assetsResponse.data) {
        // 映射API响应数据到组件数据结构
        // 注意：assetsResponse.data 可能是整个API响应，真正的资产数据在 data.data 中
        const apiData = assetsResponse.data.data || assetsResponse.data
        console.log('[CartView] 提取的用户资产数据:', apiData)
        userAssets.value = {
          currency: {
            normal: apiData.game_coins || 0,
            gold: apiData.shop_coins || 0,
          },
          fame_points: apiData.points || 0,
          items: [],
        }
        console.log('[CartView] 映射后的用户资产:', userAssets.value)
      }
    } catch (error) {
      console.warn('获取用户资产信息失败:', error)
    }
  } catch (error) {
    console.error('[CartView] 加载用户数据失败:', error)
    console.error('[CartView] 错误详情:', {
      message: error.message,
      status: error.status,
      response: error.response,
    })

    // 如果获取用户信息失败，可能是token过期，跳转到登录页
    if (error.status === 401) {
      console.log('[CartView] Token过期，跳转到登录页')
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      router.push('/login')
    } else {
      // 如果不是认证问题，尝试从localStorage获取用户信息
      console.log('[CartView] 尝试从localStorage获取用户信息作为降级方案')
      const storedUserInfo = authApi.getCurrentUserFromStorage()
      if (storedUserInfo) {
        console.log('[CartView] 从localStorage获取到用户信息:', storedUserInfo)
        userInfo.value = {
          user_id: storedUserInfo.id || storedUserInfo.user_id,
          steam_id: storedUserInfo.steam_id,
          username: storedUserInfo.username,
          email: storedUserInfo.email,
          user_type: storedUserInfo.user_type || 'user',
          is_admin: storedUserInfo.is_admin || false,
          is_super_admin: storedUserInfo.is_super_admin || false,
        }
      }
    }
  }
}

// 初始化购物车数据和用户数据
onMounted(async () => {
  console.log('[CartView] 组件挂载开始')

  // 检查登录状态
  if (!authApi.isLoggedIn()) {
    console.log('[CartView] 用户未登录，跳转到登录页')
    router.push('/login')
    return
  }

  console.log('[CartView] 用户已登录，开始加载数据')

  // 加载用户数据
  await loadUserData()

  console.log('[CartView] 用户数据加载完成，当前状态:')
  console.log('[CartView] userInfo:', userInfo.value)
  console.log('[CartView] userStats:', userStats.value)
  console.log('[CartView] userAssets:', userAssets.value)

  // 从localStorage加载购物车数据
  cartStore.loadFromStorage()
  cartStore.startAutoSave()

  console.log('[CartView] 组件挂载完成')
})
</script>
