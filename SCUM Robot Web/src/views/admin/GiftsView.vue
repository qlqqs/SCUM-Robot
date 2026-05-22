<template>
  <div>
    <div
      class="flex flex-col xl:flex-row xl:flex-wrap xl:justify-between xl:items-start mb-6 gap-4"
    >
      <div class="flex-shrink-0">
        <h2 class="text-lg sm:text-xl lg:text-2xl font-bold">礼包管理</h2>
        <p class="text-xs sm:text-sm text-gray-400 mt-1 break-words">
          当前礼包数量: {{ totalGifts }} | 显示: {{ paginatedGifts.length }} | 加载状态:
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
              placeholder="搜索礼包..."
              class="bg-gray-700 border border-gray-600 rounded-md py-2 pl-8 pr-3 focus:outline-none focus:ring-2 focus:ring-blue-500 w-full sm:w-38 text-sm"
            />
            <i
              class="fas fa-search absolute left-2 top-1/2 transform -translate-y-1/2 text-gray-400 text-sm"
            ></i>
          </div>

          <!-- 礼包类型筛选 -->
          <select
            v-model="selectedGiftType"
            @change="handleTypeFilter"
            class="w-full sm:w-auto sm:min-w-[120px] sm:max-w-[200px] bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">全部类型</option>
            <option value="one_time">一次性礼包</option>
            <option value="daily">每日礼包</option>
            <option value="limited_quantity">限量礼包</option>
            <option value="limited_time">限时礼包</option>
            <option value="limited_time_quantity">限时限量礼包</option>
          </select>

          <!-- 状态筛选 -->
          <select
            v-model="selectedStatus"
            @change="handleStatusFilter"
            class="w-full sm:w-auto sm:min-w-[100px] bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">全部状态</option>
            <option value="active">启用</option>
            <option value="inactive">禁用</option>
          </select>
        </div>

        <!-- 按钮盒子 -->
        <div
          class="flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center gap-2 sm:gap-3 sm:min-w-[260px]"
        >
          <!-- 刷新按钮 -->
          <button
            @click="refreshData"
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
              ref="dropdownButton"
              @click="toggleDropdown"
              class="w-full sm:w-auto sm:min-w-[90px] bg-purple-700 hover:bg-purple-800 text-white px-3 py-2 rounded transition-colors flex items-center text-sm font-medium"
            >
              <i class="fas fa-check mr-1"></i>
              <span>操作</span>
              <i
                class="fas fa-chevron-down ml-1 text-xs"
                :class="{ 'rotate-180': showMultiSelectDropdown }"
              ></i>
            </button>

            <!-- 下拉菜单 - 改回相对定位 -->
            <div
              v-if="showMultiSelectDropdown"
              class="absolute right-0 top-full mt-1 min-w-[200px] bg-gray-700 border border-gray-600 rounded-md shadow-lg z-[9999]"
            >
              <button
                @click="batchToggleStatus(true)"
                :disabled="selectedGifts.size === 0"
                class="w-full text-left px-4 py-2 text-sm text-white hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                <i class="fas fa-eye mr-2 text-green-400"></i>
                批量激活 ({{ selectedGifts.size }})
              </button>
              <button
                @click="batchToggleStatus(false)"
                :disabled="selectedGifts.size === 0"
                class="w-full text-left px-4 py-2 text-sm text-white hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                <i class="fas fa-eye-slash mr-2 text-yellow-400"></i>
                批量停用 ({{ selectedGifts.size }})
              </button>
              <button
                @click="batchDelete"
                :disabled="selectedGifts.size === 0"
                class="w-full text-left px-4 py-2 text-sm text-white hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                <i class="fas fa-trash mr-2 text-red-400"></i>
                批量删除 ({{ selectedGifts.size }})
              </button>
              <hr class="border-gray-600 my-1" />
              <button
                @click="toggleMultiSelectMode"
                class="w-full text-left px-4 py-2 text-sm text-white hover:bg-gray-600 flex items-center"
              >
                <i class="fas fa-times mr-2 text-gray-400"></i>
                退出多选
              </button>
            </div>

            <!-- 点击外部关闭下拉菜单 -->
            <div
              v-if="showMultiSelectDropdown"
              @click="showMultiSelectDropdown = false"
              class="fixed inset-0 z-40"
            ></div>
          </div>

          <!-- 创建礼包按钮 -->
          <button
            @click="showCreateModal = true"
            class="w-full sm:w-auto sm:min-w-[90px] bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded transition-colors text-sm font-medium"
          >
            <i class="fas fa-plus mr-1"></i>
            <span>创建礼包</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="errorMessage" class="mb-6 p-4 bg-red-900/50 border border-red-500 rounded-lg">
      <div class="flex items-center justify-between">
        <div class="flex items-center">
          <i class="fas fa-exclamation-triangle text-red-400 mr-2"></i>
          <span class="text-red-200">{{ errorMessage }}</span>
        </div>
        <button @click="errorMessage = ''" class="text-red-400 hover:text-red-300">
          <i class="fas fa-times"></i>
        </button>
      </div>
    </div>

    <!-- 成功提示 -->
    <div v-if="successMessage" class="mb-6 p-4 bg-green-900/50 border border-green-500 rounded-lg">
      <div class="flex items-center justify-between">
        <div class="flex items-center">
          <i class="fas fa-check-circle text-green-400 mr-2"></i>
          <span class="text-green-200">{{ successMessage }}</span>
        </div>
        <button @click="successMessage = ''" class="text-green-400 hover:text-green-300">
          <i class="fas fa-times"></i>
        </button>
      </div>
    </div>

    <div class="bg-transparent p-6 rounded-lg">
      <!-- 加载状态 -->
      <div v-if="loading && paginatedGifts.length === 0" class="text-center py-8">
        <i class="fas fa-spinner fa-spin text-2xl text-gray-400 mb-2"></i>
        <p class="text-gray-400">加载礼包数据中...</p>
      </div>

      <!-- 空状态 -->
      <div v-else-if="!loading && paginatedGifts.length === 0" class="text-center py-8">
        <i class="fas fa-gift text-4xl text-gray-500 mb-4"></i>
        <p class="text-gray-400 mb-4">暂无礼包数据</p>
        <p class="text-sm text-gray-500">点击上方"创建礼包"按钮创建第一个礼包</p>
      </div>

      <!-- 数据表格 -->
      <div v-else class="overflow-x-auto" style="min-width: 0">
        <table class="w-full text-left" style="min-width: 1200px">
          <thead>
            <tr class="border-b border-gray-700">
              <th class="p-2 min-w-[50px] w-[50px] text-center">
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
              <th class="p-2 min-w-[70px] w-[70px] text-center">图片</th>
              <th class="p-2 min-w-[120px] w-[140px] text-center">礼包名称</th>
              <th class="p-2 min-w-[100px] w-[110px] text-center">类型</th>
              <th class="p-2 min-w-[180px] w-[200px] text-center">物品配置</th>
              <th class="p-2 min-w-[70px] w-[80px] text-center">状态</th>
              <th class="p-2 min-w-[90px] w-[100px] text-center">数量信息</th>
              <th class="p-2 min-w-[100px] w-[120px] text-center">时间限制</th>
              <th class="p-2 min-w-[100px] w-[120px] text-center">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(gift, index) in paginatedGifts"
              :key="gift.id"
              class="border-b border-gray-700 hover:bg-gray-700/50"
            >
              <td class="p-2 text-center">
                <!-- 多选模式下显示复选框 -->
                <div v-if="multiSelectMode" class="flex items-center justify-center">
                  <input
                    type="checkbox"
                    :checked="selectedGifts.has(gift.id)"
                    @change="toggleGiftSelection(gift.id)"
                    class="w-4 h-4 text-purple-600 bg-gray-700 border-gray-600 rounded focus:ring-purple-500 focus:ring-2"
                  />
                </div>
                <!-- 普通模式下显示排序序号 -->
                <span
                  v-else
                  :class="{ 'opacity-50': !gift.is_active }"
                  class="text-sm font-medium text-gray-400"
                >
                  {{ (currentPage - 1) * pageSize + index + 1 }}
                </span>
              </td>
              <!-- 图片列 -->
              <td class="p-2 text-center">
                <div
                  class="w-12 h-12 rounded-lg overflow-hidden bg-gray-600 flex items-center justify-center mx-auto"
                >
                  <img
                    :src="getThumbnailUrl(gift.image_url)"
                    :alt="gift.name"
                    class="w-full h-full object-cover"
                    :class="{ 'opacity-50': gift.is_active === false }"
                    @error="handleImageError"
                  />
                </div>
              </td>
              <!-- 礼包名称列 -->
              <td class="p-2 text-center">
                <div :class="{ 'opacity-50': !gift.is_active }" class="min-w-0">
                  <div class="font-medium truncate text-base">{{ gift.name }}</div>
                  <div class="text-sm text-gray-400 mt-1 truncate">
                    {{ gift.description || '无描述' }}
                  </div>
                </div>
              </td>
              <td class="p-2 text-center">
                <span
                  class="px-2 py-1 rounded-full text-sm font-medium inline-block"
                  :class="[getGiftTypeClass(gift.gift_type), { 'opacity-50': !gift.is_active }]"
                >
                  {{ getGiftTypeDisplay(gift.gift_type) }}
                </span>
              </td>
              <td class="p-2 text-center">
                <textarea
                  :value="formatItemsConfigForDisplay(gift.items_config)"
                  readonly
                  class="w-full h-12 p-1 text-sm bg-gray-800 border border-gray-600 rounded resize-none text-center"
                  :class="{ 'opacity-50': !gift.is_active }"
                ></textarea>
              </td>
              <td class="p-2 text-center">
                <span
                  class="px-2 py-1 rounded-full text-sm font-medium inline-block"
                  :class="
                    gift.is_active
                      ? 'bg-green-900/50 text-green-400 border border-green-500/50'
                      : 'bg-red-900/50 text-red-400 border border-red-500/50'
                  "
                >
                  {{ gift.is_active ? '启用' : '禁用' }}
                </span>
              </td>
              <td class="p-2 text-center">
                <div class="text-sm" :class="{ 'opacity-50': !gift.is_active }">
                  <div v-if="gift.total_quantity">
                    剩余: {{ gift.remaining_quantity || 0 }}/{{ gift.total_quantity }}
                  </div>
                  <div v-else>无限制</div>
                  <div class="text-sm text-gray-400">已领取: {{ gift.claimed_quantity || 0 }}</div>
                </div>
              </td>
              <td class="p-2 text-center">
                <div class="text-sm" :class="{ 'opacity-50': !gift.is_active }">
                  <div v-if="gift.start_time && gift.end_time">
                    <div class="text-sm text-gray-400">
                      {{ formatDateTime(gift.start_time) }}
                    </div>
                    <div class="text-sm text-gray-400">至 {{ formatDateTime(gift.end_time) }}</div>
                  </div>
                  <div v-else class="text-sm text-gray-400">无时间限制</div>
                </div>
              </td>
              <td class="p-2 text-center">
                <button
                  @click="editGift(gift)"
                  :disabled="gift.updating || gift.is_active === false"
                  class="text-blue-400 hover:text-blue-300 mr-2 disabled:opacity-50"
                  title="编辑"
                >
                  <i class="fas fa-edit text-base"></i>
                </button>
                <button
                  @click="toggleGiftStatus(gift)"
                  :disabled="gift.updating"
                  class="text-yellow-400 hover:text-yellow-300 mr-2 disabled:opacity-50"
                  :title="gift.is_active ? '禁用' : '启用'"
                >
                  <i
                    :class="gift.is_active ? 'fas fa-pause text-base' : 'fas fa-play text-base'"
                  ></i>
                </button>
                <button
                  @click="deleteGift(gift.id)"
                  :disabled="gift.updating"
                  class="text-red-500 hover:text-red-400 disabled:opacity-50"
                  title="删除"
                >
                  <i class="fas fa-trash text-base"></i>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 分页控件 -->
      <div v-if="totalPages > 1" class="flex justify-between items-center mt-6">
        <div class="text-sm text-gray-400">
          显示第 {{ (currentPage - 1) * pageSize + 1 }} -
          {{ Math.min(currentPage * pageSize, totalGifts) }} 条，共 {{ totalGifts }} 条
        </div>
        <div class="flex items-center gap-2">
          <button
            @click="previousPage"
            :disabled="currentPage === 1"
            class="px-3 py-1 bg-gray-700 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-600"
          >
            上一页
          </button>
          <span class="text-sm text-gray-400"> 第 {{ currentPage }} / {{ totalPages }} 页 </span>
          <button
            @click="nextPage"
            :disabled="currentPage === totalPages"
            class="px-3 py-1 bg-gray-700 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-600"
          >
            下一页
          </button>
        </div>
      </div>
    </div>

    <!-- 创建/编辑礼包模态框 -->
    <GiftModal
      :show="showCreateModal || showEditModal"
      :gift="editingGift"
      :is-editing="!!showEditModal"
      @close="closeModal"
      @save="handleSaveGift"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { giftsApi } from '../../api/services/giftsApi.js'
import { API_CONFIG } from '../../api/config.js'
import GiftModal from '../../components/admin/GiftModal.vue'

// 响应式数据
const gifts = ref([])
const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

// 筛选和分页
const selectedGiftType = ref('')
const selectedStatus = ref('')
const currentPage = ref(1)
const pageSize = ref(10)

// 模态框状态
const showCreateModal = ref(false)
const showEditModal = ref(false)
const editingGift = ref(null)

// 多选模式状态
const multiSelectMode = ref(false)
const selectedGifts = ref(new Set())
const showMultiSelectDropdown = ref(false)

// 搜索功能
const searchQuery = ref('')

// 下拉菜单按钮引用
const dropdownButton = ref(null)

// 计算属性
const filteredGifts = computed(() => {
  // 确保 gifts.value 是数组
  if (!Array.isArray(gifts.value)) {
    console.warn('gifts.value 不是数组:', gifts.value)
    return []
  }

  let filtered = gifts.value

  // 搜索筛选
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(
      (gift) =>
        gift.name.toLowerCase().includes(query) ||
        (gift.description && gift.description.toLowerCase().includes(query)),
    )
  }

  // 类型筛选
  if (selectedGiftType.value) {
    filtered = filtered.filter((gift) => gift.gift_type === selectedGiftType.value)
  }

  // 状态筛选
  if (selectedStatus.value) {
    const isActive = selectedStatus.value === 'active'
    filtered = filtered.filter((gift) => gift.is_active === isActive)
  }

  return filtered
})

// 多选相关计算属性
const isAllSelected = computed(() => {
  return (
    paginatedGifts.value.length > 0 &&
    paginatedGifts.value.every((gift) => selectedGifts.value.has(gift.id))
  )
})

const isIndeterminate = computed(() => {
  const selectedCount = paginatedGifts.value.filter((gift) =>
    selectedGifts.value.has(gift.id),
  ).length
  return selectedCount > 0 && selectedCount < paginatedGifts.value.length
})

const totalGifts = computed(() => filteredGifts.value.length)
const totalPages = computed(() => Math.ceil(totalGifts.value / pageSize.value))

const paginatedGifts = computed(() => {
  // 确保 filteredGifts.value 是数组
  if (!Array.isArray(filteredGifts.value)) {
    console.warn('filteredGifts.value 不是数组:', filteredGifts.value)
    return []
  }

  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredGifts.value.slice(start, end)
})

// 加载礼包数据
const loadGifts = async () => {
  try {
    loading.value = true
    errorMessage.value = ''

    const response = await giftsApi.getAllGifts()
    if (response.success) {
      gifts.value = response.data.gifts || []
    } else {
      errorMessage.value = response.message || '加载礼包失败'
    }
  } catch (error) {
    console.error('加载礼包失败:', error)
    errorMessage.value = error.message || '加载礼包失败'
  } finally {
    loading.value = false
  }
}

const refreshData = async () => {
  currentPage.value = 1
  await loadGifts()

  // 只有在成功加载数据且没有错误时才显示刷新成功提示
  if (!errorMessage.value) {
    successMessage.value = '数据刷新成功'

    // 自动清除成功消息
    setTimeout(() => {
      successMessage.value = ''
    }, 2000)
  }
}

const handleTypeFilter = () => {
  currentPage.value = 1
}

const handleStatusFilter = () => {
  currentPage.value = 1
}

const previousPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
  }
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
  }
}

const getGiftTypeClass = (giftType) => {
  const typeClasses = {
    one_time: 'bg-blue-900/50 text-blue-400 border border-blue-500/50',
    daily: 'bg-green-900/50 text-green-400 border border-green-500/50',
    limited_quantity: 'bg-orange-900/50 text-orange-400 border border-orange-500/50',
    limited_time: 'bg-purple-900/50 text-purple-400 border border-purple-500/50',
    limited_time_quantity: 'bg-red-900/50 text-red-400 border border-red-500/50',
  }
  return typeClasses[giftType] || 'bg-gray-900/50 text-gray-400 border border-gray-500/50'
}

const getGiftTypeDisplay = (giftType) => {
  return giftsApi.getGiftTypeDisplay(giftType)
}

const formatItemsConfigForDisplay = (itemsConfig) => {
  if (!itemsConfig) return ''

  let itemCodeLines = []

  if (itemsConfig.items && Array.isArray(itemsConfig.items)) {
    // 新格式：{ items: [...] } - 数组格式
    itemCodeLines = itemsConfig.items
      .map((item) => {
        // 检查item字段是否已经包含完整命令
        if (item.item && item.item.startsWith('#')) {
          // 如果item字段包含完整命令，直接返回
          return item.item
        } else if (item.command && item.command.startsWith('#')) {
          // 如果有command字段，构建完整命令
          return item.amount > 1
            ? `${item.command} ${item.item} ${item.amount}`
            : `${item.command} ${item.item} 1`
        } else {
          // 没有命令，只显示物品名称
          return item.amount > 1 ? `${item.item} ${item.amount}` : item.item
        }
      })
      .filter((line) => line)
  } else if (Array.isArray(itemsConfig)) {
    // 数组格式：[...]
    itemCodeLines = itemsConfig
      .map((item) => {
        // 检查item字段是否已经包含完整命令
        if (item.item && item.item.startsWith('#')) {
          // 如果item字段包含完整命令，直接返回
          return item.item
        } else if (item.command && item.command.startsWith('#')) {
          // 如果有command字段，构建完整命令
          return item.amount > 1
            ? `${item.command} ${item.item} ${item.amount}`
            : `${item.command} ${item.item} 1`
        } else {
          // 没有命令，只显示物品名称
          return item.amount > 1 ? `${item.item} ${item.amount}` : item.item
        }
      })
      .filter((line) => line)
  } else if (typeof itemsConfig === 'object') {
    // 字典格式：{"item_name": quantity} - 显示为单独的物品代码
    itemCodeLines = Object.entries(itemsConfig).map(([itemName, quantity]) => {
      return quantity > 1 ? `${itemName} ${quantity}` : itemName
    })
  }

  return itemCodeLines.join('\n')
}

const formatDateTime = (dateTimeString) => {
  if (!dateTimeString) return ''
  try {
    const date = new Date(dateTimeString)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return dateTimeString
  }
}

const editGift = async (gift) => {
  try {
    loading.value = true
    errorMessage.value = ''

    // 获取礼包详细配置
    const response = await giftsApi.getGift(gift.id)

    if (response.success) {
      editingGift.value = response.data
      showEditModal.value = true
    } else {
      errorMessage.value = response.message || '获取礼包详情失败'
    }
  } catch (error) {
    console.error('获取礼包详情失败:', error)
    errorMessage.value = error.message || '获取礼包详情失败'
  } finally {
    loading.value = false
  }
}

const closeModal = () => {
  showCreateModal.value = false
  showEditModal.value = false
  editingGift.value = null
}

const handleSaveGift = async (giftData, imageFile) => {
  try {
    let giftId

    if (showEditModal.value) {
      // 更新礼包
      await giftsApi.updateGift(editingGift.value.id, giftData)
      giftId = editingGift.value.id
      successMessage.value = '礼包更新成功'
    } else {
      // 创建礼包
      const response = await giftsApi.createGift(giftData)
      giftId = response.data.gift_id || response.data.id
      successMessage.value = '礼包创建成功'
    }

    // 如果有图片需要上传
    if (imageFile && giftId) {
      try {
        const uploadResponse = await giftsApi.uploadGiftImage(giftId, imageFile)
        if (uploadResponse.success) {
          // 更新礼包的图片URL
          await giftsApi.updateGift(giftId, { image_url: uploadResponse.data.image_url })
          successMessage.value += '，图片上传成功'
        }
      } catch (uploadError) {
        console.error('图片上传失败:', uploadError)
        successMessage.value += '，但图片上传失败'
      }
    }

    closeModal()
    await loadGifts()

    // 自动清除成功消息
    setTimeout(() => {
      successMessage.value = ''
    }, 3000)
  } catch (error) {
    console.error('保存礼包失败:', error)
    errorMessage.value = error.message || '保存礼包失败'
  }
}

const toggleGiftStatus = async (gift) => {
  try {
    gift.updating = true
    const updateData = { is_active: !gift.is_active }
    await giftsApi.updateGift(gift.id, updateData)

    // 更新本地数据
    gift.is_active = !gift.is_active
    successMessage.value = `礼包已${gift.is_active ? '启用' : '禁用'}`

    // 自动清除成功消息
    setTimeout(() => {
      successMessage.value = ''
    }, 2000)
  } catch (error) {
    console.error('更新礼包状态失败:', error)
    errorMessage.value = error.message || '更新礼包状态失败'
  } finally {
    gift.updating = false
  }
}

const deleteGift = async (giftId) => {
  if (!confirm('确定要删除这个礼包吗？此操作不可撤销。')) {
    return
  }

  try {
    await giftsApi.deleteGift(giftId)
    successMessage.value = '礼包删除成功'
    await loadGifts()

    // 自动清除成功消息
    setTimeout(() => {
      successMessage.value = ''
    }, 3000)
  } catch (error) {
    console.error('删除礼包失败:', error)
    errorMessage.value = error.message || '删除礼包失败'
  }
}

// 图片处理函数
const handleImageError = (event) => {
  const currentSrc = event.target.src

  // 如果当前是新格式缩略图且加载失败，尝试加载原图
  if (currentSrc.includes('/thumbs/') && currentSrc.includes('-thumb.')) {
    // 将 /static/images/gifts/thumbs/filename-thumb.ext 转换为 /static/images/gifts/imgs/filename.ext
    const originalUrl = currentSrc.replace('/thumbs/', '/imgs/').replace('-thumb.', '.')
    event.target.src = originalUrl
    return
  }

  // 兼容旧格式缩略图
  if (currentSrc.includes('_thumb.')) {
    const originalUrl = currentSrc.replace('/thumbs/', '/imgs/').replace('_thumb.', '.')
    event.target.src = originalUrl
    return
  }

  // 如果原图也加载失败，显示占位图
  event.target.src = 'https://placehold.co/100x100/cccccc/666666?text=No+Image'
}

// 获取缩略图URL
const getThumbnailUrl = (imageUrl) => {
  if (!imageUrl) {
    return 'https://placehold.co/100x100/cccccc/666666?text=No+Image'
  }

  // 确保URL包含完整的后端服务器地址
  const getFullUrl = (url) => {
    if (url.startsWith('http://') || url.startsWith('https://')) {
      return url
    }
    // 使用配置中的后端服务器地址
    return `${API_CONFIG.BASE_URL}${url}`
  }

  // 根据后端实际实现，礼包图片URL格式（与物品API一致）：
  // 原图：/static/images/gifts/imgs/filename.jpg
  // 缩略图：/static/images/gifts/thumbs/filename-thumb.jpg
  if (imageUrl.includes('/static/images/gifts/imgs/')) {
    // 将原图路径转换为缩略图路径
    const filename = imageUrl.split('/').pop() // 获取文件名
    const lastDotIndex = filename.lastIndexOf('.')
    if (lastDotIndex > 0) {
      const nameWithoutExt = filename.substring(0, lastDotIndex)
      const extension = filename.substring(lastDotIndex)
      const thumbnailFilename = `${nameWithoutExt}-thumb${extension}`
      const thumbnailUrl = `/static/images/gifts/thumbs/${thumbnailFilename}`
      return getFullUrl(thumbnailUrl)
    }
  } else if (imageUrl.includes('/static/images/gifts/thumbs/')) {
    // 已经是缩略图路径
    return getFullUrl(imageUrl)
  } else if (imageUrl.includes('/static/images/gifts/')) {
    // 处理非标准路径，如 /static/images/gifts/updated_image.jpg
    const filename = imageUrl.split('/').pop()
    const lastDotIndex = filename.lastIndexOf('.')
    if (lastDotIndex > 0) {
      const nameWithoutExt = filename.substring(0, lastDotIndex)
      const extension = filename.substring(lastDotIndex)
      const thumbnailFilename = `${nameWithoutExt}-thumb${extension}`
      const thumbnailUrl = `/static/images/gifts/thumbs/${thumbnailFilename}`
      return getFullUrl(thumbnailUrl)
    }
  }

  // 对于其他URL或无法生成缩略图的情况，返回原图
  return getFullUrl(imageUrl)
}

// 多选功能方法
const toggleMultiSelectMode = () => {
  multiSelectMode.value = !multiSelectMode.value

  // 退出多选模式时清空选中项和隐藏下拉菜单
  if (!multiSelectMode.value) {
    selectedGifts.value.clear()
    showMultiSelectDropdown.value = false
  }
}

const toggleDropdown = (event) => {
  event.stopPropagation()
  showMultiSelectDropdown.value = !showMultiSelectDropdown.value
}

const toggleSelectAll = () => {
  if (isAllSelected.value) {
    // 取消选择当前页面的所有礼包
    paginatedGifts.value.forEach((gift) => {
      selectedGifts.value.delete(gift.id)
    })
  } else {
    // 选择当前页面的所有礼包
    paginatedGifts.value.forEach((gift) => {
      selectedGifts.value.add(gift.id)
    })
  }
}

const toggleGiftSelection = (giftId) => {
  if (selectedGifts.value.has(giftId)) {
    selectedGifts.value.delete(giftId)
  } else {
    selectedGifts.value.add(giftId)
  }
}

const batchToggleStatus = async (isActive) => {
  if (selectedGifts.value.size === 0) return

  try {
    loading.value = true
    const promises = Array.from(selectedGifts.value).map(async (giftId) => {
      const gift = gifts.value.find((g) => g.id === giftId)
      if (gift) {
        const updateData = { is_active: isActive }
        return await giftsApi.updateGift(giftId, updateData)
      }
    })

    await Promise.all(promises)

    // 刷新数据
    await loadGifts()

    successMessage.value = `成功${isActive ? '激活' : '停用'}了 ${selectedGifts.value.size} 个礼包`
    selectedGifts.value.clear()
    showMultiSelectDropdown.value = false

    setTimeout(() => {
      successMessage.value = ''
    }, 3000)
  } catch (error) {
    console.error('批量操作失败:', error)
    errorMessage.value = error.message || '批量操作失败'
  } finally {
    loading.value = false
  }
}

const batchDelete = async () => {
  if (selectedGifts.value.size === 0) return

  if (!confirm(`确定要删除选中的 ${selectedGifts.value.size} 个礼包吗？此操作不可撤销。`)) {
    return
  }

  try {
    loading.value = true
    const promises = Array.from(selectedGifts.value).map((giftId) => giftsApi.deleteGift(giftId))

    await Promise.all(promises)

    // 刷新数据
    await loadGifts()

    successMessage.value = `成功删除了 ${selectedGifts.value.size} 个礼包`
    selectedGifts.value.clear()
    showMultiSelectDropdown.value = false

    setTimeout(() => {
      successMessage.value = ''
    }, 3000)
  } catch (error) {
    console.error('批量删除失败:', error)
    errorMessage.value = error.message || '批量删除失败'
  } finally {
    loading.value = false
  }
}

// 生命周期
onMounted(() => {
  loadGifts()
})
</script>
