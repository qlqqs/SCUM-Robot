<template>
  <div
    data-profile-view
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
        <!-- Page Header -->
        <div class="flex flex-col sm:flex-row justify-between items-center mb-6 gap-4">
          <div class="flex items-center gap-3">
            <i class="fas fa-user text-2xl text-cyan-400"></i>
            <h1 class="text-2xl font-bold text-white">个人信息</h1>
          </div>
          <div class="flex items-center gap-2">
            <button
              @click="goToStore"
              class="px-4 py-2 text-sm bg-green-600 hover:bg-green-700 text-white rounded-md transition-colors"
            >
              <i class="fas fa-store mr-1"></i>
              返回商城
            </button>
          </div>
        </div>

        <!-- Profile Content -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- 基本信息卡片 -->
          <div class="bg-gray-900 bg-opacity-50 rounded-lg p-6">
            <h2 class="text-xl font-semibold text-white mb-4 flex items-center">
              <i class="fas fa-id-card mr-2 text-blue-400"></i>
              基本信息
            </h2>

            <div class="space-y-4">
              <div
                class="flex items-center justify-between p-3 bg-gray-800 bg-opacity-50 rounded-lg"
              >
                <div class="flex items-center">
                  <i class="fas fa-user text-cyan-400 mr-3"></i>
                  <span class="text-gray-300">用户名</span>
                </div>
                <span class="text-white font-medium">{{ userInfo.username || 'N/A' }}</span>
              </div>

              <div
                class="flex items-center justify-between p-3 bg-gray-800 bg-opacity-50 rounded-lg"
              >
                <div class="flex items-center">
                  <i class="fas fa-gamepad text-cyan-400 mr-3"></i>
                  <span class="text-gray-300">Steam ID</span>
                </div>
                <span class="text-white font-medium">{{ userInfo.steam_id || 'N/A' }}</span>
              </div>

              <div
                class="flex items-center justify-between p-3 bg-gray-800 bg-opacity-50 rounded-lg"
              >
                <div class="flex items-center">
                  <i class="fas fa-envelope text-cyan-400 mr-3"></i>
                  <span class="text-gray-300">邮箱</span>
                </div>
                <span class="text-white font-medium">{{ userInfo.email || 'N/A' }}</span>
              </div>

              <div
                class="flex items-center justify-between p-3 bg-gray-800 bg-opacity-50 rounded-lg"
              >
                <div class="flex items-center">
                  <i class="fas fa-calendar text-cyan-400 mr-3"></i>
                  <span class="text-gray-300">注册时间</span>
                </div>
                <span class="text-white font-medium">{{ formatDate(userInfo.created_at) }}</span>
              </div>
            </div>

            <button
              @click="editMode = !editMode"
              class="mt-4 w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            >
              <i class="fas fa-edit mr-2"></i>
              {{ editMode ? '取消编辑' : '编辑信息' }}
            </button>
          </div>

          <!-- 游戏数据卡片 -->
          <div class="bg-gray-900 bg-opacity-50 rounded-lg p-6">
            <h2 class="text-xl font-semibold text-white mb-4 flex items-center">
              <i class="fas fa-gamepad mr-2 text-green-400"></i>
              游戏数据
            </h2>

            <div class="space-y-4">
              <div
                class="flex items-center justify-between p-3 bg-gray-800 bg-opacity-50 rounded-lg"
              >
                <div class="flex items-center">
                  <i class="fas fa-coins text-yellow-400 mr-3"></i>
                  <span class="text-gray-300">普通币</span>
                </div>
                <span class="text-yellow-400 font-bold">{{
                  formatNumber(userAssets.currency?.normal || 0)
                }}</span>
              </div>

              <div
                class="flex items-center justify-between p-3 bg-gray-800 bg-opacity-50 rounded-lg"
              >
                <div class="flex items-center">
                  <i class="fas fa-gem text-purple-400 mr-3"></i>
                  <span class="text-gray-300">金币</span>
                </div>
                <span class="text-purple-400 font-bold">{{
                  formatNumber(userAssets.currency?.gold || 0)
                }}</span>
              </div>

              <div
                class="flex items-center justify-between p-3 bg-gray-800 bg-opacity-50 rounded-lg"
              >
                <div class="flex items-center">
                  <i class="fas fa-trophy text-orange-400 mr-3"></i>
                  <span class="text-gray-300">声望积分</span>
                </div>
                <span class="text-orange-400 font-bold">{{
                  formatNumber(userAssets.fame_points || 0)
                }}</span>
              </div>

              <div
                class="flex items-center justify-between p-3 bg-gray-800 bg-opacity-50 rounded-lg"
                v-if="userStats.vip_level !== undefined || userStats.vip_stats"
              >
                <div class="flex items-center">
                  <i class="fas fa-crown text-yellow-400 mr-3"></i>
                  <span class="text-gray-300">VIP等级</span>
                </div>
                <span class="text-yellow-400 font-bold">{{
                  userStats.vip_level || userStats.vip_stats?.level || 0
                }}</span>
              </div>

              <div
                class="flex items-center justify-between p-3 bg-gray-800 bg-opacity-50 rounded-lg"
                v-if="userStats.pass_stats"
              >
                <div class="flex items-center">
                  <i class="fas fa-star text-cyan-400 mr-3"></i>
                  <span class="text-gray-300">通行证等级</span>
                </div>
                <span class="text-cyan-400 font-bold"
                  >Lv.{{ userStats.pass_stats.level || 0 }}</span
                >
              </div>

              <div
                class="flex items-center justify-between p-3 bg-gray-800 bg-opacity-50 rounded-lg"
              >
                <div class="flex items-center">
                  <i class="fas fa-clock text-green-400 mr-3"></i>
                  <span class="text-gray-300">在线时长</span>
                </div>
                <span class="text-green-400 font-bold">{{ userInfo.onlineNumber }} 小时</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '@/api/services/authApi.js'
import { usersApi } from '@/api/services/usersApi.js'
import { vipApi } from '@/api/services/vipApi.js'
import GameHeader from '../components/GameHeader.vue'

const router = useRouter()

// 编辑模式
const editMode = ref(false)

// 用户信息（用于Header）
const userInfo = ref({
  user_id: null,
  steam_id: null,
  username: '',
  email: '',
  user_type: 'user',
  is_admin: false,
  is_super_admin: false,
  created_at: null,
  last_login: null,
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

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

// 格式化数字
const formatNumber = (number) => {
  if (!number && number !== 0) return '0'
  return number.toLocaleString()
}

// 导航函数
const goToStore = () => {
  router.push('/store')
}

// 注销函数
const handleLogout = async () => {
  try {
    await authApi.logout()
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('rememberedUser')
    router.push('/login')
  } catch (error) {
    console.error('注销失败:', error)
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('rememberedUser')
    router.push('/login')
  }
}

// 加载用户数据
const loadUserData = async () => {
  try {
    // 获取当前用户基本信息
    const currentUserResponse = await usersApi.getCurrentUser()

    if (currentUserResponse.success && currentUserResponse.data) {
      // 映射API响应数据到组件数据结构
      // 注意：currentUserResponse.data 是整个API响应，真正的用户数据在 data.data 中
      const apiData = currentUserResponse.data.data || currentUserResponse.data
      console.log('[ProfileView] 提取的用户数据:', apiData)
      userInfo.value = {
        user_id: apiData.id || apiData.user_id,
        steam_id: apiData.steam_id,
        username: apiData.username,
        email: apiData.email,
        user_type: apiData.user_type || 'user',
        is_admin: apiData.is_admin || false,
        is_super_admin: apiData.is_super_admin || false,
        created_at: apiData.created_at,
        last_login: apiData.last_login,
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

      console.log('[ProfileView] 映射后的用户信息:', userInfo.value)
      console.log('[ProfileView] 映射后的用户统计:', userStats.value)
    } else {
      // 如果API没有返回数据，尝试从localStorage获取
      const storedUserInfo = authApi.getCurrentUserFromStorage()
      if (storedUserInfo) {
        userInfo.value = storedUserInfo
      }
    }

    // 额外获取详细的VIP状态信息
    try {
      const vipResponse = await vipApi.getUserVipStatus()
      if (vipResponse.success && vipResponse.data) {
        console.log('[ProfileView] VIP状态数据:', vipResponse.data)
        // 更新VIP相关数据
        userStats.value.vip_level = vipResponse.data.vip_level || null
        userStats.value.vip_stats = {
          level: vipResponse.data.vip_level || 0,
          name: vipResponse.data.vip_name,
          expire_date: vipResponse.data.vip_expire_date,
          is_permanent: vipResponse.data.is_permanent,
          is_expired: vipResponse.data.is_expired,
        }
        console.log('[ProfileView] 更新后的VIP数据:', userStats.value)
      }
    } catch (vipError) {
      console.warn('[ProfileView] 获取VIP状态失败:', vipError)
      // VIP API失败不影响基本功能，继续执行
    }

    // 获取用户统计信息
    try {
      const statsResponse = await usersApi.getUserStats()
      if (statsResponse.success) {
        const apiData = statsResponse.data.data || statsResponse.data
        console.log('[ProfileView] 提取的用户统计数据:', apiData)
        // 保留VIP数据，只更新其他统计信息
        userStats.value = {
          ...userStats.value, // 保留现有数据（包括VIP数据）
          ...apiData, // 更新统计数据
          // 确保VIP数据不被覆盖
          vip_level: userStats.value.vip_level,
          vip_stats: userStats.value.vip_stats,
        }
      }
    } catch (error) {
      console.warn('获取用户统计信息失败:', error)
    }

    // 获取用户资产信息
    try {
      const assetsResponse = await usersApi.getUserAssets()
      if (assetsResponse.success) {
        const apiData = assetsResponse.data.data || assetsResponse.data
        console.log('[ProfileView] 提取的用户资产数据:', apiData)
        userAssets.value = {
          currency: {
            normal: apiData.game_coins || 0,
            gold: apiData.shop_coins || 0,
          },
          fame_points: apiData.points || 0,
          items: [],
        }
        console.log('[ProfileView] 映射后的用户资产:', userAssets.value)
      }
    } catch (error) {
      console.warn('获取用户资产信息失败:', error)
    }
  } catch (error) {
    console.error('加载用户数据失败:', error)
    // 如果获取用户信息失败，可能是token过期，跳转到登录页
    if (error.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      router.push('/login')
    }
  }
}

// 组件挂载时加载用户数据
onMounted(async () => {
  await loadUserData()
})
</script>

<style scoped>
.backdrop-blur-md {
  backdrop-filter: blur(12px);
}

.bg-opacity-60 {
  background-color: rgba(31, 41, 55, 0.6);
}

.bg-opacity-50 {
  background-color: rgba(17, 24, 39, 0.5);
}

/* 卡片悬停效果 */
.hover\:bg-opacity-70:hover {
  background-color: rgba(17, 24, 39, 0.7);
}

/* 按钮动画 */
button {
  transition: all 0.2s ease-in-out;
}

button:hover {
  transform: translateY(-1px);
}
</style>
