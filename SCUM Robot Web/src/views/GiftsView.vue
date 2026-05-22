<template>
  <div
    data-gifts-view
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
            <i class="fas fa-gift text-yellow-400 mr-3"></i>
            礼包中心
          </h1>
          <p class="text-gray-300 text-lg">领取专属礼包，获得丰厚奖励</p>
        </div>

        <!-- Action Bar -->
        <div class="flex flex-col sm:flex-row justify-between items-center mb-6 gap-4">
          <div class="flex items-center gap-4">
            <button
              @click="loadGifts"
              :disabled="loading"
              class="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors disabled:opacity-50"
              title="刷新礼包"
            >
              <i class="fas fa-sync-alt mr-1" :class="{ 'animate-spin': loading }"></i>
              刷新
            </button>

            <!-- 排序按钮 -->
            <button
              v-if="userInfo?.is_admin"
              @click="toggleSortMode"
              :class="[
                'px-4 py-2 text-sm rounded-md transition-colors text-white font-medium',
                sortMode ? 'bg-blue-700 hover:bg-blue-800' : 'bg-blue-600 hover:bg-blue-700',
              ]"
              title="管理员排序功能"
            >
              <i :class="['mr-1', sortMode ? 'fas fa-check' : 'fas fa-sort']"></i>
              <span>{{ sortMode ? '完成' : '排序' }}</span>
            </button>

            <div class="text-sm text-gray-300">
              <i class="fas fa-box text-yellow-400 mr-1"></i>
              可领取礼包: {{ availableGifts.length }}
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button
              @click="showClaimedHistory = !showClaimedHistory"
              class="px-4 py-2 text-sm bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
            >
              <i class="fas fa-history mr-1"></i>
              {{ showClaimedHistory ? '隐藏历史' : '领取历史' }}
            </button>
          </div>
        </div>

        <!-- 排序模式提示 -->
        <div v-if="sortMode" class="mb-4 p-3 bg-blue-900/30 border border-blue-500/50 rounded-lg">
          <div class="flex items-center">
            <i class="fas fa-info-circle text-blue-400 mr-2"></i>
            <span class="text-blue-200">排序模式已启用，您可以拖拽礼包卡片来调整显示顺序</span>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="flex justify-center items-center py-12">
          <div class="text-center">
            <i class="fas fa-spinner fa-spin text-4xl text-blue-500 mb-4"></i>
            <p class="text-gray-300">正在加载礼包数据...</p>
          </div>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="text-center py-12">
          <div class="bg-red-900/50 border border-red-700 rounded-lg p-6 max-w-md mx-auto">
            <i class="fas fa-exclamation-triangle text-4xl text-red-400 mb-4"></i>
            <h3 class="text-xl font-semibold text-red-300 mb-2">加载失败</h3>
            <p class="text-red-200 mb-4">{{ error }}</p>
            <button
              @click="loadGifts"
              class="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded transition-colors"
            >
              重试
            </button>
          </div>
        </div>

        <!-- Content -->
        <template v-else>
          <!-- Claimed History -->
          <div v-if="showClaimedHistory" class="mb-8">
            <div class="bg-gray-900/50 rounded-lg p-4 border border-gray-700">
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-semibold text-white">
                  <i class="fas fa-history text-gray-400 mr-2"></i>
                  领取历史
                </h3>
                <div v-if="claimedHistory.length > 0" class="text-sm text-gray-400">
                  共 {{ claimedHistory.length }} 条记录
                </div>
              </div>

              <div v-if="claimedHistory.length === 0" class="text-center py-8 text-gray-400">
                <i class="fas fa-file-alt text-3xl mb-2"></i>
                <p>暂无领取记录</p>
              </div>
              <div v-else>
                <textarea
                  :value="formatClaimedHistoryLog()"
                  readonly
                  class="w-full h-40 p-3 text-sm font-mono bg-gray-800 border border-gray-600 rounded resize-none text-gray-300"
                  placeholder="领取记录将显示在这里..."
                ></textarea>
              </div>
            </div>
          </div>

          <!-- Empty State -->
          <div v-if="availableGifts.length === 0" class="text-center py-12">
            <div class="text-gray-400">
              <i class="fas fa-gift text-6xl mb-4"></i>
              <h3 class="text-xl font-semibold mb-2">暂无可领取礼包</h3>
              <p>请稍后再来查看是否有新的礼包</p>
            </div>
          </div>

          <!-- Gifts List -->
          <div v-else class="space-y-4">
            <div
              v-for="(gift, index) in sortedGifts"
              :key="gift.id"
              :class="[
                'border rounded-lg p-6 min-h-[220px] transition-all duration-300',
                canClaimGift(gift)
                  ? 'bg-gray-900/50 border-gray-700 hover:border-yellow-500/50 hover:shadow-lg hover:shadow-yellow-500/20'
                  : 'bg-gray-800/30 border-gray-600 opacity-60',
                {
                  'bg-gray-700/30 scale-98 opacity-80': sortMode && draggedItem === gift.id,
                  'bg-blue-900/20':
                    sortMode && dragOverIndex === index && draggedItemIndex !== index,
                  'bg-blue-900/10': sortMode,
                  'cursor-move': sortMode,
                },
              ]"
              :draggable="sortMode"
              @dragstart="handleDragStart(index, gift.id)"
              @dragover.prevent="handleDragOver(index)"
              @dragenter.prevent="handleDragEnter(index)"
              @dragleave="handleDragLeave"
              @drop="handleDrop(index)"
              @dragend="handleDragEnd"
            >
              <!-- Gift Banner Layout -->
              <div class="flex items-center gap-4">
                <!-- Gift Icon -->
                <div class="flex-shrink-0">
                  <div
                    :class="[
                      'w-16 h-16 rounded-lg flex items-center justify-center',
                      canClaimGift(gift)
                        ? 'bg-gradient-to-br from-yellow-400 to-orange-500'
                        : 'bg-gradient-to-br from-gray-500 to-gray-600',
                    ]"
                  >
                    <i class="fas fa-gift text-white text-2xl"></i>
                  </div>
                </div>

                <!-- Gift Info -->
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 mb-1">
                    <h3 class="text-lg font-bold text-white truncate">{{ gift.name }}</h3>
                    <!-- 不可用状态标签 -->
                    <span
                      v-if="!canClaimGift(gift)"
                      class="px-2 py-1 text-xs bg-red-900/50 text-red-400 border border-red-500/50 rounded-full flex-shrink-0"
                    >
                      不可领取
                    </span>
                  </div>
                  <p class="text-gray-400 text-sm mb-2 line-clamp-1">
                    {{ gift.description || '精美礼包等你领取' }}
                  </p>

                  <!-- Gift Details -->
                  <div class="flex items-center gap-4 text-xs text-gray-400">
                    <div v-if="gift.total_quantity" class="flex items-center gap-1">
                      <i class="fas fa-box text-yellow-400"></i>
                      <span>{{ gift.remaining_quantity || 0 }}/{{ gift.total_quantity }}</span>
                    </div>
                    <div v-if="gift.start_time && gift.end_time" class="flex items-center gap-1">
                      <i class="fas fa-clock text-blue-400"></i>
                      <span>{{ formatDateRange(gift.start_time, gift.end_time) }}</span>
                    </div>
                  </div>
                </div>

                <!-- Claim Button -->
                <div class="flex-shrink-0">
                  <button
                    @click="claimGift(gift)"
                    :disabled="gift.claiming || !canClaimGift(gift)"
                    class="px-6 py-2 rounded-lg font-medium transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                    :class="getClaimButtonClass(gift)"
                  >
                    <i v-if="gift.claiming" class="fas fa-spinner fa-spin mr-2"></i>
                    <i v-else-if="isPaidGift(gift.name)" class="fas fa-shopping-cart mr-2"></i>
                    <i v-else class="fas fa-hand-holding-heart mr-2"></i>
                    {{ getClaimButtonText(gift) }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { giftsApi } from '@/api/services/giftsApi.js'
import { authApi } from '@/api/services/authApi.js'
import { usersApi } from '@/api/services/usersApi.js'
import { vipApi } from '@/api/services/vipApi.js'
import GameHeader from '../components/GameHeader.vue'

const router = useRouter()

// 响应式状态
const loading = ref(false)
const error = ref('')
const availableGifts = ref([])
const claimedHistory = ref([])
const showClaimedHistory = ref(false)

// 排序相关数据
const sortMode = ref(false)
const draggedItemIndex = ref(null)
const draggedItem = ref(null)
const dragOverIndex = ref(null)

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

// 加载用户信息
const loadUserInfo = async () => {
  try {
    const [userResponse, assetsResponse] = await Promise.all([
      authApi.getCurrentUser(),
      usersApi.getUserAssets(),
    ])

    if (userResponse.success && userResponse.data) {
      const userData = userResponse.data.data || userResponse.data
      userInfo.value = userData
      // 初始化用户统计数据（基本用户API不包含VIP信息）
      userStats.value = {
        ...userData,
        vip_level: null,
        pass_stats: {
          level: userData.pass_level || 0,
          exp: userData.pass_exp || 0,
        },
        vip_stats: null,
      }
    }

    if (assetsResponse.success && assetsResponse.data) {
      const assetsData = assetsResponse.data.data || assetsResponse.data
      userAssets.value = {
        currency: {
          normal: assetsData.game_coins || assetsData.currency?.normal || 0,
          gold: assetsData.shop_coins || assetsData.currency?.gold || 0,
        },
        fame_points: assetsData.points || assetsData.fame_points || 0,
      }
    }

    // 额外获取详细的VIP状态信息
    try {
      const vipResponse = await vipApi.getUserVipStatus()
      if (vipResponse.success && vipResponse.data) {
        console.log('[GiftsView] VIP状态数据:', vipResponse.data)
        // 更新VIP相关数据
        userStats.value.vip_level = vipResponse.data.vip_level || null
        userStats.value.vip_stats = {
          level: vipResponse.data.vip_level || 0,
          name: vipResponse.data.vip_name,
          expire_date: vipResponse.data.vip_expire_date,
          is_permanent: vipResponse.data.is_permanent,
          is_expired: vipResponse.data.is_expired,
        }
        console.log('[GiftsView] 更新后的VIP数据:', userStats.value)
      }
    } catch (vipError) {
      console.warn('[GiftsView] 获取VIP状态失败:', vipError)
      // VIP API失败不影响基本功能，继续执行
    }
  } catch (error) {
    console.error('Failed to load user info:', error)
  }
}

// 排序后的礼包列表（可用的在前，不可用的在后）
const sortedGifts = computed(() => {
  if (!Array.isArray(availableGifts.value)) {
    return []
  }

  // 在排序模式下，保持当前顺序不变，便于拖拽
  if (sortMode.value) {
    return [...availableGifts.value]
  }

  return [...availableGifts.value].sort((a, b) => {
    const aCanClaim = canClaimGift(a)
    const bCanClaim = canClaimGift(b)

    // 可领取的礼包排在前面
    if (aCanClaim && !bCanClaim) return -1
    if (!aCanClaim && bCanClaim) return 1

    // 如果都可领取或都不可领取，按sort_order排序（如果有），否则按ID排序
    if (a.sort_order !== undefined && b.sort_order !== undefined) {
      return (a.sort_order || 0) - (b.sort_order || 0)
    }
    return (a.id || 0) - (b.id || 0)
  })
})

// 加载礼包数据
const loadGifts = async () => {
  loading.value = true
  error.value = ''

  try {
    const response = await giftsApi.getAvailableGifts()
    if (response.success) {
      availableGifts.value = response.data || []
    } else {
      error.value = response.message || '获取礼包列表失败'
    }
  } catch (err) {
    error.value = err.message || '获取礼包列表失败'
  } finally {
    loading.value = false
  }
}

// 加载领取历史
const loadClaimedHistory = async () => {
  try {
    const response = await giftsApi.getGiftHistory({ limit: 30, offset: 0 })
    if (response.success) {
      claimedHistory.value = response.data.history || []
    }
  } catch (err) {
    console.error('Failed to load claimed history:', err)
  }
}

// 领取礼包
const claimGift = async (gift) => {
  if (!canClaimGift(gift) || gift.claiming) return

  gift.claiming = true

  try {
    const response = await giftsApi.claimGift(gift.id)
    if (response.success) {
      // 显示成功消息
      showSuccessMessage(`成功领取礼包: ${gift.name}`)

      // 刷新数据
      await Promise.all([loadGifts(), loadClaimedHistory(), loadUserInfo()])
    } else {
      showErrorMessage(response.message || '领取礼包失败')
    }
  } catch (err) {
    showErrorMessage(err.message || '领取礼包失败')
  } finally {
    gift.claiming = false
  }
}

// 工具函数
const canClaimGift = (gift) => {
  // 使用API返回的can_claim字段
  if (!gift.can_claim) return false
  if (gift.total_quantity && (gift.remaining_quantity || 0) <= 0) return false

  const now = new Date()
  if (gift.start_time && new Date(gift.start_time) > now) return false
  if (gift.end_time && new Date(gift.end_time) < now) return false

  return true
}

const getClaimButtonClass = (gift) => {
  if (!canClaimGift(gift)) {
    return 'bg-gray-600 text-gray-400 cursor-not-allowed'
  }
  return 'bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-600 hover:to-orange-600 text-white shadow-lg hover:shadow-xl'
}

// 检测礼包名称中是否包含付费关键词
const isPaidGift = (giftName) => {
  if (!giftName) return false

  // 使用正则表达式进行更精确的匹配
  const paidPatterns = [
    // 中文数字 + 元
    /[一二三四五六七八九十]元/,
    // 阿拉伯数字 + 元
    /\d+元/,
    // 付费关键词（完整词汇匹配）
    /付费|收费|充值/,
  ]

  return paidPatterns.some((pattern) => pattern.test(giftName))
}

const getClaimButtonText = (gift) => {
  const isPaid = isPaidGift(gift.name)

  if (gift.claiming) return isPaid ? '购买中...' : '领取中...'

  // 使用API返回的can_claim字段
  if (!gift.can_claim) return '礼包不可用'

  if (gift.total_quantity && (gift.remaining_quantity || 0) <= 0) return '已领完'

  const now = new Date()
  if (gift.start_time && new Date(gift.start_time) > now) return '未开始'
  if (gift.end_time && new Date(gift.end_time) < now) return '已过期'

  return isPaid ? '立即购买' : '立即领取'
}

const formatClaimedHistoryLog = () => {
  if (!claimedHistory.value || claimedHistory.value.length === 0) {
    return '暂无领取记录'
  }

  // 获取当前用户的显示名称
  const currentUserName = userInfo.value?.username || userInfo.value?.nickname || '当前用户'

  return claimedHistory.value
    .slice(0, 30) // 只显示最新30条
    .map((record) => {
      const time = record.claimed_at
        ? new Date(record.claimed_at).toLocaleString('zh-CN')
        : '未知时间'

      // 由于这是当前用户的领取历史，直接使用当前用户信息
      const user = currentUserName

      const gift = record.gift_name || record.name || '未知礼包'

      return `[${time}] ${user} 领取了 ${gift}`
    })
    .join('\n')
}

const formatDateRange = (start, end) => {
  if (!start || !end) return '永久有效'
  const startDate = new Date(start).toLocaleDateString('zh-CN')
  const endDate = new Date(end).toLocaleDateString('zh-CN')
  return `${startDate} - ${endDate}`
}

const showSuccessMessage = (message) => {
  // 这里可以集成通知组件
  alert(message)
}

const showErrorMessage = (message) => {
  // 这里可以集成通知组件
  alert(message)
}

// 排序功能
const toggleSortMode = () => {
  sortMode.value = !sortMode.value

  // 退出排序模式时清理拖拽状态
  if (!sortMode.value) {
    draggedItemIndex.value = null
    draggedItem.value = null
    dragOverIndex.value = null
  }
}

// 拖拽处理函数
const handleDragStart = (index, giftId) => {
  if (!sortMode.value) return
  draggedItemIndex.value = index
  draggedItem.value = giftId
}

const handleDragOver = (index) => {
  if (!sortMode.value) return
  if (draggedItemIndex.value !== null && draggedItemIndex.value !== index) {
    dragOverIndex.value = index
  }
}

const handleDragEnter = (index) => {
  if (!sortMode.value) return
  if (draggedItemIndex.value !== null && draggedItemIndex.value !== index) {
    dragOverIndex.value = index
  }
}

const handleDragLeave = () => {
  if (!sortMode.value) return
  dragOverIndex.value = null
}

const handleDrop = async (toIndex) => {
  if (!sortMode.value) return
  if (draggedItemIndex.value !== null && draggedItemIndex.value !== toIndex) {
    try {
      // 获取当前显示的礼包列表的副本
      const giftsCopy = [...availableGifts.value]

      // 移除被拖拽的礼包
      const [movedGift] = giftsCopy.splice(draggedItemIndex.value, 1)

      // 插入到新位置
      giftsCopy.splice(toIndex, 0, movedGift)

      // 更新sortOrder以反映新的顺序
      giftsCopy.forEach((gift, index) => {
        gift.sortOrder = index
      })

      // 更新礼包数组
      availableGifts.value = giftsCopy

      // TODO: 这里可以调用API来保存新的排序到服务器
      // await giftsApi.updateGiftSort(giftsCopy)

      console.log('[Gifts] Gifts reordered successfully')
    } catch (error) {
      console.error('[Gifts] Failed to reorder gifts:', error)
    }
  }
  dragOverIndex.value = null
}

const handleDragEnd = () => {
  if (!sortMode.value) return
  draggedItemIndex.value = null
  draggedItem.value = null
  dragOverIndex.value = null
}

const handleLogout = async () => {
  try {
    await authApi.logout()
    router.push('/login')
  } catch (error) {
    console.error('Logout failed:', error)
    router.push('/login')
  }
}

// 生命周期
onMounted(async () => {
  await Promise.all([loadUserInfo(), loadGifts(), loadClaimedHistory()])
})
</script>

<style scoped>
.item-grid-container {
  min-height: 200px;
}

/* 自定义滚动条 */
.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: rgba(75, 85, 99, 0.3);
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: rgba(156, 163, 175, 0.5);
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: rgba(156, 163, 175, 0.7);
}
</style>
