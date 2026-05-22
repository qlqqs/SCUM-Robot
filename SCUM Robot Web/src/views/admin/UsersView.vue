<template>
  <div>
    <div
      class="flex flex-col xl:flex-row xl:flex-wrap xl:justify-between xl:items-start mb-6 gap-4"
    >
      <div class="flex-shrink-0">
        <h2 class="text-lg sm:text-xl lg:text-2xl font-bold">用户管理</h2>
        <p class="text-xs sm:text-sm text-gray-400 mt-1 break-words">
          当前用户数量: {{ totalUsers }} | 加载状态:
          {{ loading ? '加载中' : '已完成' }}
        </p>
      </div>
      <div
        class="flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center gap-2 sm:gap-3 xl:flex-shrink-0 xl:min-w-0 max-w-full"
      >
        <!-- 搜索筛选盒子 -->
        <div
          class="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3 sm:flex-1 sm:min-w-[380px]"
        >
          <!-- 搜索框 -->
          <div class="relative">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索用户名、邮箱或SteamID..."
              class="bg-gray-700 border border-gray-600 rounded-md py-2 pl-8 pr-3 focus:outline-none focus:ring-2 focus:ring-blue-500 w-full sm:w-40 text-sm"
            />
            <i
              class="fas fa-search absolute left-2 top-1/2 transform -translate-y-1/2 text-gray-400 text-sm"
            ></i>
          </div>

          <!-- 用户类型筛选 -->
          <select
            v-model="selectedUserType"
            class="w-full sm:w-auto sm:min-w-[100px] sm:max-w-[200px] bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">所有类型</option>
            <option value="user">普通用户</option>
            <option value="admin">管理员</option>
            <option value="super_admin">超级管理员</option>
          </select>

          <!-- 状态筛选 -->
          <select
            v-model="selectedStatus"
            class="w-full sm:w-auto sm:min-w-[100px] bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">所有状态</option>
            <option value="active">激活</option>
            <option value="inactive">未激活</option>
          </select>
        </div>

        <!-- 按钮盒子 -->
        <div
          class="flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center gap-2 sm:gap-3 sm:min-w-[200px]"
        >
          <!-- 刷新按钮 -->
          <button
            @click="loadUsers"
            :disabled="loading"
            class="w-full sm:w-auto sm:min-w-[70px] bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-3 py-2 rounded transition-colors text-sm font-medium"
          >
            <i class="fas fa-sync-alt mr-1" :class="{ 'animate-spin': loading }"></i>
            <span>刷新</span>
          </button>

          <!-- 多选按钮/下拉菜单 -->
          <div class="relative" v-if="!multiSelectMode">
            <button
              @click="toggleMultiSelectMode"
              class="w-full sm:w-auto sm:min-w-[70px] bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded transition-colors text-sm font-medium"
            >
              <i class="fas fa-check-square mr-1"></i>
              <span>多选</span>
            </button>
          </div>
          <div class="relative" v-else>
            <button
              @click="showMultiSelectDropdown = !showMultiSelectDropdown"
              class="w-full sm:w-auto sm:min-w-[90px] bg-purple-700 hover:bg-purple-800 text-white px-3 py-2 rounded transition-colors flex items-center text-sm font-medium"
            >
              <i class="fas fa-check mr-1"></i>
              <span>操作</span>
              <i
                class="fas fa-chevron-down ml-1 text-xs"
                :class="{ 'rotate-180': showMultiSelectDropdown }"
              ></i>
            </button>

            <!-- 下拉菜单 -->
            <div
              v-if="showMultiSelectDropdown"
              class="absolute right-0 top-full mt-1 min-w-[200px] bg-gray-700 border border-gray-600 rounded-md shadow-lg z-[9999]"
            >
              <button
                @click="batchActivate"
                :disabled="selectedUsers.size === 0"
                class="w-full text-left px-4 py-2 text-sm text-white hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                <i class="fas fa-user-check mr-2 text-green-400"></i>
                批量激活 ({{ selectedUsers.size }})
              </button>
              <button
                @click="batchDeactivate"
                :disabled="selectedUsers.size === 0"
                class="w-full text-left px-4 py-2 text-sm text-white hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                <i class="fas fa-user-times mr-2 text-yellow-400"></i>
                批量停用 ({{ selectedUsers.size }})
              </button>
              <button
                @click="batchDelete"
                :disabled="selectedUsers.size === 0"
                class="w-full text-left px-4 py-2 text-sm text-white hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                <i class="fas fa-trash mr-2 text-red-400"></i>
                批量删除 ({{ selectedUsers.size }})
              </button>
              <hr class="border-gray-600 my-1" />
              <button
                @click="toggleMultiSelectMode"
                class="w-full text-left px-4 py-2 text-sm text-white hover:bg-gray-600 flex items-center"
              >
                <i class="fas fa-times mr-2 text-gray-400"></i>
                取消多选
              </button>
            </div>
          </div>

          <!-- 创建用户按钮 -->
          <button
            @click="createUser"
            class="w-full sm:w-auto sm:min-w-[90px] bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded transition-colors text-sm font-medium"
          >
            <i class="fas fa-user-plus mr-1"></i>
            <span>创建用户</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 用户表格 -->
    <!-- 加载状态 -->
    <div v-if="loading" class="flex justify-center items-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      <span class="ml-3 text-gray-400">加载中...</span>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="text-center py-12">
      <div class="text-red-400 mb-4">
        <i class="fas fa-exclamation-triangle text-4xl"></i>
      </div>
      <p class="text-gray-400 mb-4">{{ error }}</p>
      <button
        @click="loadUsers"
        class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded transition-colors"
      >
        重新加载
      </button>
    </div>

    <!-- 空状态 -->
    <div v-else-if="filteredUsers.length === 0" class="text-center py-12">
      <div class="text-gray-400 mb-4">
        <i class="fas fa-users text-4xl"></i>
      </div>
      <p class="text-gray-400">{{ searchQuery ? '没有找到匹配的用户' : '暂无用户数据' }}</p>
    </div>

    <!-- 数据表格 -->
    <div v-else class="overflow-x-auto" style="min-width: 0">
      <table class="w-full text-left" style="min-width: 1200px">
        <thead>
          <tr class="border-b border-gray-700">
            <th class="p-3 min-w-[50px] w-[50px] text-center">
              <div v-if="multiSelectMode" class="flex items-center justify-center">
                <input
                  type="checkbox"
                  :checked="isAllSelected"
                  :indeterminate="isIndeterminate"
                  @change="toggleSelectAll"
                  class="w-4 h-4 text-purple-600 bg-gray-700 border-gray-600 rounded focus:ring-purple-500 focus:ring-2"
                />
              </div>
              <span v-else>序号</span>
            </th>
            <th class="p-3 min-w-[120px] w-[140px] text-center">用户名</th>
            <th class="p-3 min-w-[160px] w-[180px] text-center">邮箱</th>
            <th class="p-3 min-w-[120px] w-[140px] text-center">SteamID</th>
            <th class="p-3 min-w-[80px] w-[100px] text-center">用户类型</th>
            <th class="p-3 min-w-[70px] w-[80px] text-center">状态</th>
            <th class="p-3 min-w-[100px] w-[120px] text-center">注册时间</th>
            <th class="p-3 min-w-[100px] w-[120px] text-center">最后登录</th>
            <th class="p-3 min-w-[100px] w-[120px] text-center">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(user, index) in paginatedUsers"
            :key="user.user_id || user.id"
            class="border-b border-gray-700 hover:bg-gray-700/50"
          >
            <td class="p-3 text-center">
              <!-- 多选模式下显示复选框 -->
              <div v-if="multiSelectMode" class="flex items-center justify-center">
                <input
                  type="checkbox"
                  :checked="selectedUsers.has(user.user_id || user.id)"
                  @change="toggleUserSelection(user.user_id || user.id)"
                  class="w-4 h-4 text-purple-600 bg-gray-700 border-gray-600 rounded focus:ring-purple-500 focus:ring-2"
                />
              </div>
              <!-- 普通模式下显示排序序号 -->
              <span v-else class="text-gray-400 text-base">
                {{ (currentPage - 1) * pageSize + index + 1 }}
              </span>
            </td>
            <td class="p-3 text-center">
              <div class="font-medium text-white text-base">{{ user.username || 'N/A' }}</div>
            </td>
            <td class="p-3 text-center">
              <div class="text-gray-300 text-base">{{ user.email || 'N/A' }}</div>
            </td>
            <td class="p-3 text-center">
              <div class="text-gray-300 font-mono text-base">{{ user.steam_id || 'N/A' }}</div>
            </td>
            <td class="p-3 text-center">
              <span
                class="px-2 py-1 rounded-full text-sm font-medium inline-block"
                :class="{
                  'bg-red-900/50 text-red-400 border border-red-500/50':
                    user.user_type === 'super_admin',
                  'bg-yellow-900/50 text-yellow-400 border border-yellow-500/50':
                    user.user_type === 'admin',
                  'bg-blue-900/50 text-blue-400 border border-blue-500/50':
                    user.user_type === 'user',
                }"
              >
                {{
                  user.user_type === 'super_admin'
                    ? '超级管理员'
                    : user.user_type === 'admin'
                      ? '管理员'
                      : '普通用户'
                }}
              </span>
            </td>
            <td class="p-3 text-center">
              <span
                class="px-2 py-1 rounded-full text-sm font-medium inline-block"
                :class="{
                  'bg-green-900/50 text-green-400 border border-green-500/50':
                    user.is_active === 1 || user.is_active === true,
                  'bg-red-900/50 text-red-400 border border-red-500/50':
                    user.is_active === 0 || user.is_active === false,
                }"
              >
                {{ user.is_active === 1 || user.is_active === true ? '激活' : '未激活' }}
              </span>
            </td>
            <td class="p-3 text-center">
              <div class="text-gray-300 text-base">
                {{ user.created_at ? formatDate(user.created_at) : 'N/A' }}
              </div>
            </td>
            <td class="p-3 text-center">
              <div class="text-gray-300 text-base">
                {{ user.last_login_at ? formatDate(user.last_login_at) : '从未登录' }}
              </div>
            </td>
            <td class="p-3 text-center">
              <div class="flex items-center justify-center gap-2">
                <button
                  @click="editUser(user)"
                  class="text-blue-400 hover:text-blue-300 text-sm px-2 py-1 rounded transition-colors"
                  title="编辑用户"
                >
                  <i class="fas fa-edit text-base"></i>
                </button>
                <button
                  @click="deleteUser(user)"
                  class="text-red-400 hover:text-red-300 text-sm px-2 py-1 rounded transition-colors"
                  title="删除用户"
                >
                  <i class="fas fa-trash text-base"></i>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 分页控件 -->
    <div v-if="totalPages > 1" class="flex justify-between items-center mt-6">
      <div class="text-sm text-gray-400">
        显示第 {{ (currentPage - 1) * pageSize + 1 }} -
        {{ Math.min(currentPage * pageSize, totalUsers) }} 条，共 {{ totalUsers }} 条
      </div>
      <div class="flex items-center gap-2">
        <button
          @click="currentPage = Math.max(1, currentPage - 1)"
          :disabled="currentPage === 1"
          class="px-3 py-1 bg-gray-700 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-600 transition-colors"
        >
          上一页
        </button>
        <span class="px-3 py-1 bg-blue-600 text-white rounded">{{ currentPage }}</span>
        <button
          @click="currentPage = Math.min(totalPages, currentPage + 1)"
          :disabled="currentPage === totalPages"
          class="px-3 py-1 bg-gray-700 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-600 transition-colors"
        >
          下一页
        </button>
      </div>
    </div>

    <!-- 用户编辑模态框 -->
    <UserEditModal
      :is-visible="showEditModal"
      :user="editingUser"
      :is-editing="!isCreatingUser"
      :is-creating="isCreatingUser"
      @close="closeEditModal"
      @save="saveUserEdit"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import * as userManagementApi from '../../api/services/userManagementApi.js'
import UserEditModal from '../../components/admin/UserEditModal.vue'

// 响应式数据
const users = ref([])
const loading = ref(false)
const error = ref('')

// 搜索和筛选
const searchQuery = ref('')
const selectedUserType = ref('')
const selectedStatus = ref('')

// 分页相关
const currentPage = ref(1)
const pageSize = ref(20)

// 多选模式状态
const multiSelectMode = ref(false)
const selectedUsers = ref(new Set())
const showMultiSelectDropdown = ref(false)

// 编辑模态框相关
const showEditModal = ref(false)
const editingUser = ref(null)
const isCreatingUser = ref(false)

// 计算属性
const filteredUsers = computed(() => {
  let filtered = users.value

  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(
      (user) =>
        user.username?.toLowerCase().includes(query) ||
        user.email?.toLowerCase().includes(query) ||
        user.steam_id?.toLowerCase().includes(query),
    )
  }

  // 用户类型过滤
  if (selectedUserType.value) {
    filtered = filtered.filter((user) => user.user_type === selectedUserType.value)
  }

  // 状态过滤
  if (selectedStatus.value) {
    const isActive = selectedStatus.value === 'active'
    filtered = filtered.filter((user) => {
      const userActive = user.is_active === 1 || user.is_active === true
      return userActive === isActive
    })
  }

  return filtered
})

const totalUsers = computed(() => filteredUsers.value.length)
const totalPages = computed(() => Math.ceil(totalUsers.value / pageSize.value))

const paginatedUsers = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredUsers.value.slice(start, end)
})

// 多选相关计算属性
const isAllSelected = computed(() => {
  if (paginatedUsers.value.length === 0) return false
  return paginatedUsers.value.every((user) => selectedUsers.value.has(user.user_id || user.id))
})

const isIndeterminate = computed(() => {
  const selectedCount = paginatedUsers.value.filter((user) =>
    selectedUsers.value.has(user.user_id || user.id),
  ).length
  return selectedCount > 0 && selectedCount < paginatedUsers.value.length
})

// 方法
const loadUsers = async () => {
  try {
    loading.value = true
    error.value = ''
    const response = await userManagementApi.getUserList({
      page: 1,
      limit: 100,
    })

    if (response.success) {
      // 解析嵌套的数据结构
      const userData = response.data?.data?.users || response.data?.users || response.data || []
      users.value = Array.isArray(userData) ? userData : []
      console.log('用户数据加载成功:', users.value.length, '个用户')
      console.log('用户数据结构:', response.data)
    } else {
      throw new Error(response.message || '获取用户列表失败')
    }
  } catch (err) {
    console.error('加载用户失败:', err)
    error.value = err.message || '加载用户数据失败'
    users.value = []
  } finally {
    loading.value = false
  }
}

// 多选相关方法
const toggleMultiSelectMode = () => {
  multiSelectMode.value = !multiSelectMode.value
  if (!multiSelectMode.value) {
    selectedUsers.value.clear()
  }
  showMultiSelectDropdown.value = false
}

const toggleUserSelection = (userId) => {
  if (selectedUsers.value.has(userId)) {
    selectedUsers.value.delete(userId)
  } else {
    selectedUsers.value.add(userId)
  }
}

const toggleSelectAll = () => {
  if (isAllSelected.value) {
    // 取消选择当前页所有用户
    paginatedUsers.value.forEach((user) => {
      selectedUsers.value.delete(user.user_id || user.id)
    })
  } else {
    // 选择当前页所有用户
    paginatedUsers.value.forEach((user) => {
      selectedUsers.value.add(user.user_id || user.id)
    })
  }
}

// 批量操作方法
const batchActivate = async () => {
  if (selectedUsers.value.size === 0) return

  try {
    const userIds = Array.from(selectedUsers.value)
    for (const userId of userIds) {
      await userManagementApi.updateUser(userId, { is_active: 1 })
    }
    await loadUsers()
    selectedUsers.value.clear()
    showMultiSelectDropdown.value = false
    console.log('批量激活成功')
  } catch (err) {
    console.error('批量激活失败:', err)
    error.value = '批量激活失败: ' + err.message
  }
}

const batchDeactivate = async () => {
  if (selectedUsers.value.size === 0) return

  try {
    const userIds = Array.from(selectedUsers.value)
    for (const userId of userIds) {
      await userManagementApi.updateUser(userId, { is_active: 0 })
    }
    await loadUsers()
    selectedUsers.value.clear()
    showMultiSelectDropdown.value = false
    console.log('批量停用成功')
  } catch (err) {
    console.error('批量停用失败:', err)
    error.value = '批量停用失败: ' + err.message
  }
}

const batchDelete = async () => {
  if (selectedUsers.value.size === 0) return

  if (!confirm(`确定要删除选中的 ${selectedUsers.value.size} 个用户吗？此操作不可撤销！`)) {
    return
  }

  try {
    const userIds = Array.from(selectedUsers.value)
    for (const userId of userIds) {
      await userManagementApi.deleteUser(userId)
    }
    await loadUsers()
    selectedUsers.value.clear()
    showMultiSelectDropdown.value = false
    console.log('批量删除成功')
  } catch (err) {
    console.error('批量删除失败:', err)
    error.value = '批量删除失败: ' + err.message
  }
}

// 编辑用户
const editUser = async (user) => {
  try {
    // 获取用户资产信息
    const assetsResponse = await userManagementApi.getUserAssets(user.id)
    console.log('[DEBUG] 资产API响应:', assetsResponse)

    // 合并用户基本信息和资产信息
    const assetsData = assetsResponse.success
      ? assetsResponse.data?.data || assetsResponse.data
      : {}
    console.log('[DEBUG] 提取的资产数据:', assetsData)

    const userWithAssets = {
      ...user,
      game_coins: assetsData?.game_coins || 0,
      shop_coins: assetsData?.shop_coins || 0,
      points: assetsData?.points || 0,
      vip_level: assetsData?.vip_level || 0,
    }

    editingUser.value = userWithAssets
    showEditModal.value = true
    console.log('[DEBUG] 编辑用户数据:', userWithAssets)
  } catch (err) {
    console.error('获取用户资产失败:', err)
    // 即使获取资产失败，也显示编辑模态框，只是资产信息为0
    editingUser.value = {
      ...user,
      game_coins: 0,
      shop_coins: 0,
      points: 0,
      vip_level: 0,
    }
    showEditModal.value = true
  }
}

// 创建用户
const createUser = () => {
  isCreatingUser.value = true
  editingUser.value = {
    username: '',
    email: '',
    steam_id: '',
    password: '',
    user_type: 'user',
    is_active: true,
    shop_coins: 0,
    points: 0,
    game_coins: 0,
    vip_level: 0,
  }
  showEditModal.value = true
}

// 关闭编辑模态框
const closeEditModal = () => {
  showEditModal.value = false
  editingUser.value = null
  isCreatingUser.value = false
}

// 保存用户编辑
const saveUserEdit = async (updateData) => {
  try {
    console.log('[DEBUG] 开始保存用户:', updateData, '创建模式:', isCreatingUser.value)

    // 分离基本信息和资产信息
    const { shop_coins, points, ...basicData } = updateData

    let response
    let userId

    if (isCreatingUser.value) {
      // 创建用户模式
      response = await userManagementApi.createUser(basicData)
      console.log('[DEBUG] 创建用户响应:', response)
      console.log('[DEBUG] 响应数据结构:', response.data)
      // 处理嵌套的响应结构
      const userData = response.data?.data?.data || response.data?.data || response.data
      userId = userData?.id || userData?.user_id
      console.log('[DEBUG] 提取的用户数据:', userData)
      console.log('[DEBUG] 提取的userId:', userId)
    } else {
      // 编辑用户模式
      userId = editingUser.value.user_id || editingUser.value.id
      response = await userManagementApi.updateUser(userId, basicData)
      console.log('[DEBUG] 更新用户响应:', response)
    }

    console.log('[DEBUG] 检查条件:', {
      success: response.success,
      userId,
      responseData: response.data,
    })

    if (response.success && userId) {
      // 处理资产更新（创建模式或编辑模式都需要）
      if (shop_coins !== undefined) {
        const shouldUpdate =
          isCreatingUser.value || shop_coins !== (editingUser.value.shop_coins || 0)
        if (shouldUpdate) {
          try {
            const assetsData = {
              asset_type: 'shop_coins',
              amount: shop_coins,
              operation: 'set',
            }
            await userManagementApi.updateUserAssets(userId, assetsData)
            console.log('商城币更新成功:', shop_coins)
          } catch (assetsErr) {
            console.error('更新商城币失败:', assetsErr)
            // 不阻止整个更新流程，只记录错误
          }
        }
      }

      // 如果有积分更新，单独处理
      if (points !== undefined) {
        const shouldUpdate = isCreatingUser.value || points !== (editingUser.value.points || 0)
        if (shouldUpdate) {
          try {
            const assetsData = {
              asset_type: 'points',
              amount: points,
              operation: 'set',
            }
            await userManagementApi.updateUserAssets(userId, assetsData)
            console.log('积分更新成功:', points)
          } catch (assetsErr) {
            console.error('更新积分失败:', assetsErr)
            // 不阻止整个更新流程，只记录错误
          }
        }
      }

      // 重新加载用户数据
      await loadUsers()
      closeEditModal()
      console.log(isCreatingUser.value ? '用户创建成功' : '用户更新成功')
    } else {
      // 提供更详细的错误信息
      const errorMsg = response.message || (isCreatingUser.value ? '创建用户失败' : '更新用户失败')
      console.error('API响应失败:', response)
      throw new Error(errorMsg)
    }
  } catch (err) {
    console.error('保存用户编辑失败:', err)

    // 根据错误类型提供更友好的错误信息
    let userFriendlyMessage = err.message

    if (err.message.includes('Steam ID已被其他用户使用')) {
      userFriendlyMessage = '❌ Steam ID冲突：该Steam ID已被其他用户使用，请使用不同的Steam ID'
    } else if (err.message.includes('用户名已被使用')) {
      userFriendlyMessage = '❌ 用户名冲突：该用户名已被使用，请使用不同的用户名'
    } else if (err.message.includes('邮箱已被使用')) {
      userFriendlyMessage = '❌ 邮箱冲突：该邮箱已被使用，请使用不同的邮箱'
    } else if (err.message.includes('Steam ID格式不正确')) {
      userFriendlyMessage = '❌ 格式错误：' + err.message
    } else if (err.message.includes('数据验证失败')) {
      userFriendlyMessage = '❌ 验证失败：' + err.message
    } else if (err.message.includes('网络')) {
      userFriendlyMessage = '❌ 网络错误：请检查网络连接后重试'
    } else {
      userFriendlyMessage = '❌ 保存失败：' + err.message
    }

    error.value = userFriendlyMessage
  }
}

// 删除用户
const deleteUser = async (user) => {
  if (!confirm(`确定要删除用户 "${user.username}" 吗？此操作不可撤销！`)) {
    return
  }

  try {
    const userId = user.user_id || user.id
    const response = await userManagementApi.deleteUser(userId)

    if (response.success) {
      await loadUsers()
      console.log('用户删除成功')
    } else {
      throw new Error(response.message || '删除用户失败')
    }
  } catch (err) {
    console.error('删除用户失败:', err)
    error.value = '删除失败: ' + err.message
  }
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return 'N/A'
  }
}

// 监听搜索和筛选变化，重置到第一页
watch([searchQuery, selectedUserType, selectedStatus], () => {
  currentPage.value = 1
})

// 组件挂载时加载数据
onMounted(() => {
  loadUsers()
})
</script>
