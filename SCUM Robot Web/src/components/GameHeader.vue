<template>
  <header
    class="bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 bg-opacity-95 backdrop-blur-lg shadow-2xl z-20 border-b border-gray-700/50"
  >
    <div class="max-w-full mx-auto px-4 lg:px-6">
      <!-- Top Nav-->
      <div
        class="flex flex-col lg:flex-row justify-between items-center text-sm py-3 border-b border-gray-600/30 gap-3"
      >
        <nav class="flex items-center justify-center gap-1 lg:gap-2 flex-wrap w-full lg:w-auto">
          <!--
          <router-link to="#" class="nav-link group">
            <i
              class="fas fa-id-card mr-1.5 text-blue-400 group-hover:text-blue-300 transition-colors"
            ></i>
            <span>通行证</span>
          </router-link>
          -->
          <router-link
            to="/store"
            class="nav-link group"
            :class="{ 'nav-link-active': $route.path === '/store' || $route.path === '/' }"
          >
            <i
              class="fas fa-store mr-1.5 text-yellow-400 group-hover:text-yellow-300 transition-colors"
            ></i>
            <span>商城</span>
          </router-link>
          <router-link
            to="/gifts"
            class="nav-link group"
            :class="{ 'nav-link-active': $route.path === '/gifts' }"
          >
            <i
              class="fas fa-gift mr-1.5 text-purple-400 group-hover:text-purple-300 transition-colors"
            ></i>
            <span>礼包</span>
          </router-link>
          <!--
          <router-link to="#" class="nav-link group">
            <i
              class="fas fa-location-arrow mr-1.5 text-green-400 group-hover:text-green-300 transition-colors"
            ></i>
            <span>传送</span>
          </router-link>
          -->
          <router-link
            to="/recharge"
            class="nav-link group"
            :class="{ 'nav-link-active': $route.path === '/recharge' }"
          >
            <i
              class="fas fa-donate mr-1.5 text-pink-400 group-hover:text-pink-300 transition-colors"
            ></i>
            <span>赞助</span>
          </router-link>
        </nav>
        <nav class="flex items-center gap-1 lg:gap-2 flex-wrap">
          <router-link
            v-if="isAdmin"
            to="/admin"
            class="nav-link group"
            :class="{ 'nav-link-active': $route.path.startsWith('/admin') }"
          >
            <i
              class="fas fa-shield-halved mr-1.5 text-red-400 group-hover:text-red-300 transition-colors"
            ></i>
            <span>管理</span>
          </router-link>
          <router-link to="/profile" class="nav-link group">
            <i
              class="fas fa-user mr-1.5 text-cyan-400 group-hover:text-cyan-300 transition-colors"
            ></i>
            <span>个人信息</span>
          </router-link>
          <button @click="logout" class="logout-btn group">
            <i
              class="fas fa-sign-out-alt mr-1.5 group-hover:rotate-12 transition-transform duration-200"
            ></i>
            <span>注销</span>
          </button>
        </nav>
      </div>
      <!-- Bottom Nav / Info -->
      <div
        class="flex flex-col sm:flex-row justify-between items-start sm:items-center text-sm py-3 gap-3"
      >
        <div class="flex items-center gap-3 sm:gap-6 text-gray-300 flex-wrap">
          <div class="info-item group">
            <i
              class="fas fa-user text-cyan-400 mr-2 group-hover:scale-110 transition-transform"
            ></i>
            <span class="text-gray-400">昵称:</span>
            <span class="text-white font-medium ml-1">{{ userInfo.username || 'N/A' }}</span>
          </div>
          <div class="info-item group">
            <i
              class="fas fa-gamepad text-blue-400 mr-2 group-hover:scale-110 transition-transform"
            ></i>
            <span class="text-gray-400">SteamID:</span>
            <span class="text-white font-medium ml-1">{{ formatSteamId(userInfo.steam_id) }}</span>
          </div>
          <div class="info-item group">
            <i
              class="fas fa-money-bill text-green-400 mr-2 group-hover:scale-110 transition-transform"
            ></i>
            <span class="text-gray-400">{{ gameCurrencyName }}:</span>
            <span class="text-yellow-300 font-medium ml-1">{{
              formatNumber(userAssets.currency?.normal || 0)
            }}</span>
          </div>
          <div class="info-item group">
            <i
              class="fas fa-coins text-yellow-400 mr-2 group-hover:scale-110 transition-transform"
            ></i>
            <span class="text-gray-400">{{ shopCurrencyName }}:</span>
            <span class="text-green-300 font-medium ml-1">{{
              formatNumber(userAssets.currency?.gold || 0)
            }}</span>
          </div>
          <!-- VIP等级显示 -->
          <div
            class="info-item group"
            v-if="
              (userStats.vip_level !== undefined && userStats.vip_level !== null) ||
              (userStats.vip_stats && Object.keys(userStats.vip_stats).length > 0)
            "
          >
            <i
              class="fas fa-crown text-yellow-400 mr-2 group-hover:scale-110 transition-transform"
            ></i>
            <span class="text-gray-400">VIP等级:</span>
            <span class="text-yellow-300 font-medium ml-1">{{
              userStats.vip_level || userStats.vip_stats?.level || 0
            }}</span>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useSystemConfigStore } from '@/stores/systemConfigStore.js'

// Props
const props = defineProps({
  userInfo: {
    type: Object,
    required: true,
  },
  userStats: {
    type: Object,
    default: () => ({}),
  },
  userAssets: {
    type: Object,
    default: () => ({}),
  },
})

// 调试日志 (已修复，可以移除)
// console.log('[GameHeader] Props received:')
// console.log('[GameHeader] userInfo:', props.userInfo)
// console.log('[GameHeader] userStats:', props.userStats)
// console.log('[GameHeader] userAssets:', props.userAssets)

// Emits
const emit = defineEmits(['logout'])

// 系统配置
const systemConfigStore = useSystemConfigStore()

// 计算属性
const isAdmin = computed(() => {
  if (!props.userInfo) return false

  // 检查多种可能的管理员权限字段
  return (
    props.userInfo.role === 'admin' ||
    props.userInfo.is_admin === true ||
    props.userInfo.is_super_admin === true ||
    props.userInfo.permissions?.includes('admin') ||
    props.userInfo.user_type === 'admin' ||
    props.userInfo.user_type === 'super_admin'
  )
})

// 货币名称（从系统配置获取）
const gameCurrencyName = computed(() => systemConfigStore.gameCurrencyName)
const shopCurrencyName = computed(() => systemConfigStore.shopCurrencyName)

// 方法
const logout = () => {
  emit('logout')
}

const formatSteamId = (steamId) => {
  if (!steamId) return 'N/A'
  return steamId.toString()
}

const formatNumber = (number) => {
  if (!number && number !== 0) return '0'
  return number.toLocaleString()
}

// 组件挂载时加载系统配置
onMounted(() => {
  systemConfigStore.loadConfig()
})
</script>

<style scoped>
/* 导航链接样式 */
.nav-link {
  padding: 0.5rem 0.75rem;
  border-radius: 0.5rem;
  color: rgb(209 213 219);
  transition: all 0.2s ease-in-out;
  white-space: nowrap;
  display: flex;
  align-items: center;
  border: 1px solid transparent;
  backdrop-filter: blur(4px);
}

.nav-link:hover {
  color: white;
  background-color: rgba(55, 65, 81, 0.5);
  border-color: rgba(75, 85, 99, 0.5);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.nav-link-active {
  color: white;
  background: linear-gradient(to right, rgba(37, 99, 235, 0.2), rgba(147, 51, 234, 0.2));
  border-color: rgba(59, 130, 246, 0.3);
  box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.1);
}

/* 注销按钮样式 */
.logout-btn {
  padding: 0.5rem 0.75rem;
  border-radius: 0.5rem;
  background: linear-gradient(to right, rgb(220, 38, 38), rgb(185, 28, 28));
  color: white;
  transition: all 0.2s ease-in-out;
  white-space: nowrap;
  display: flex;
  align-items: center;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.logout-btn:hover {
  background: linear-gradient(to right, rgb(185, 28, 28), rgb(153, 27, 27));
  border-color: rgba(248, 113, 113, 0.5);
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(239, 68, 68, 0.3);
}

/* 信息项样式 */
.info-item {
  display: flex;
  align-items: center;
  white-space: nowrap;
  padding: 0.25rem 0.5rem;
  border-radius: 0.375rem;
  transition: all 0.2s ease-in-out;
  cursor: default;
}

.info-item:hover {
  background-color: rgba(31, 41, 55, 0.3);
  backdrop-filter: blur(8px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* 背景模糊效果 */
.backdrop-blur-lg {
  backdrop-filter: blur(16px);
}

/* 渐变背景 */
.bg-gradient-to-r {
  background-image: linear-gradient(
    to right,
    rgba(17, 24, 39, 0.95),
    rgba(31, 41, 55, 0.95),
    rgba(17, 24, 39, 0.95)
  );
}

/* 响应式调整 */
@media (max-width: 640px) {
  .nav-link {
    padding: 0.375rem 0.5rem;
    font-size: 0.875rem;
  }

  .logout-btn {
    padding: 0.375rem 0.5rem;
    font-size: 0.875rem;
  }

  .info-item {
    font-size: 0.75rem;
    padding: 0.25rem;
  }
}

/* 动画关键帧 */
@keyframes pulse-glow {
  0%,
  100% {
    box-shadow: 0 0 5px rgba(59, 130, 246, 0.3);
  }
  50% {
    box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
  }
}

.nav-link-active {
  animation: pulse-glow 3s ease-in-out infinite;
}

/* 图标悬停效果 */
.group:hover .fas {
  filter: drop-shadow(0 0 4px currentColor);
}
</style>
