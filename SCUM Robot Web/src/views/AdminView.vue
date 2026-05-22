<template>
  <div
    data-admin-view
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
    <main class="flex-grow p-4 lg:p-6 overflow-x-auto">
      <div
        class="w-4/5 mx-auto bg-gray-800/60 backdrop-blur-md rounded-lg p-4 lg:p-6 min-w-[800px]"
      >
        <!-- Admin Header -->
        <div class="flex flex-col sm:flex-row justify-between items-center mb-6 gap-4">
          <div class="flex items-center gap-3">
            <i class="fas fa-shield-halved text-2xl text-blue-400"></i>
            <h1 class="text-2xl font-bold text-white">管理后台</h1>
            <span class="bg-blue-600 text-white text-sm px-2 py-1 rounded-full"> 管理员模式 </span>
          </div>
          <div class="flex items-center gap-2">
            <!-- 备份按钮 -->
            <button
              @click="showBackupDialog = true"
              class="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
              title="创建系统备份"
            >
              <i class="fas fa-download mr-1"></i>
              备份
            </button>

            <!-- 备份管理按钮 -->
            <button
              @click="showBackupListDialog = true; loadBackupList()"
              class="px-4 py-2 text-sm bg-purple-600 hover:bg-purple-700 text-white rounded-md transition-colors"
              title="管理备份文件"
            >
              <i class="fas fa-list mr-1"></i>
              备份管理
            </button>

            <!-- 恢复按钮 -->
            <button
              @click="showRestoreDialog = true"
              class="px-4 py-2 text-sm bg-orange-600 hover:bg-orange-700 text-white rounded-md transition-colors"
              title="恢复系统备份"
            >
              <i class="fas fa-upload mr-1"></i>
              恢复
            </button>

            <button
              @click="goToStore"
              class="px-4 py-2 text-sm bg-green-600 hover:bg-green-700 text-white rounded-md transition-colors"
            >
              <i class="fas fa-store mr-1"></i>
              返回商城
            </button>
          </div>
        </div>

        <!-- Admin Content Layout -->
        <div class="flex flex-col lg:flex-row gap-6 min-w-0">
          <!-- Left Sidebar Navigation -->
          <div class="w-full lg:w-48 flex-shrink-0">
            <div class="bg-gray-900 bg-opacity-50 rounded-lg p-4">
              <h3 class="text-lg font-semibold text-white mb-4 flex items-center">
                <i class="fas fa-cogs mr-2 text-blue-400"></i>
                管理菜单
              </h3>

              <nav class="space-y-2">
                <router-link
                  to="/admin/dashboard"
                  class="admin-sidebar-link group"
                  :class="{ 'admin-sidebar-active': $route.path === '/admin/dashboard' }"
                >
                  <i
                    class="fas fa-tachometer-alt mr-3 text-blue-400 group-hover:text-blue-300 transition-colors"
                  ></i>
                  <span>仪表盘</span>
                </router-link>

                <!-- 商城配置组 -->
                <div class="admin-nav-group">
                  <button
                    @click="toggleStoreConfigMenu"
                    class="admin-sidebar-link group w-full justify-between"
                    :class="{ 'admin-sidebar-active': isStoreConfigMenuActive }"
                  >
                    <div class="flex items-center">
                      <i
                        class="fas fa-store mr-3 text-blue-400 group-hover:text-blue-300 transition-colors"
                      ></i>
                      <span>商城配置</span>
                    </div>
                    <i
                      class="fas fa-chevron-down transition-transform duration-200"
                      :class="{ 'rotate-180': storeConfigMenuExpanded }"
                    ></i>
                  </button>

                  <!-- 商城配置子菜单 -->
                  <div
                    class="admin-submenu overflow-hidden transition-all duration-300"
                    :class="storeConfigMenuExpanded ? 'max-h-32 opacity-100' : 'max-h-0 opacity-0'"
                  >
                    <router-link
                      to="/admin/categories"
                      class="admin-sidebar-sublink group"
                      :class="{ 'admin-sidebar-active': isCategoryManagementActive }"
                    >
                      <i
                        class="fas fa-sitemap mr-3 text-xs text-purple-400 group-hover:text-purple-300"
                      ></i>
                      <span>类目管理</span>
                    </router-link>
                    <router-link
                      to="/admin/items"
                      class="admin-sidebar-sublink group"
                      :class="{ 'admin-sidebar-active': $route.path === '/admin/items' }"
                    >
                      <i
                        class="fas fa-boxes-stacked mr-3 text-xs text-yellow-400 group-hover:text-yellow-300"
                      ></i>
                      <span>物品管理</span>
                    </router-link>
                  </div>
                </div>

                <!-- 礼包配置 -->
                <router-link
                  to="/admin/gifts"
                  class="admin-sidebar-link group"
                  :class="{ 'admin-sidebar-active': $route.path === '/admin/gifts' }"
                >
                  <i
                    class="fas fa-gift mr-3 text-pink-400 group-hover:text-pink-300 transition-colors"
                  ></i>
                  <span>礼包配置</span>
                </router-link>

                <!-- VIP配置 -->
                <router-link
                  to="/admin/vip"
                  class="admin-sidebar-link group"
                  :class="{ 'admin-sidebar-active': $route.path === '/admin/vip' }"
                >
                  <i
                    class="fas fa-crown mr-3 text-yellow-400 group-hover:text-yellow-300 transition-colors"
                  ></i>
                  <span>VIP配置</span>
                </router-link>

                <!-- 用户管理 -->
                <router-link
                  to="/admin/users"
                  class="admin-sidebar-link group"
                  :class="{ 'admin-sidebar-active': $route.path === '/admin/users' }"
                >
                  <i
                    class="fas fa-users mr-3 text-blue-400 group-hover:text-blue-300 transition-colors"
                  ></i>
                  <span>用户管理</span>
                </router-link>

                <!-- 支付配置 -->
                <router-link
                  to="/admin/packages"
                  class="admin-sidebar-link group"
                  :class="{ 'admin-sidebar-active': $route.path === '/admin/packages' }"
                >
                  <i
                    class="fas fa-credit-card mr-3 text-green-400 group-hover:text-green-300 transition-colors"
                  ></i>
                  <span>套餐配置</span>
                </router-link>

                <!-- 订单管理 -->
                <router-link
                  to="/admin/orders"
                  class="admin-sidebar-link group"
                  :class="{ 'admin-sidebar-active': $route.path === '/admin/orders' }"
                >
                  <i
                    class="fas fa-file-invoice-dollar mr-3 text-cyan-400 group-hover:text-cyan-300 transition-colors"
                  ></i>
                  <span>订单管理</span>
                </router-link>

                <!-- 系统设置 -->
                <div class="mb-2">
                  <button
                    @click="toggleSettingsMenu"
                    class="admin-sidebar-link group w-full flex items-center justify-between"
                    :class="{ 'admin-sidebar-active': $route.path.startsWith('/admin/settings') }"
                  >
                    <div class="flex items-center">
                      <i
                        class="fas fa-cogs mr-3 text-purple-400 group-hover:text-purple-300 transition-colors"
                      ></i>
                      <span>系统设置</span>
                    </div>
                    <i
                      class="fas fa-chevron-down text-xs transition-transform duration-200"
                      :class="{ 'rotate-180': showSettingsMenu }"
                    ></i>
                  </button>

                  <!-- 系统设置二级菜单 -->
                  <div
                    class="admin-submenu overflow-hidden transition-all duration-300"
                    :class="showSettingsMenu ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'"
                  >
                    <router-link
                      to="/admin/settings/system"
                      class="admin-sidebar-sublink group"
                      :class="{ 'admin-sidebar-active': $route.path === '/admin/settings/system' }"
                    >
                      <i
                        class="fas fa-cogs mr-3 text-xs text-blue-400 group-hover:text-blue-300"
                      ></i>
                      <span>网站配置</span>
                    </router-link>

                    <router-link
                      to="/admin/settings/api"
                      class="admin-sidebar-sublink group"
                      :class="{ 'admin-sidebar-active': $route.path === '/admin/settings/api' }"
                    >
                      <i
                        class="fas fa-plug mr-3 text-xs text-green-400 group-hover:text-green-300"
                      ></i>
                      <span>API配置</span>
                    </router-link>

                    <router-link
                      to="/admin/settings/security"
                      class="admin-sidebar-sublink group"
                      :class="{
                        'admin-sidebar-active': $route.path === '/admin/settings/security',
                      }"
                    >
                      <i
                        class="fas fa-shield-alt mr-3 text-xs text-red-400 group-hover:text-red-300"
                      ></i>
                      <span>安全配置</span>
                    </router-link>

                    <router-link
                      to="/admin/settings/game"
                      class="admin-sidebar-sublink group"
                      :class="{ 'admin-sidebar-active': $route.path === '/admin/settings/game' }"
                    >
                      <i
                        class="fas fa-gamepad mr-3 text-xs text-yellow-400 group-hover:text-yellow-300"
                      ></i>
                      <span>游戏配置</span>
                    </router-link>

                    <router-link
                      to="/admin/settings/user"
                      class="admin-sidebar-sublink group"
                      :class="{ 'admin-sidebar-active': $route.path === '/admin/settings/user' }"
                    >
                      <i
                        class="fas fa-users mr-3 text-xs text-purple-400 group-hover:text-purple-300"
                      ></i>
                      <span>用户配置</span>
                    </router-link>

                    <router-link
                      to="/admin/settings/notification"
                      class="admin-sidebar-sublink group"
                      :class="{
                        'admin-sidebar-active': $route.path === '/admin/settings/notification',
                      }"
                    >
                      <i
                        class="fas fa-bell mr-3 text-xs text-orange-400 group-hover:text-orange-300"
                      ></i>
                      <span>通知配置</span>
                    </router-link>

                    <router-link
                      to="/admin/settings/performance"
                      class="admin-sidebar-sublink group"
                      :class="{
                        'admin-sidebar-active': $route.path === '/admin/settings/performance',
                      }"
                    >
                      <i
                        class="fas fa-tachometer-alt mr-3 text-xs text-cyan-400 group-hover:text-cyan-300"
                      ></i>
                      <span>性能配置</span>
                    </router-link>
                  </div>
                </div>
              </nav>
            </div>
          </div>

          <!-- Right Content Area -->
          <div class="flex-1 min-w-0">
            <div class="bg-transparent rounded-lg p-4 lg:p-6 min-w-0">
              <router-view />
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>

  <!-- 备份对话框 -->
  <div v-if="showBackupDialog" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-gray-800 rounded-lg p-6 w-96 max-w-full mx-4">
      <h3 class="text-xl font-bold text-white mb-4">
        <i class="fas fa-download mr-2 text-blue-400"></i>
        创建系统备份
      </h3>

      <div class="space-y-4">
        <div>
          <label class="flex items-center text-white">
            <input
              type="checkbox"
              v-model="backupOptions.include_database"
              class="mr-2"
            >
            备份数据库
          </label>
        </div>

        <div>
          <label class="flex items-center text-white">
            <input
              type="checkbox"
              v-model="backupOptions.include_images"
              class="mr-2"
            >
            备份图片文件
          </label>
        </div>

        <div class="text-sm text-gray-400">
          <p>备份将包含：</p>
          <ul class="list-disc list-inside ml-2">
            <li v-if="backupOptions.include_database">SQLite数据库文件</li>
            <li v-if="backupOptions.include_images">用户上传的图片文件</li>
          </ul>
        </div>
      </div>

      <div class="flex justify-end gap-2 mt-6">
        <button
          @click="showBackupDialog = false"
          class="px-4 py-2 text-gray-400 hover:text-white transition-colors"
          :disabled="isCreatingBackup"
        >
          取消
        </button>
        <button
          @click="handleCreateBackup"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors disabled:opacity-50"
          :disabled="isCreatingBackup || (!backupOptions.include_database && !backupOptions.include_images)"
        >
          <i v-if="isCreatingBackup" class="fas fa-spinner fa-spin mr-2"></i>
          <i v-else class="fas fa-download mr-2"></i>
          {{ isCreatingBackup ? '创建中...' : '创建备份' }}
        </button>
      </div>
    </div>
  </div>

  <!-- 恢复对话框 -->
  <div v-if="showRestoreDialog" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-gray-800 rounded-lg p-6 w-96 max-w-full mx-4">
      <h3 class="text-xl font-bold text-white mb-4">
        <i class="fas fa-upload mr-2 text-orange-400"></i>
        恢复系统备份
      </h3>

      <div class="space-y-4">
        <div>
          <label class="block text-white mb-2">选择备份文件：</label>
          <input
            type="file"
            accept=".zip"
            @change="onBackupFileSelected"
            class="w-full text-white bg-gray-700 border border-gray-600 rounded-md p-2"
          >
        </div>

        <div v-if="selectedBackupFile" class="text-sm text-gray-400">
          <p>已选择文件: {{ selectedBackupFile.name }}</p>
          <p>文件大小: {{ formatFileSize(selectedBackupFile.size) }}</p>
        </div>

        <div>
          <label class="flex items-center text-white">
            <input
              type="checkbox"
              v-model="restoreOptions.restore_database"
              class="mr-2"
            >
            恢复数据库
          </label>
        </div>

        <div>
          <label class="flex items-center text-white">
            <input
              type="checkbox"
              v-model="restoreOptions.restore_images"
              class="mr-2"
            >
            恢复图片文件
          </label>
        </div>

        <div class="bg-red-900 bg-opacity-30 border border-red-600 rounded-md p-3">
          <p class="text-red-400 text-sm">
            <i class="fas fa-exclamation-triangle mr-2"></i>
            警告：恢复操作将覆盖当前数据，请确保已做好备份！
          </p>
        </div>
      </div>

      <div class="flex justify-end gap-2 mt-6">
        <button
          @click="showRestoreDialog = false; selectedBackupFile = null"
          class="px-4 py-2 text-gray-400 hover:text-white transition-colors"
          :disabled="isRestoringBackup"
        >
          取消
        </button>
        <button
          @click="handleRestoreBackup"
          class="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-md transition-colors disabled:opacity-50"
          :disabled="isRestoringBackup || !selectedBackupFile || (!restoreOptions.restore_database && !restoreOptions.restore_images)"
        >
          <i v-if="isRestoringBackup" class="fas fa-spinner fa-spin mr-2"></i>
          <i v-else class="fas fa-upload mr-2"></i>
          {{ isRestoringBackup ? '恢复中...' : '恢复备份' }}
        </button>
      </div>
    </div>
  </div>

  <!-- 备份列表对话框 -->
  <div v-if="showBackupListDialog" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-gray-800 rounded-lg p-6 w-[600px] max-w-full mx-4 max-h-[80vh] overflow-y-auto">
      <h3 class="text-xl font-bold text-white mb-4">
        <i class="fas fa-list mr-2 text-purple-400"></i>
        备份文件管理
      </h3>

      <div v-if="isLoadingBackupList" class="text-center py-8">
        <i class="fas fa-spinner fa-spin text-2xl text-blue-400 mb-2"></i>
        <p class="text-gray-400">加载备份列表中...</p>
      </div>

      <div v-else-if="backupList.length === 0" class="text-center py-8">
        <i class="fas fa-inbox text-4xl text-gray-500 mb-4"></i>
        <p class="text-gray-400">暂无备份文件</p>
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="backup in backupList"
          :key="backup.filename"
          class="bg-gray-700 rounded-lg p-4 flex items-center justify-between"
        >
          <div class="flex-1">
            <h4 class="text-white font-medium">{{ backup.filename }}</h4>
            <div class="text-sm text-gray-400 mt-1">
              <span>大小: {{ formatFileSize(backup.size) }}</span>
              <span class="mx-2">•</span>
              <span>创建时间: {{ formatDateTime(backup.created_at) }}</span>
              <span v-if="backup.created_by" class="mx-2">•</span>
              <span v-if="backup.created_by">创建者: {{ backup.created_by }}</span>
            </div>
          </div>

          <div class="flex items-center gap-2 ml-4">
            <button
              @click="handleDownloadBackup(backup.filename)"
              class="px-3 py-1 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
              title="下载备份文件"
            >
              <i class="fas fa-download mr-1"></i>
              下载
            </button>

            <button
              @click="handleDeleteBackup(backup.filename)"
              class="px-3 py-1 text-sm bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors"
              title="删除备份文件"
            >
              <i class="fas fa-trash mr-1"></i>
              删除
            </button>
          </div>
        </div>
      </div>

      <div class="flex justify-between items-center mt-6">
        <button
          @click="loadBackupList()"
          class="px-4 py-2 text-sm bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
          :disabled="isLoadingBackupList"
        >
          <i v-if="isLoadingBackupList" class="fas fa-spinner fa-spin mr-2"></i>
          <i v-else class="fas fa-refresh mr-2"></i>
          刷新列表
        </button>

        <button
          @click="showBackupListDialog = false"
          class="px-4 py-2 text-sm bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
        >
          关闭
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authApi } from '@/api/services/authApi.js'
import { usersApi } from '@/api/services/usersApi.js'
import { vipApi } from '@/api/services/vipApi.js'
import { useGameStore } from '@/stores/gameStore.js'
import { createBackup, getBackupList, downloadBackup, restoreBackup, deleteBackup, formatFileSize, formatDateTime } from '@/api/backup.js'
import GameHeader from '../components/GameHeader.vue'

const route = useRoute()
const router = useRouter()
const gameStore = useGameStore()

// 系统设置菜单展开状态
const showSettingsMenu = ref(false)

// 备份相关状态
const showBackupDialog = ref(false)
const showRestoreDialog = ref(false)
const showBackupListDialog = ref(false)
const backupList = ref([])
const isCreatingBackup = ref(false)
const isRestoringBackup = ref(false)
const isLoadingBackupList = ref(false)
const selectedBackupFile = ref(null)
const backupOptions = ref({
  include_database: true,
  include_images: true
})
const restoreOptions = ref({
  restore_database: true,
  restore_images: true
})

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

// 商城配置菜单展开状态
const storeConfigMenuExpanded = ref(false)

// 计算当前是否在商城配置相关页面
const isStoreConfigMenuActive = computed(() => {
  return (
    route.path.includes('/admin/categories') ||
    route.path.includes('/admin/subcategories') ||
    route.path.includes('/admin/items')
  )
})

// 计算当前是否在类目管理页面（用于显示三级菜单）
const isCategoryManagementActive = computed(() => {
  return route.path.includes('/admin/categories') || route.path.includes('/admin/subcategories')
})

// 切换商城配置菜单展开状态
const toggleStoreConfigMenu = () => {
  storeConfigMenuExpanded.value = !storeConfigMenuExpanded.value
}

// 导航函数
const goToStore = () => {
  router.push('/store')
}

// 切换系统设置菜单
const toggleSettingsMenu = () => {
  showSettingsMenu.value = !showSettingsMenu.value
}

const handleLogout = async () => {
  try {
    // 调用API注销
    await authApi.logout()

    // 清除本地存储的用户信息
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('rememberedUser')

    // 跳转到登录页面
    router.push('/login')
  } catch (error) {
    console.error('注销失败:', error)
    // 即使API调用失败，也要清除本地数据并跳转
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
      console.log('[AdminView] 提取的用户数据:', apiData)
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

      console.log('[AdminView] 映射后的用户信息:', userInfo.value)
      console.log('[AdminView] 映射后的用户统计:', userStats.value)
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
        // 更新VIP相关数据
        userStats.value.vip_level = vipResponse.data.vip_level || null
        userStats.value.vip_stats = {
          level: vipResponse.data.vip_level || 0,
          name: vipResponse.data.vip_name,
          expire_date: vipResponse.data.vip_expire_date,
          is_permanent: vipResponse.data.is_permanent,
          is_expired: vipResponse.data.is_expired,
        }
      }
    } catch (vipError) {
      console.warn('[AdminView] 获取VIP状态失败:', vipError)
      // VIP API失败不影响基本功能，继续执行
    }

    // 获取用户统计信息
    try {
      const statsResponse = await usersApi.getUserStats()
      if (statsResponse.success) {
        const apiData = statsResponse.data.data || statsResponse.data
        console.log('[AdminView] 提取的用户统计数据:', apiData)
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
        console.log('[AdminView] 提取的用户资产数据:', apiData)
        userAssets.value = {
          currency: {
            normal: apiData.game_coins || 0,
            gold: apiData.shop_coins || 0,
          },
          fame_points: apiData.points || 0,
          items: [],
        }
        console.log('[AdminView] 映射后的用户资产:', userAssets.value)
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

// 备份相关函数
const handleCreateBackup = async () => {
  try {
    isCreatingBackup.value = true
    const result = await createBackup(backupOptions.value)

    if (result.success) {
      const filename = result.backup_info.filename
      const fileSize = formatFileSize(result.backup_info.size)

      // 显示备份创建成功信息
      alert(`备份创建成功！\n文件名: ${filename}\n大小: ${fileSize}\n\n正在下载到本地...`)

      // 自动下载备份文件到本地
      try {
        await downloadBackup(filename)
        alert(`备份已成功下载到本地！\n文件名: ${filename}`)
      } catch (downloadError) {
        console.error('下载备份失败:', downloadError)
        alert(`备份创建成功，但下载失败: ${downloadError.message}\n您可以稍后在备份列表中手动下载。`)
      }

      showBackupDialog.value = false
      await loadBackupList()
    } else {
      alert('备份创建失败: ' + result.message)
    }
  } catch (error) {
    console.error('创建备份失败:', error)
    alert('创建备份失败: ' + error.message)
  } finally {
    isCreatingBackup.value = false
  }
}

const loadBackupList = async () => {
  try {
    isLoadingBackupList.value = true
    const result = await getBackupList()
    if (Array.isArray(result)) {
      backupList.value = result
    } else if (result.success && Array.isArray(result.data)) {
      backupList.value = result.data
    } else {
      backupList.value = []
    }
  } catch (error) {
    console.error('获取备份列表失败:', error)
    backupList.value = []
    alert('获取备份列表失败: ' + error.message)
  } finally {
    isLoadingBackupList.value = false
  }
}

const handleDownloadBackup = async (filename) => {
  try {
    await downloadBackup(filename)
  } catch (error) {
    console.error('下载备份失败:', error)
    alert('下载备份失败: ' + error.message)
  }
}

const handleRestoreBackup = async () => {
  if (!selectedBackupFile.value) {
    alert('请选择备份文件')
    return
  }

  if (!confirm('确定要恢复备份吗？这将覆盖当前的数据！')) {
    return
  }

  try {
    isRestoringBackup.value = true
    const result = await restoreBackup(selectedBackupFile.value, restoreOptions.value)

    if (result.success) {
      alert(`备份恢复成功！\n${result.message}`)
      showRestoreDialog.value = false
      selectedBackupFile.value = null
      // 恢复后重新加载用户数据
      await loadUserData()
    } else {
      alert('备份恢复失败: ' + result.message)
    }
  } catch (error) {
    console.error('恢复备份失败:', error)
    alert('恢复备份失败: ' + error.message)
  } finally {
    isRestoringBackup.value = false
  }
}

const handleDeleteBackup = async (filename) => {
  if (!confirm(`确定要删除备份文件 ${filename} 吗？`)) {
    return
  }

  try {
    const result = await deleteBackup(filename)
    if (result.success) {
      alert('备份文件删除成功')
      await loadBackupList()
    } else {
      alert('删除备份文件失败: ' + result.message)
    }
  } catch (error) {
    console.error('删除备份文件失败:', error)
    alert('删除备份文件失败: ' + error.message)
  }
}

const onBackupFileSelected = (event) => {
  const file = event.target.files[0]
  if (file) {
    if (!file.name.endsWith('.zip')) {
      alert('请选择ZIP格式的备份文件')
      event.target.value = ''
      return
    }
    selectedBackupFile.value = file
  }
}

// 监听路由变化，如果访问商城配置相关页面，自动展开菜单
watch(
  isStoreConfigMenuActive,
  (isActive) => {
    if (isActive) {
      storeConfigMenuExpanded.value = true
    }
  },
  { immediate: true },
)

// 监听路由变化，admin子目录切换时自动刷新数据
watch(
  () => route.path,
  async (newPath, oldPath) => {
    // 只在admin路径下且路径确实发生变化时刷新
    if (newPath.startsWith('/admin') && oldPath && newPath !== oldPath) {
      console.log('[AdminView] Route changed from', oldPath, 'to', newPath, '- refreshing data...')

      // 根据不同的页面刷新对应的数据
      try {
        if (newPath === '/admin/categories') {
          await gameStore.loadCategories()
        } else if (newPath === '/admin/subcategories') {
          await gameStore.loadSubcategories()
        } else if (newPath === '/admin/items') {
          await gameStore.loadItems()
        } else if (newPath === '/admin/dashboard') {
          // 仪表盘需要刷新所有数据
          await gameStore.refreshData()
        }
        console.log('[AdminView] Data refreshed successfully for', newPath)
      } catch (error) {
        console.error('[AdminView] Failed to refresh data for', newPath, ':', error)
      }
    }
  },
  { immediate: false },
)

// 监听路由变化，自动展开系统设置菜单
watch(
  () => route.path,
  (newPath) => {
    if (newPath.startsWith('/admin/settings') || newPath.startsWith('/admin/config')) {
      showSettingsMenu.value = true
    }
  },
  { immediate: true },
)

// 组件挂载时加载用户数据
onMounted(async () => {
  await loadUserData()
})
</script>

<style scoped>
/* 侧边栏导航链接样式 */
.admin-sidebar-link {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  color: rgb(209 213 219);
  transition: all 0.2s ease-in-out;
  text-decoration: none;
  border: 1px solid transparent;
  margin-bottom: 0.25rem;
}

.admin-sidebar-link:hover {
  color: white;
  background-color: rgba(55, 65, 81, 0.7);
  border-color: rgba(75, 85, 99, 0.5);
  transform: translateX(4px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.admin-sidebar-active {
  color: white;
  background: linear-gradient(to right, rgba(37, 99, 235, 0.3), rgba(147, 51, 234, 0.2));
  border-color: rgba(59, 130, 246, 0.4);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
}

/* 子菜单链接样式 */
.admin-sidebar-sublink {
  display: flex;
  align-items: center;
  padding: 0.5rem 1rem 0.5rem 2rem;
  color: rgb(156 163 175);
  transition: all 0.2s ease-in-out;
  text-decoration: none;
  border-radius: 0.375rem;
  margin: 0.125rem 0;
  font-size: 0.875rem;
}

.admin-sidebar-sublink:hover {
  color: white;
  background-color: rgba(55, 65, 81, 0.5);
  transform: translateX(8px);
}

/* 子菜单容器样式 */
.admin-submenu {
  background-color: rgba(17, 24, 39, 0.3);
  border-radius: 0.375rem;
  margin-top: 0.25rem;
  padding: 0.25rem;
}

/* 背景模糊效果 */
.backdrop-blur-md {
  backdrop-filter: blur(12px);
}

.bg-opacity-60 {
  background-color: rgba(31, 41, 55, 0.6);
}

.bg-opacity-50 {
  background-color: rgba(17, 24, 39, 0.5);
}

/* 菜单动画样式 */
.rotate-180 {
  transform: rotate(180deg);
}

.transition-transform {
  transition-property: transform;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 200ms;
}

/* 自定义滚动条样式 */
:deep(::-webkit-scrollbar) {
  width: 8px;
  height: 8px;
}

:deep(::-webkit-scrollbar-track) {
  background: rgba(31, 41, 55, 0.5);
  border-radius: 4px;
}

:deep(::-webkit-scrollbar-thumb) {
  background: rgba(75, 85, 99, 0.7);
  border-radius: 4px;
}

:deep(::-webkit-scrollbar-thumb:hover) {
  background: rgba(107, 114, 128, 0.8);
}

/* 响应式调整 */
@media (max-width: 1024px) {
  .admin-sidebar-link {
    padding: 0.5rem 0.75rem;
    font-size: 0.875rem;
  }

  .admin-sidebar-sublink {
    padding: 0.375rem 0.75rem 0.375rem 1.5rem;
    font-size: 0.8125rem;
  }
}

@media (max-width: 640px) {
  .admin-sidebar-link {
    padding: 0.5rem;
    font-size: 0.875rem;
  }

  .admin-sidebar-sublink {
    padding: 0.375rem 0.5rem 0.375rem 1.25rem;
    font-size: 0.8125rem;
  }
}

/* 图标悬停效果 */
.group:hover .fas {
  filter: drop-shadow(0 0 4px currentColor);
}
</style>
