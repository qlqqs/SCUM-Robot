<template>
  <div
    data-recharge-view
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
      <div class="w-3/5 mx-auto bg-gray-800/60 backdrop-blur-md rounded-lg p-4 lg:p-6">
        <!-- Page Header -->
        <div class="text-center mb-8">
          <h1 class="text-3xl lg:text-4xl font-bold text-white mb-2">
            <i class="fas fa-donate text-pink-400 mr-3"></i>
            赞助
          </h1>
          <p class="text-gray-300 text-lg">支持服务器运营</p>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="flex justify-center items-center py-12">
          <div class="text-center">
            <i class="fas fa-spinner fa-spin text-4xl text-pink-500 mb-4"></i>
            <p class="text-gray-300">正在加载充值数据...</p>
          </div>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="text-center py-12">
          <div class="bg-red-900/50 border border-red-700 rounded-lg p-6 max-w-md mx-auto">
            <i class="fas fa-exclamation-triangle text-4xl text-red-400 mb-4"></i>
            <h3 class="text-xl font-semibold text-red-300 mb-2">加载失败</h3>
            <p class="text-red-200 mb-4">{{ error }}</p>
            <button
              @click="initializeData"
              class="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded transition-colors"
            >
              重试
            </button>
          </div>
        </div>

        <!-- Main Content -->
        <template v-else>
          <!-- Current Balance -->
          <div
            class="bg-gradient-to-r from-blue-900/50 to-purple-900/50 rounded-lg p-6 mb-8 border border-blue-500/30"
          >
            <div class="text-center">
              <h3 class="text-lg font-semibold text-white mb-2">当前余额</h3>
              <div class="flex justify-center items-center gap-8">
                <div class="text-center">
                  <div class="text-2xl font-bold text-yellow-400">
                    {{ formatNumber(userAssets.currency?.normal || 0) }}
                  </div>
                  <div class="text-sm text-gray-300">{{ gameCurrencyName }}</div>
                </div>
                <div class="text-center">
                  <div class="text-2xl font-bold text-purple-400">
                    {{ formatNumber(userAssets.currency?.gold || 0) }}
                  </div>
                  <div class="text-sm text-gray-300">{{ shopCurrencyName }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Recharge Packages -->
          <div class="mb-8">
            <h3 class="text-xl font-semibold text-white mb-4 flex items-center">
              <i class="fas fa-credit-card text-green-400 mr-2"></i>
              充值套餐
            </h3>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div
                v-for="package_ in rechargePackages"
                :key="package_.id"
                class="bg-gray-900/50 border border-gray-700 rounded-lg p-6 hover:border-pink-500/50 hover:shadow-lg hover:shadow-pink-500/20 transition-all duration-300"
              >
                <!-- Package Header -->
                <div class="text-center mb-4">
                  <div
                    class="w-16 h-16 mx-auto mb-3 rounded-lg bg-gradient-to-br from-pink-400 to-purple-500 flex items-center justify-center"
                  >
                    <i class="fas fa-gem text-white text-2xl"></i>
                  </div>
                  <h4 class="text-lg font-bold text-white">{{ package_.name }}</h4>
                  <p class="text-sm text-gray-400">{{ package_.description }}</p>
                </div>

                <!-- Package Details -->
                <div class="space-y-2 mb-4">
                  <div class="flex justify-between items-center">
                    <span class="text-gray-300">充值金额</span>
                    <span class="text-xl font-bold text-green-400">¥{{ package_.price }}</span>
                  </div>
                  <div class="flex justify-between items-center">
                    <span class="text-gray-300">获得{{ shopCurrencyName }}</span>
                    <span class="text-lg font-semibold text-purple-400">{{
                      formatNumber(package_.coins)
                    }}</span>
                  </div>
                  <!-- 额外赠送行，没有赠送时保持占位 -->
                  <div class="flex justify-between items-center">
                    <span class="text-gray-300" :class="{ 'opacity-0': package_.bonus <= 0 }">
                      额外赠送
                    </span>
                    <span
                      class="text-lg font-semibold text-yellow-400"
                      :class="{ 'opacity-0': package_.bonus <= 0 }"
                    >
                      +{{ formatNumber(package_.bonus || 0) }}
                    </span>
                  </div>
                </div>

                <!-- Purchase Button -->
                <button
                  @click="purchasePackage(package_)"
                  :disabled="purchasing === package_.id"
                  class="w-full px-4 py-3 rounded-lg font-medium transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed bg-gradient-to-r from-pink-500 to-purple-600 hover:from-pink-600 hover:to-purple-700 text-white"
                >
                  <i v-if="purchasing === package_.id" class="fas fa-spinner fa-spin mr-2"></i>
                  <i v-else class="fas fa-shopping-cart mr-2"></i>
                  {{ purchasing === package_.id ? '处理中...' : '立即充值' }}
                </button>
              </div>
            </div>
          </div>

          <!-- Payment Methods -->
          <div class="mb-8">
            <h3 class="text-xl font-semibold text-white mb-4 flex items-center">
              <i class="fas fa-wallet text-blue-400 mr-2"></i>
              支付方式
            </h3>

            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div
                v-for="method in paymentMethods"
                :key="method.id"
                class="bg-gray-900/50 border border-gray-700 rounded-lg p-4 text-center hover:border-blue-500/50 transition-colors"
              >
                <div
                  class="w-12 h-12 mx-auto mb-2 rounded-lg bg-gray-700 flex items-center justify-center"
                >
                  <i :class="method.icon" class="text-xl text-white"></i>
                </div>
                <div class="text-sm text-gray-300">{{ method.name }}</div>
              </div>
            </div>
          </div>

          <!-- Recharge History -->
          <div>
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-xl font-semibold text-white flex items-center">
                <i class="fas fa-history text-gray-400 mr-2"></i>
                充值记录
              </h3>
              <button
                @click="loadRechargeHistory"
                :disabled="loadingHistory"
                class="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors disabled:opacity-50"
              >
                <i class="fas fa-sync-alt mr-1" :class="{ 'animate-spin': loadingHistory }"></i>
                刷新
              </button>
            </div>

            <div class="bg-gray-900/50 rounded-lg border border-gray-700">
              <div v-if="rechargeHistory.length === 0" class="text-center py-8 text-gray-400">
                <i class="fas fa-file-alt text-3xl mb-2"></i>
                <p>暂无充值记录</p>
              </div>
              <!-- 滚动容器，最多显示3条记录的高度 -->
              <div v-else class="max-h-[360px] overflow-y-auto">
                <div class="divide-y divide-gray-700">
                  <div
                    v-for="record in rechargeHistory"
                    :key="record.id"
                    class="p-4 hover:bg-gray-800/50 transition-colors"
                  >
                    <div class="flex items-center justify-between">
                      <div class="flex-1">
                        <div class="flex items-center gap-2">
                          <div class="text-white font-medium">{{ record.package_name }}</div>
                          <span
                            class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
                            :class="getStatusBadgeClass(record.status)"
                          >
                            {{ getStatusText(record.status) }}
                          </span>
                        </div>
                        <div class="text-sm text-gray-400 mt-1">订单号: {{ record.order_id }}</div>
                        <div class="text-sm text-gray-400">
                          {{ formatDate(record.created_at) }}
                        </div>
                      </div>
                      <div class="text-right">
                        <div class="text-green-400 font-semibold">¥{{ record.amount }}</div>
                        <div
                          v-if="record.coins_added"
                          class="text-sm text-yellow-400 flex items-center justify-end gap-1"
                        >
                          <i class="fas fa-coins"></i>
                          <span>+{{ record.coins_added }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </main>

    <!-- Payment QR Code Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="showPaymentModal"
          class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
        >
          <div class="bg-gray-800 rounded-lg shadow-2xl border border-gray-600 p-6 max-w-md w-full">
            <!-- Modal Header -->
            <div class="flex items-center justify-between mb-4 border-b border-gray-600 pb-4">
              <h3 class="text-xl font-semibold text-white flex items-center">
                <i class="fab fa-alipay text-blue-400 mr-2"></i>
                请使用支付宝扫码支付
              </h3>
            </div>

            <!-- QR Code -->
            <div class="flex justify-center mb-4">
              <div class="bg-white p-4 rounded-lg">
                <canvas ref="qrCodeCanvas"></canvas>
              </div>
            </div>

            <!-- Order Info -->
            <div class="space-y-2 mb-4 bg-gray-900/50 rounded-lg p-4">
              <div class="flex justify-between text-sm">
                <span class="text-gray-400">订单号:</span>
                <span class="text-white font-mono">{{ currentOrder?.order_id }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-400">金额:</span>
                <span class="text-green-400 font-semibold">¥{{ currentOrder?.amount }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-400">获得:</span>
                <span class="text-purple-400 font-semibold"
                  >{{ currentOrder?.coins }} {{ shopCurrencyName }}</span
                >
              </div>
            </div>

            <!-- Countdown -->
            <div class="text-center mb-4">
              <div class="text-sm text-gray-400 mb-1">剩余时间</div>
              <div class="text-2xl font-bold text-yellow-400">{{ countdown }}</div>
            </div>

            <!-- Status -->
            <div class="text-center mb-4">
              <div class="inline-flex items-center gap-2 text-blue-400">
                <i class="fas fa-spinner fa-spin"></i>
                <span>等待支付中...</span>
              </div>
            </div>

            <!-- Cancel Button -->
            <div class="flex justify-center">
              <button
                @click="cancelPayment"
                :disabled="cancellingPayment"
                class="px-6 py-2 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors duration-200 flex items-center gap-2"
              >
                <i class="fas" :class="cancellingPayment ? 'fa-spinner fa-spin' : 'fa-times'"></i>
                <span>{{ cancellingPayment ? '取消中...' : '取消支付' }}</span>
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Payment Success Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="showSuccessModal"
          class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
          @click="showSuccessModal = false"
        >
          <div
            class="bg-gray-800 rounded-lg shadow-2xl border border-green-600 p-6 max-w-md w-full"
            @click.stop
          >
            <div class="text-center">
              <div
                class="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-4"
              >
                <i class="fas fa-check text-white text-3xl"></i>
              </div>
              <h3 class="text-2xl font-bold text-white mb-2">支付成功！</h3>
              <p class="text-gray-300 mb-4">{{ successMessage }}</p>
              <button
                @click="showSuccessModal = false"
                class="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
              >
                确定
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '@/api/services/authApi.js'
import { usersApi } from '@/api/services/usersApi.js'
import { paymentApi } from '@/api/services/paymentApi.js'
import { rechargePackageApi } from '@/api/services/rechargePackageApi.js'
import { vipApi } from '@/api/services/vipApi.js'
import { useSystemConfigStore } from '@/stores/systemConfigStore.js'
import GameHeader from '../components/GameHeader.vue'
import QRCode from 'qrcode'

const router = useRouter()
const systemConfigStore = useSystemConfigStore()

// 响应式状态
const loading = ref(false)
const purchasing = ref(null)
const loadingHistory = ref(false)
const loadingMethods = ref(false)
const rechargeHistory = ref([])
const error = ref('')

// 支付相关状态
const showPaymentModal = ref(false)
const showSuccessModal = ref(false)
const currentOrder = ref(null)
const countdown = ref('15:00')
const successMessage = ref('')
const qrCodeCanvas = ref(null)
const cancellingPayment = ref(false)

// 定时器
let pollTimer = null
let countdownTimer = null

// 用户信息
const userInfo = ref({})
const userStats = ref({
  signin_stats: {},
  pass_stats: {},
  vip_stats: null,
  character_stats: {},
  vip_level: null,
})
const userAssets = ref({
  currency: {
    normal: 0,
    gold: 0,
  },
  fame_points: 0,
})

// 系统配置
const gameCurrencyName = computed(() => systemConfigStore.gameCurrencyName)
const shopCurrencyName = computed(() => systemConfigStore.shopCurrencyName)

// 充值套餐数据 - 从后端API获取
const rechargePackages = ref([])

// 支付方式数据 - 从后端API获取
const paymentMethods = ref([])

// 加载支付方式
const loadPaymentMethods = async () => {
  loadingMethods.value = true
  try {
    const response = await paymentApi.getMethods('production')
    if (response.success && response.data) {
      paymentMethods.value = response.data.map((method) => ({
        id: method.id,
        name: method.provider_name,
        icon: getPaymentIcon(method.provider_code),
        provider_code: method.provider_code,
      }))
    }
  } catch (error) {
    console.error('[RechargeView] Failed to load payment methods:', error)
    error.value = '加载支付方式失败'
  } finally {
    loadingMethods.value = false
  }
}

// 获取支付方式图标
const getPaymentIcon = (providerCode) => {
  const iconMap = {
    alipay: 'fab fa-alipay',
    wechat: 'fab fa-weixin',
    epay: 'fas fa-credit-card',
    qq: 'fab fa-qq',
  }
  return iconMap[providerCode] || 'fas fa-credit-card'
}

// 加载充值套餐配置
const loadRechargePackages = async () => {
  try {
    // 从后端API获取充值套餐配置（只获取启用的套餐）
    const response = await rechargePackageApi.getPackages({ active_only: true })

    if (response.success && response.data) {
      // 按排序顺序排列，并转换字段名以兼容现有代码
      rechargePackages.value = response.data
        .sort((a, b) => a.sort_order - b.sort_order)
        .map((pkg) => ({
          id: pkg.id,
          name: pkg.name,
          description: pkg.description || pkg.tag || '',
          price: pkg.price,
          coins: pkg.coins,
          bonus: pkg.bonus_coins || 0,
          total_coins: pkg.total_coins,
          badge: pkg.badge,
          is_hot: pkg.is_hot,
        }))

      console.log('[RechargeView] Loaded recharge packages:', rechargePackages.value.length)
    } else {
      throw new Error(response.message || '获取充值套餐失败')
    }
  } catch (error) {
    console.error('[RechargeView] Failed to load recharge packages:', error)
    error.value = '加载充值套餐失败'
  }
}

// 加载用户信息
const loadUserInfo = async () => {
  try {
    console.log('[RechargeView] Loading user info and assets...')

    const [userResponse, assetsResponse] = await Promise.all([
      authApi.getCurrentUser(),
      usersApi.getUserAssets(),
    ])

    console.log('[RechargeView] User response:', userResponse)
    console.log('[RechargeView] Assets response:', assetsResponse)

    if (userResponse.success && userResponse.data) {
      const userData = userResponse.data.data || userResponse.data
      userInfo.value = userData
      userStats.value = {
        ...userData,
        vip_level: userData.vip_level ?? null, // 保留用户的VIP等级
        pass_stats: {
          level: userData.pass_level || 0,
          exp: userData.pass_exp || 0,
        },
        vip_stats: userData.vip_stats ?? null, // 保留用户的VIP统计
      }
      console.log('[RechargeView] User info loaded:', userInfo.value)
      console.log('[RechargeView] VIP level:', userStats.value.vip_level)
      console.log('[RechargeView] VIP stats:', userStats.value.vip_stats)
    }

    if (assetsResponse.success && assetsResponse.data) {
      // API返回的数据结构是嵌套的：{ success, message, data: { 实际数据 } }
      // 需要从 assetsResponse.data.data 中获取实际的资产数据
      const assetsData = assetsResponse.data.data || assetsResponse.data
      console.log('[RechargeView] Assets data:', assetsData)
      console.log('[RechargeView] game_coins:', assetsData.game_coins)
      console.log('[RechargeView] shop_coins:', assetsData.shop_coins)

      userAssets.value = {
        currency: {
          normal: assetsData.game_coins || 0,
          gold: assetsData.shop_coins || 0,
        },
        fame_points: assetsData.points || 0,
      }
      console.log('[RechargeView] User assets updated:', userAssets.value)
    } else {
      console.error('[RechargeView] Assets response failed:', assetsResponse)
    }

    // 额外获取VIP状态信息（与其他页面保持一致）
    try {
      const vipResponse = await vipApi.getUserVipStatus()
      if (vipResponse.success && vipResponse.data) {
        console.log('[RechargeView] VIP response:', vipResponse.data)
        // 更新VIP相关数据
        userStats.value.vip_level = vipResponse.data.vip_level ?? null
        userStats.value.vip_stats = {
          level: vipResponse.data.vip_level || 0,
          name: vipResponse.data.vip_name,
          expire_date: vipResponse.data.vip_expire_date,
          is_permanent: vipResponse.data.is_permanent,
          is_expired: vipResponse.data.is_expired,
        }
        console.log(
          '[RechargeView] VIP data updated:',
          userStats.value.vip_level,
          userStats.value.vip_stats,
        )
      }
    } catch (vipError) {
      console.warn('[RechargeView] 获取VIP状态失败:', vipError)
      // VIP API失败不影响基本功能，继续执行
    }
  } catch (error) {
    console.error('[RechargeView] Failed to load user info:', error)
    error.value = '加载用户信息失败'
  }
}

// 购买套餐
const purchasePackage = async (package_) => {
  if (paymentMethods.value.length === 0) {
    alert('暂无可用支付方式，请稍后重试')
    return
  }

  purchasing.value = package_.id

  try {
    // 使用第一个可用的支付方式
    const defaultPaymentMethod = paymentMethods.value[0]

    const orderData = {
      amount: package_.price,
      package_id: package_.id, // 传递套餐ID，后端会自动使用套餐的product_name
      payment_method_id: defaultPaymentMethod.id,
    }

    console.log('[RechargeView] Creating order:', orderData)
    const response = await paymentApi.createOrder(orderData)

    if (response.success && response.data) {
      const orderInfo = response.data
      console.log('[RechargeView] Order created:', orderInfo)

      // 检查是否有二维码数据
      const qrCodeUrl = orderInfo.payment_data?.qr_code || orderInfo.qr_code

      if (qrCodeUrl) {
        // 显示二维码支付模态框
        // 注意：后端返回的字段名是 expired_at，不是 expires_at
        // 如果后端没有返回过期时间，则使用当前时间 + 15分钟
        const expiresAt =
          orderInfo.expires_at ||
          orderInfo.expired_at ||
          new Date(Date.now() + 15 * 60 * 1000).toISOString()

        currentOrder.value = {
          order_id: orderInfo.order_id,
          amount: orderInfo.amount,
          coins: package_.coins + package_.bonus,
          qr_code: qrCodeUrl,
          expires_at: expiresAt,
        }

        console.log('[RechargeView] Current order set:', currentOrder.value)
        await displayPaymentQRCode()
        startPollingOrderStatus(orderInfo.order_id)
      } else if (orderInfo.payment_url) {
        // 如果有支付URL，跳转到支付页面
        window.open(orderInfo.payment_url, '_blank')
        await loadRechargeHistory()
      } else {
        alert(`订单创建成功\n订单号：${orderInfo.order_id}\n请按照提示完成支付`)
        await loadRechargeHistory()
      }
    } else {
      throw new Error(response.message || '创建订单失败')
    }
  } catch (error) {
    console.error('[RechargeView] Purchase failed:', error)
    const errorMessage = error.response?.data?.message || error.message || '充值失败，请稍后重试'
    alert(errorMessage)
  } finally {
    purchasing.value = null
  }
}

// 显示支付二维码
const displayPaymentQRCode = async () => {
  console.log('[RechargeView] Displaying payment QR code, current order:', currentOrder.value)
  showPaymentModal.value = true

  // 等待DOM更新
  await nextTick()

  // 生成二维码
  if (qrCodeCanvas.value && currentOrder.value?.qr_code) {
    try {
      await QRCode.toCanvas(qrCodeCanvas.value, currentOrder.value.qr_code, {
        width: 256,
        margin: 1,
        color: {
          dark: '#000000',
          light: '#FFFFFF',
        },
      })
      console.log('[RechargeView] QR code generated successfully')
    } catch (err) {
      console.error('[RechargeView] Failed to generate QR code:', err)
    }
  }

  // 开始倒计时
  if (currentOrder.value?.expires_at) {
    console.log('[RechargeView] Starting countdown with expires_at:', currentOrder.value.expires_at)
    startCountdown(currentOrder.value.expires_at)
  } else {
    console.warn('[RechargeView] No expires_at found in current order')
  }
}

// 开始倒计时
const startCountdown = (expiresAt) => {
  console.log('[RechargeView] Starting countdown, expires_at:', expiresAt)

  // 清除之前的定时器
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }

  const expiresTime = new Date(expiresAt).getTime()
  console.log('[RechargeView] Expires time:', expiresTime, 'Current time:', new Date().getTime())

  const updateCountdown = () => {
    const now = new Date().getTime()
    const distance = expiresTime - now

    if (distance < 0) {
      countdown.value = '已过期'
      clearInterval(countdownTimer)
      countdownTimer = null
      closePaymentModal()
      alert('订单已过期，请重新下单')
      return
    }

    const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60))
    const seconds = Math.floor((distance % (1000 * 60)) / 1000)

    countdown.value = `${minutes}:${seconds.toString().padStart(2, '0')}`
  }

  updateCountdown()
  countdownTimer = setInterval(updateCountdown, 1000)
  console.log('[RechargeView] Countdown timer started, timer ID:', countdownTimer)
}

// 开始轮询订单状态
const startPollingOrderStatus = (orderId) => {
  const pollInterval = 2000 // 2秒轮询一次
  const maxAttempts = 450 // 最多轮询15分钟
  let attempts = 0

  const poll = async () => {
    attempts++

    if (attempts > maxAttempts) {
      clearInterval(pollTimer)
      showPaymentTimeout()
      return
    }

    try {
      const response = await paymentApi.getOrderStatus(orderId)

      if (response.success && response.data) {
        const status = response.data.status

        if (status === 'paid' || status === 'success' || status === 'completed') {
          // 支付成功
          clearInterval(pollTimer)
          showPaymentSuccess(response.data)
        } else if (status === 'failed' || status === 'cancelled') {
          // 支付失败或取消
          clearInterval(pollTimer)
          showPaymentFailed()
        }
        // status === 'pending' 继续轮询
      }
    } catch (err) {
      console.error('[RechargeView] Failed to poll order status:', err)
    }
  }

  poll() // 立即执行一次
  pollTimer = setInterval(poll, pollInterval)
}

// 显示支付成功
const showPaymentSuccess = async (orderData) => {
  closePaymentModal()

  // 后端返回的字段名是 coins_added，不是 coins
  const coinsAdded = orderData.coins_added ?? currentOrder.value?.coins ?? 0
  successMessage.value = `充值成功！您已获得 ${coinsAdded} ${shopCurrencyName.value}`
  showSuccessModal.value = true

  // 刷新用户余额和充值记录
  await Promise.all([loadUserInfo(), loadRechargeHistory()])
}

// 显示支付失败
const showPaymentFailed = () => {
  closePaymentModal()
  alert('支付失败，请重试')
}

// 显示支付超时
const showPaymentTimeout = () => {
  closePaymentModal()
  alert('支付超时，订单已取消')
}

// 取消支付
const cancelPayment = async () => {
  if (!currentOrder.value?.order_id) {
    closePaymentModal()
    return
  }

  cancellingPayment.value = true

  try {
    console.log('[RechargeView] Cancelling order:', currentOrder.value.order_id)

    const response = await paymentApi.cancelOrder(currentOrder.value.order_id)

    if (response.success) {
      console.log('[RechargeView] Order cancelled successfully')
      closePaymentModal()
      alert('订单已取消')
      // 刷新充值记录
      await loadRechargeHistory()
    } else {
      console.error('[RechargeView] Failed to cancel order:', response.message)
      alert(response.message || '取消订单失败')
    }
  } catch (error) {
    console.error('[RechargeView] Cancel order error:', error)
    const errorMessage = error.response?.data?.error || error.message || '取消订单失败，请稍后重试'
    alert(errorMessage)
  } finally {
    cancellingPayment.value = false
  }
}

// 关闭支付模态框
const closePaymentModal = () => {
  showPaymentModal.value = false
  currentOrder.value = null
  countdown.value = '15:00'
  cancellingPayment.value = false

  // 清理定时器
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
}

// 加载充值记录
const loadRechargeHistory = async () => {
  loadingHistory.value = true

  try {
    console.log('[RechargeView] Loading recharge history...')

    // 使用订单列表API获取当前用户的充值记录
    const response = await paymentApi.getOrders({
      page: 1,
      page_size: 10, // 只显示最近10条记录
    })

    if (response.success && response.data) {
      rechargeHistory.value = response.data.orders.map((record) => ({
        id: record.id,
        package_name: record.description || '充值订单',
        amount: record.amount,
        status: record.status,
        created_at: record.created_at,
        order_id: record.order_id,
        coins_added: record.coins_added,
      }))
      console.log('[RechargeView] Recharge history loaded:', rechargeHistory.value.length)
    } else {
      rechargeHistory.value = []
      console.log('[RechargeView] No recharge history found')
    }
  } catch (error) {
    console.error('[RechargeView] Failed to load recharge history:', error)
    rechargeHistory.value = []
  } finally {
    loadingHistory.value = false
  }
}

// 工具函数
const formatNumber = (number) => {
  if (!number && number !== 0) return '0'
  return number.toLocaleString()
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

// 获取订单状态徽章样式
const getStatusBadgeClass = (status) => {
  switch (status) {
    case 'success':
      return 'bg-green-500/20 text-green-400 border border-green-500/30'
    case 'pending':
      return 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
    case 'processing':
      return 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
    case 'failed':
      return 'bg-red-500/20 text-red-400 border border-red-500/30'
    case 'cancelled':
      return 'bg-gray-500/20 text-gray-400 border border-gray-500/30'
    case 'refunded':
      return 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
    case 'expired':
      return 'bg-orange-500/20 text-orange-400 border border-orange-500/30'
    default:
      return 'bg-gray-500/20 text-gray-400 border border-gray-500/30'
  }
}

const getStatusText = (status) => {
  switch (status) {
    case 'success':
      return '支付成功'
    case 'pending':
      return '待支付'
    case 'processing':
      return '处理中'
    case 'failed':
      return '支付失败'
    case 'cancelled':
      return '已取消'
    case 'refunded':
      return '已退款'
    case 'expired':
      return '已过期'
    default:
      return '未知状态'
  }
}

// 登出处理
const handleLogout = () => {
  authApi.logout()
  router.push('/login')
}

// 初始化数据加载
const initializeData = async () => {
  loading.value = true
  error.value = ''

  try {
    // 并行加载基础数据
    await Promise.all([
      systemConfigStore.loadConfig(),
      loadUserInfo(),
      loadPaymentMethods(),
      loadRechargePackages(),
    ])

    // 加载充值记录
    await loadRechargeHistory()
  } catch (err) {
    console.error('[RechargeView] Failed to initialize data:', err)
    error.value = '初始化数据失败，请刷新页面重试'
  } finally {
    loading.value = false
  }
}

// 组件挂载时加载数据
onMounted(() => {
  initializeData()
})

// 组件卸载时清理定时器
onUnmounted(() => {
  if (pollTimer) {
    clearInterval(pollTimer)
  }
  if (countdownTimer) {
    clearInterval(countdownTimer)
  }
})
</script>

<style scoped>
/* 自定义样式 */
.bg-gray-850 {
  background-color: rgba(31, 41, 55, 0.85);
}

/* 渐变动画 */
@keyframes gradient {
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}

.animate-gradient {
  background-size: 200% 200%;
  animation: gradient 3s ease infinite;
}

/* 模态框过渡动画 */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active > div,
.modal-leave-active > div {
  transition: transform 0.3s ease;
}

.modal-enter-from > div,
.modal-leave-to > div {
  transform: scale(0.9);
}

/* 自定义滚动条样式 */
.max-h-\[360px\]::-webkit-scrollbar {
  width: 8px;
}

.max-h-\[360px\]::-webkit-scrollbar-track {
  background: rgba(31, 41, 55, 0.5);
  border-radius: 4px;
}

.max-h-\[360px\]::-webkit-scrollbar-thumb {
  background: rgba(75, 85, 99, 0.8);
  border-radius: 4px;
}

.max-h-\[360px\]::-webkit-scrollbar-thumb:hover {
  background: rgba(107, 114, 128, 0.9);
}
</style>
