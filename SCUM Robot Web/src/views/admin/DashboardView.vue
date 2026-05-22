<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold">仪表盘</h2>
      <div class="flex items-center gap-4">
        <!-- API状态指示器 -->
        <div class="flex items-center gap-2">
          <div
            :class="['w-3 h-3 rounded-full', apiStatus.robot ? 'bg-green-500' : 'bg-red-500']"
          ></div>
          <span class="text-sm text-gray-400"> API {{ apiStatus.robot ? '正常' : '异常' }} </span>
        </div>

        <!-- 刷新按钮 -->
        <button
          @click="refreshData"
          :disabled="gameStore.isLoading || isLoadingStats"
          class="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-2 rounded transition-colors"
        >
          <i
            class="fas fa-sync-alt mr-2"
            :class="{ 'animate-spin': gameStore.isLoading || isLoadingStats }"
          ></i>
          {{ isLoadingStats ? '加载统计...' : '刷新' }}
        </button>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="gameStore.hasErrors" class="mb-6 p-4 bg-red-900/50 border border-red-500 rounded-lg">
      <div class="flex items-center">
        <i class="fas fa-exclamation-triangle text-red-400 mr-2"></i>
        <span class="text-red-200">数据加载出现问题</span>
      </div>
      <div class="mt-2 text-sm text-red-300">
        <div v-if="gameStore.errors.init">初始化错误: {{ gameStore.errors.init }}</div>
        <div v-if="gameStore.errors.categories">类目错误: {{ gameStore.errors.categories }}</div>
        <div v-if="gameStore.errors.items">物品错误: {{ gameStore.errors.items }}</div>
      </div>
      <button
        @click="gameStore.clearError()"
        class="mt-2 text-sm text-red-400 hover:text-red-300 underline"
      >
        清除错误
      </button>
    </div>

    <!-- 基础统计卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <div class="bg-gray-800 p-6 rounded-lg shadow-lg">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-lg font-semibold text-gray-400">总类目数</h3>
            <p class="text-3xl font-bold mt-2">{{ stats?.totalCategories || 0 }}</p>
            <p class="text-sm text-gray-500 mt-1">活跃: {{ stats?.activeCategories || 0 }}</p>
          </div>
          <i class="fas fa-sitemap text-3xl text-blue-500"></i>
        </div>
      </div>

      <div class="bg-gray-800 p-6 rounded-lg shadow-lg">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-lg font-semibold text-gray-400">总物品数</h3>
            <p class="text-3xl font-bold mt-2">{{ stats?.totalItems || 0 }}</p>
            <p class="text-sm text-gray-500 mt-1">活跃: {{ stats?.activeItems || 0 }}</p>
          </div>
          <i class="fas fa-boxes-stacked text-3xl text-green-500"></i>
        </div>
      </div>

      <div class="bg-gray-800 p-6 rounded-lg shadow-lg">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-lg font-semibold text-gray-400">低库存物品</h3>
            <p class="text-3xl font-bold mt-2 text-yellow-400">{{ stats?.lowStockItems || 0 }}</p>
            <p class="text-sm text-gray-500 mt-1">库存 ≤ 10</p>
          </div>
          <i class="fas fa-exclamation-triangle text-3xl text-yellow-500"></i>
        </div>
      </div>

      <div class="bg-gray-800 p-6 rounded-lg shadow-lg">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-lg font-semibold text-gray-400">缺货物品</h3>
            <p class="text-3xl font-bold mt-2 text-red-400">{{ stats?.outOfStockItems || 0 }}</p>
            <p class="text-sm text-gray-500 mt-1">库存 = 0</p>
          </div>
          <i class="fas fa-times-circle text-3xl text-red-500"></i>
        </div>
      </div>
    </div>

    <!-- 管理员统计卡片 -->

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <!-- 用户统计
      <div class="bg-gray-800 p-6 rounded-lg shadow-lg">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-lg font-semibold text-gray-400">总用户数</h3>
            <p class="text-3xl font-bold mt-2">{{ adminStats.users.total }}</p>
            <p class="text-sm text-gray-500 mt-1">在线: {{ adminStats.users.online }}</p>
          </div>
          <i class="fas fa-users text-3xl text-purple-500"></i>
        </div>
      </div>
      -->
      <!-- 签到统计
      <div class="bg-gray-800 p-6 rounded-lg shadow-lg">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-lg font-semibold text-gray-400">今日签到</h3>
            <p class="text-3xl font-bold mt-2">{{ adminStats.signin.today_signed_in }}</p>
            <p class="text-sm text-gray-500 mt-1">
              签到率: {{ adminStats.signin.signin_rate.toFixed(1) }}%
            </p>
          </div>
          <i class="fas fa-calendar-check text-3xl text-green-500"></i>
        </div>
      </div>
      -->
      <!-- VIP统计
      <div class="bg-gray-800 p-6 rounded-lg shadow-lg">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-lg font-semibold text-gray-400">VIP用户</h3>
            <p class="text-3xl font-bold mt-2">{{ adminStats.vip.total_vip_users }}</p>
            <p class="text-sm text-gray-500 mt-1">月收入: ¥{{ adminStats.vip.monthly_revenue }}</p>
          </div>
          <i class="fas fa-crown text-3xl text-yellow-500"></i>
        </div>
      </div>
      -->
      <!-- 人物能力统计
      <div class="bg-gray-800 p-6 rounded-lg shadow-lg">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-lg font-semibold text-gray-400">活跃玩家</h3>
            <p class="text-3xl font-bold mt-2">{{ adminStats.character.total_players }}</p>
            <p class="text-sm text-gray-500 mt-1">
              平均力量: {{ adminStats.character.avg_strength.toFixed(1) }}
            </p>
          </div>
          <i class="fas fa-dumbbell text-3xl text-red-500"></i>
        </div>
      </div>
      -->
    </div>

    <!-- 详细统计信息 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
      <!-- 签到详情 -->
      <div class="bg-gray-800 p-6 rounded-lg shadow-lg">
        <h3 class="text-lg font-semibold mb-4 flex items-center">
          <i class="fas fa-calendar-alt mr-2 text-green-500"></i>
          签到系统详情
        </h3>
        <div class="space-y-3">
          <div class="flex justify-between">
            <span class="text-gray-300">总用户数</span>
            <span class="text-white">{{ adminStats.signin.total_users }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-300">今日签到</span>
            <span class="text-green-400">{{ adminStats.signin.today_signed_in }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-300">签到率</span>
            <span class="text-blue-400">{{ adminStats.signin.signin_rate.toFixed(1) }}%</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-300">连续签到记录</span>
            <span class="text-purple-400">{{ adminStats.signin.consecutive_streaks }}</span>
          </div>
        </div>
      </div>

      <!-- VIP详情 -->
      <div class="bg-gray-800 p-6 rounded-lg shadow-lg">
        <h3 class="text-lg font-semibold mb-4 flex items-center">
          <i class="fas fa-gem mr-2 text-yellow-500"></i>
          VIP系统详情
        </h3>
        <div class="space-y-3">
          <div class="flex justify-between">
            <span class="text-gray-300">VIP用户总数</span>
            <span class="text-white">{{ adminStats.vip.total_vip_users }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-300">月收入</span>
            <span class="text-green-400">¥{{ adminStats.vip.monthly_revenue }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-300">即将到期</span>
            <span class="text-orange-400">{{ adminStats.vip.expiring_soon }}</span>
          </div>
          <div class="text-sm text-gray-400 mt-4">
            <div class="text-xs">VIP等级分布:</div>
            <div class="mt-2 space-y-1">
              <div
                v-for="(count, level) in adminStats.vip.vip_distribution"
                :key="level"
                class="flex justify-between"
              >
                <span>{{ level }}</span>
                <span>{{ count }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useGameStore } from '@/stores/gameStore'
import { getApiStatus, signinApi, vipApi, characterApi, usersApi } from '@/api'

const gameStore = useGameStore()

// 状态数据
const apiStatus = ref({
  robot: false,
  timestamp: null,
})

// 管理员统计数据
const adminStats = ref({
  users: {
    total: 0,
    online: 0,
    new_today: 0,
    active_this_week: 0,
  },
  signin: {
    today_signed_in: 0,
    signin_rate: 0,
    total_users: 0,
    consecutive_streaks: 0,
  },
  vip: {
    total_vip_users: 0,
    vip_distribution: {},
    monthly_revenue: 0,
    expiring_soon: 0,
  },
  character: {
    total_players: 0,
    avg_strength: 0,
    avg_stamina: 0,
    avg_intelligence: 0,
    avg_agility: 0,
  },
})

const isLoadingStats = ref(false)
let statusInterval = null

// 计算属性
const stats = computed(() => gameStore.getStats)

// 获取管理员统计数据
const loadAdminStats = async () => {
  isLoadingStats.value = true
  try {
    console.log('[Dashboard] Loading admin statistics...')

    // 并行获取所有统计数据
    const [signinStatsResult, vipStatsResult, characterStatsResult, usersResult] =
      await Promise.allSettled([
        signinApi.getAdminStats().catch((err) => {
          console.warn('[Dashboard] Signin stats failed:', err.message)
          return { success: false, data: null }
        }),
        vipApi.getAdminStats().catch((err) => {
          console.warn('[Dashboard] VIP stats failed:', err.message)
          return { success: false, data: null }
        }),
        characterApi.getSummary().catch((err) => {
          console.warn('[Dashboard] Character stats failed:', err.message)
          return { success: false, data: null }
        }),
        usersApi.listUsers({ page: 1, size: 1 }).catch((err) => {
          console.warn('[Dashboard] Users stats failed:', err.message)
          return { success: false, data: null }
        }),
      ])

    // 处理签到统计
    if (signinStatsResult.status === 'fulfilled' && signinStatsResult.value?.success) {
      const signinData = signinStatsResult.value.data
      adminStats.value.signin = {
        today_signed_in: signinData.daily_stats?.signed_in_today || 0,
        signin_rate: signinData.daily_stats?.signin_rate || 0,
        total_users: signinData.daily_stats?.total_users || 0,
        consecutive_streaks: signinData.top_streaks?.length || 0,
      }
    }

    // 处理VIP统计
    if (vipStatsResult.status === 'fulfilled' && vipStatsResult.value?.success) {
      const vipData = vipStatsResult.value.data
      adminStats.value.vip = {
        total_vip_users: vipData.total_vip_users || 0,
        vip_distribution: vipData.vip_distribution || {},
        monthly_revenue: vipData.revenue_stats?.monthly_revenue || 0,
        expiring_soon: vipData.expiration_alerts?.expiring_in_7_days || 0,
      }
    }

    // 处理人物能力统计
    if (characterStatsResult.status === 'fulfilled' && characterStatsResult.value?.success) {
      const characterData = characterStatsResult.value.data
      adminStats.value.character = {
        total_players: characterData.total_players || 0,
        avg_strength: characterData.average_stats?.strength || 0,
        avg_stamina: characterData.average_stats?.stamina || 0,
        avg_intelligence: characterData.average_stats?.intelligence || 0,
        avg_agility: characterData.average_stats?.agility || 0,
      }
    }

    // 处理用户统计
    if (usersResult.status === 'fulfilled' && usersResult.value?.success) {
      const userData = usersResult.value.data
      adminStats.value.users = {
        total: userData.total || 0,
        online: userData.online_count || 0,
        new_today: userData.new_today || 0,
        active_this_week: userData.active_this_week || 0,
      }
    }

    console.log('[Dashboard] Admin statistics loaded successfully')
  } catch (error) {
    console.error('[Dashboard] Failed to load admin stats:', error)
  } finally {
    isLoadingStats.value = false
  }
}

// 刷新数据
const refreshData = async () => {
  try {
    await Promise.all([gameStore.refreshData(), updateApiStatus(), loadAdminStats()])
  } catch (error) {
    console.error('[Dashboard] Failed to refresh data:', error)
  }
}

// 更新API状态
const updateApiStatus = async () => {
  try {
    const status = await getApiStatus()
    apiStatus.value = status
  } catch (error) {
    console.error('[Dashboard] Failed to get API status:', error)
    apiStatus.value = {
      robot: false,
      error: error.message,
      timestamp: new Date().toISOString(),
    }
  }
}

// 定期更新API状态
const startStatusPolling = () => {
  statusInterval = setInterval(updateApiStatus, 30000) // 每30秒更新一次
}

const stopStatusPolling = () => {
  if (statusInterval) {
    clearInterval(statusInterval)
    statusInterval = null
  }
}

onMounted(async () => {
  // 初始化数据
  await gameStore.initializeData()

  // 获取API状态和管理员统计
  await Promise.all([updateApiStatus(), loadAdminStats()])

  // 开始定期轮询
  startStatusPolling()
})

onUnmounted(() => {
  stopStatusPolling()
})
</script>
