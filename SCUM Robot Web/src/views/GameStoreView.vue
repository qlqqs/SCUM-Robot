<template>
  <div
    data-game-store
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
      <div class="w-4/5 mx-auto bg-gray-800/60 backdrop-blur-md rounded-lg p-4 lg:p-6">
        <!-- Search and Pagination -->
        <div class="flex flex-col sm:flex-row justify-between items-center mb-4 gap-4">
          <div class="relative w-full sm:w-auto">
            <i class="fa fa-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"></i>
            <input
              v-model="searchQuery"
              @input="handleSearchInput"
              type="text"
              placeholder="输入你想搜索的"
              class="bg-gray-900 bg-opacity-50 border border-gray-700 rounded-md py-2 pl-10 pr-4 w-full sm:w-64 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <div v-if="isSearching" class="absolute right-3 top-1/2 -translate-y-1/2">
              <i class="fas fa-spinner fa-spin text-gray-400"></i>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button
              @click="gameStore.refreshData"
              :disabled="isLoading"
              class="px-4 py-2 text-sm bg-green-600 hover:bg-green-700 text-white rounded-md transition-colors disabled:opacity-50"
              title="刷新数据"
            >
              <i class="fas fa-sync-alt mr-1" :class="{ 'animate-spin': isLoading }"></i>
              刷新
            </button>
            <button
              @click="openCart"
              class="px-4 py-2 text-sm bg-orange-600 hover:bg-orange-700 text-white rounded-md transition-colors relative"
              title="购物车"
            >
              <i class="fas fa-shopping-cart mr-1"></i>
              购物车
              <span
                v-if="cartItemCount > 0"
                class="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center"
              >
                {{ cartItemCount > 99 ? '99+' : cartItemCount }}
              </span>
            </button>
            <button
              @click="previousPage"
              :disabled="!hasPreviousPage"
              class="px-4 py-2 text-sm bg-gray-700 hover:bg-gray-600 rounded-md transition-colors disabled:opacity-50"
            >
              上一页
            </button>
            <span class="px-3 py-2 text-sm text-gray-300">
              {{ currentPage }} / {{ totalPages || 1 }}
            </span>
            <button
              @click="nextPage"
              :disabled="!hasNextPage"
              class="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors disabled:opacity-50"
            >
              下一页
            </button>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="isLoading" class="flex justify-center items-center py-12">
          <div class="text-center">
            <i class="fas fa-spinner fa-spin text-4xl text-blue-500 mb-4"></i>
            <p class="text-gray-300">正在加载商品数据...</p>
          </div>
        </div>

        <!-- Error State -->
        <div v-else-if="hasError" class="text-center py-12">
          <div class="bg-red-900/50 border border-red-700 rounded-lg p-6 max-w-md mx-auto">
            <i class="fas fa-exclamation-triangle text-4xl text-red-400 mb-4"></i>
            <h3 class="text-xl font-semibold text-red-300 mb-2">加载失败</h3>
            <p class="text-red-200 mb-4">{{ hasError }}</p>
            <button
              @click="gameStore.initializeData()"
              class="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded transition-colors"
            >
              重试
            </button>
          </div>
        </div>

        <!-- Content -->
        <template v-else>
          <!-- 筛选器 -->
          <div class="mb-6 flex items-center gap-3 w-full sm:w-64">
            <!-- 类目筛选 -->
            <select
              v-model="selectedCategoryId"
              @change="handleCategoryFilter"
              class="bg-gray-900 bg-opacity-50 border border-gray-700 rounded-md py-2 px-3 text-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 flex-1"
            >
              <option value="">全部类目</option>
              <option v-for="category in categories" :key="category.id" :value="category.id">
                {{ category.name }}
              </option>
            </select>

            <!-- 子类目筛选 -->
            <select
              v-model="selectedSubcategoryId"
              @change="handleSubcategoryFilter"
              class="bg-gray-900 bg-opacity-50 border border-gray-700 rounded-md py-2 px-3 text-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex-1"
              :disabled="!selectedCategoryId"
            >
              <option value="">全部子类目</option>
              <option
                v-for="subcategory in filteredSubcategories"
                :key="subcategory.id"
                :value="subcategory.id"
              >
                {{ subcategory.name }}
              </option>
            </select>
          </div>

          <!-- Empty State -->
          <div v-if="filteredItems.length === 0" class="text-center py-12">
            <div class="text-gray-400">
              <i class="fas fa-box-open text-6xl mb-4"></i>
              <h3 class="text-xl font-semibold mb-2">暂无商品</h3>
              <p v-if="searchQuery.trim()">没有找到包含 "{{ searchQuery }}" 的商品</p>
              <p v-else-if="selectedCategoryId || selectedSubcategoryId">当前筛选条件下暂无商品</p>
              <p v-else>商店暂时没有商品</p>
            </div>
          </div>

          <!-- Item Grid -->
          <div v-else class="item-grid-container">
            <ItemGrid :items="filteredItems" @add-to-cart="addToCart" />
          </div>
        </template>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useGameStore } from '@/stores/gameStore'
import { useCartStore } from '@/stores/cartStore'
import { useSystemConfigStore } from '@/stores/systemConfigStore'
import { buildApiUrl } from '@/api/config.js'
import { authApi } from '@/api/services/authApi.js'
import { usersApi } from '@/api/services/usersApi.js'
import { vipApi } from '@/api/services/vipApi.js'
import GameHeader from '../components/GameHeader.vue'

import ItemGrid from '../components/ItemGrid.vue'

const gameStore = useGameStore()
const cartStore = useCartStore()
const systemConfigStore = useSystemConfigStore()
const router = useRouter()

// 响应式状态
const searchQuery = ref('')
const selectedCategoryId = ref('')
const selectedSubcategoryId = ref('')
const currentPage = ref(1)
const containerWidth = ref(1200) // 默认容器宽度

// 根据容器宽度获取对应的minmax值和gap（匹配ItemGrid.vue的响应式规则）
const getGridConfig = (width) => {
  // 检查高DPI屏幕（这个规则优先级最高）
  if (window.devicePixelRatio >= 1.5) {
    return { minWidth: 140, gap: 12 } // 0.75rem = 12px
  }

  if (width <= 640) {
    return { minWidth: 120, gap: 12 } // 0.75rem = 12px
  } else if (width <= 768) {
    return { minWidth: 140, gap: 16 } // gap-4 = 16px
  } else if (width <= 1024) {
    return { minWidth: 160, gap: 16 }
  } else if (width <= 1440) {
    return { minWidth: 180, gap: 16 }
  } else {
    return { minWidth: 200, gap: 16 }
  }
}

// 模拟CSS Grid auto-fill的精确算法
const calculateItemsPerRow = (containerWidth, minWidth, gap) => {
  // CSS Grid auto-fill算法：
  // 1. 计算可用空间：containerWidth
  // 2. 每个track的最小空间：minWidth + gap
  // 3. 最后一个track不需要gap：所以总公式是 (containerWidth + gap) / (minWidth + gap)

  const tracksCount = Math.floor((containerWidth + gap) / (minWidth + gap))

  // 但是需要确保至少有1个track
  return Math.max(1, tracksCount)
}

// 动态计算每页商品数量
const pageSize = computed(() => {
  const rowsPerPage = systemConfigStore.storeItemsPerPage || 3 // 每页栏数

  // 获取当前宽度对应的网格配置
  const { minWidth, gap } = getGridConfig(containerWidth.value)

  // 使用精确的CSS Grid算法
  const itemsPerRow = calculateItemsPerRow(containerWidth.value, minWidth, gap)

  const totalItems = rowsPerPage * itemsPerRow

  // 详细调试信息
  console.log(`[GameStoreView] ===== 分页计算调试 =====`)
  console.log(`容器宽度: ${containerWidth.value}px`)
  console.log(`设备像素比: ${window.devicePixelRatio}`)
  console.log(`使用的minWidth: ${minWidth}px`)
  console.log(`使用的gap: ${gap}px`)
  console.log(`计算公式: Math.floor((${containerWidth.value} + ${gap}) / (${minWidth} + ${gap}))`)
  console.log(
    `计算结果: Math.floor(${containerWidth.value + gap} / ${minWidth + gap}) = ${itemsPerRow}`,
  )
  console.log(`每页栏数: ${rowsPerPage}`)
  console.log(`每页总商品数: ${rowsPerPage} × ${itemsPerRow} = ${totalItems}`)
  console.log(`================================`)

  return totalItems
})
const isSearching = ref(false)

// 购物车状态（使用cartStore）
const cartItemCount = computed(() => cartStore.itemCount)

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

// 从store获取数据
const categories = computed(() => gameStore.categories)
const subcategories = computed(() => gameStore.subcategories)

// 根据选中的类目筛选子类目
const filteredSubcategories = computed(() => {
  if (!selectedCategoryId.value) {
    return []
  }
  return subcategories.value.filter((sub) => sub.category_id == selectedCategoryId.value)
})

// 适配API数据结构到组件期望的格式
const items = computed(() => {
  // 确保gameStore.items是数组
  if (!Array.isArray(gameStore.items)) {
    console.warn('[GameStoreView] gameStore.items is not an array:', gameStore.items)
    return []
  }

  return gameStore.items.map((item) => {
    // 严格的价格验证
    let validPrice = null
    if (item.price != null) {
      const numPrice = Number(item.price)
      if (!isNaN(numPrice) && numPrice > 0) {
        validPrice = numPrice
      }
    }

    return {
      ...item,
      // 适配图片字段
      image: item.image_url
        ? buildApiUrl(item.image_url)
        : 'https://placehold.co/150x150/666666/FFFFFF?text=暂无图片',
      // 添加quantity字段，默认为1
      quantity: 1,
      // 严格的价格处理 - 只接受有效的正数价格
      price: validPrice,
      // 标记价格是否有效
      isPriceValid: validPrice !== null,
      // 适配分类字段
      category: item.category_name || '未分类',
    }
  })
})

// 过滤后的物品列表（不分页）
const allFilteredItems = computed(() => {
  let filtered = items.value

  // 过滤掉下架的物品（在商城页面不显示下架物品）
  filtered = filtered.filter((item) => item.is_active !== false)

  // 按类目过滤
  if (selectedCategoryId.value) {
    filtered = filtered.filter((item) => item.category_id == selectedCategoryId.value)
  }

  // 按子类目过滤
  if (selectedSubcategoryId.value) {
    filtered = filtered.filter((item) => item.subcategory_id == selectedSubcategoryId.value)
  }

  // 按搜索关键词过滤
  if (searchQuery.value.trim()) {
    const keyword = searchQuery.value.toLowerCase()
    filtered = filtered.filter((item) => item.name.toLowerCase().includes(keyword))
  }

  return filtered
})

// 分页相关计算属性
const totalItems = computed(() => allFilteredItems.value.length)
const totalPages = computed(() => Math.ceil(totalItems.value / pageSize.value))
const hasNextPage = computed(() => currentPage.value < totalPages.value)
const hasPreviousPage = computed(() => currentPage.value > 1)

// 当前页的物品列表
const filteredItems = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return allFilteredItems.value.slice(start, end)
})

// 加载状态
const isLoading = computed(
  () =>
    gameStore.loading.init ||
    gameStore.loading.items ||
    gameStore.loading.categories ||
    isSearching.value,
)

const hasError = computed(
  () => gameStore.errors.init || gameStore.errors.items || gameStore.errors.categories,
)

// 处理类目筛选
const handleCategoryFilter = async () => {
  // 清空子类目选择
  selectedSubcategoryId.value = ''
  // 重置分页
  resetPagination()

  // 重新加载数据
  if (searchQuery.value.trim()) {
    await performSearch()
  } else {
    await gameStore.loadItems()
  }
}

// 处理子类目筛选
const handleSubcategoryFilter = async () => {
  // 重置分页
  resetPagination()

  // 重新加载数据
  if (searchQuery.value.trim()) {
    await performSearch()
  } else {
    await gameStore.loadItems()
  }
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
    const currentUserResponse = await usersApi.getCurrentUser()

    if (currentUserResponse.success && currentUserResponse.data) {
      // 映射API响应数据到组件数据结构
      // 注意：currentUserResponse.data 是整个API响应，真正的用户数据在 data.data 中
      const apiData = currentUserResponse.data.data || currentUserResponse.data
      console.log('[GameStoreView] 提取的用户数据:', apiData)
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

      console.log('[GameStoreView] 映射后的用户信息:', userInfo.value)
      console.log('[GameStoreView] 映射后的用户统计:', userStats.value)
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
      console.warn('[GameStoreView] 获取VIP状态失败:', vipError)
      // VIP API失败不影响基本功能，继续执行
    }

    // 获取用户统计信息
    try {
      const statsResponse = await usersApi.getUserStats()
      if (statsResponse.success) {
        const apiData = statsResponse.data.data || statsResponse.data
        console.log('[GameStoreView] 提取的用户统计数据:', apiData)
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
        console.log('[GameStoreView] 提取的用户资产数据:', apiData)
        userAssets.value = {
          currency: {
            normal: apiData.game_coins || 0,
            gold: apiData.shop_coins || 0,
          },
          fame_points: apiData.points || 0,
          items: [],
        }
        console.log('[GameStoreView] 映射后的用户资产:', userAssets.value)
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

const previousPage = () => {
  if (hasPreviousPage.value) {
    currentPage.value--
  }
}

const nextPage = () => {
  if (hasNextPage.value) {
    currentPage.value++
  }
}

// 重置分页到第一页
const resetPagination = () => {
  currentPage.value = 1
}

// 购物车相关函数
const addToCart = (item) => {
  try {
    cartStore.addItem(item)
    // 可以添加成功提示
    console.log(`[GameStoreView] 商品"${item.name}"已添加到购物车`)
  } catch (error) {
    console.error('[GameStoreView] 添加商品到购物车失败:', error)
    alert(error.message || '添加商品到购物车失败')
  }
}

const openCart = () => {
  // 跳转到购物车页面
  router.push('/cart')
}

// 执行搜索
const performSearch = async () => {
  if (!searchQuery.value.trim()) {
    // 如果搜索为空，重新加载所有物品
    await gameStore.loadItems()
    return
  }

  isSearching.value = true
  try {
    await gameStore.searchItems(searchQuery.value.trim(), {
      category_id: selectedCategoryId.value || undefined,
      subcategory_id: selectedSubcategoryId.value || undefined,
    })
  } catch (error) {
    console.error('[GameStoreView] Search failed:', error)
  } finally {
    isSearching.value = false
  }
}

// 防抖搜索
let searchTimeout = null
const handleSearchInput = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    resetPagination()
    performSearch()
  }, 500)
}

// 更新容器宽度
const updateContainerWidth = () => {
  console.log(`[GameStoreView] ===== 容器宽度获取调试 =====`)

  // 优先获取ItemGrid的实际宽度
  const itemGrid = document.querySelector('.responsive-grid')
  if (itemGrid) {
    const width = itemGrid.clientWidth
    containerWidth.value = width
    console.log(`[GameStoreView] 找到ItemGrid (.responsive-grid): ${width}px`)
    console.log(`[GameStoreView] ItemGrid offsetWidth: ${itemGrid.offsetWidth}px`)
    console.log(`[GameStoreView] ItemGrid scrollWidth: ${itemGrid.scrollWidth}px`)
    return
  }

  // 其次获取ItemGrid容器的实际宽度
  const itemGridContainer = document.querySelector('.item-grid-container')
  if (itemGridContainer) {
    const width = itemGridContainer.clientWidth
    containerWidth.value = width
    console.log(`[GameStoreView] 找到ItemGrid容器 (.item-grid-container): ${width}px`)
    return
  }

  // 如果ItemGrid容器不存在，获取main容器内的实际内容区域宽度
  const mainContainer = document.querySelector('main .w-4\\/5')
  if (mainContainer) {
    // 获取容器的实际宽度（不包括padding）
    const computedStyle = window.getComputedStyle(mainContainer)
    const paddingLeft = parseFloat(computedStyle.paddingLeft)
    const paddingRight = parseFloat(computedStyle.paddingRight)
    const actualWidth = mainContainer.clientWidth - paddingLeft - paddingRight

    containerWidth.value = actualWidth
    console.log(`[GameStoreView] 找到Main容器，减去padding后: ${actualWidth}px`)
    console.log(`[GameStoreView] Main容器原始宽度: ${mainContainer.clientWidth}px`)
    console.log(`[GameStoreView] Padding: ${paddingLeft}px + ${paddingRight}px`)
  } else {
    // 如果找不到容器，使用默认值
    containerWidth.value = 1200
    console.log(`[GameStoreView] 未找到任何容器，使用默认宽度: 1200px`)
  }

  console.log(`[GameStoreView] 最终容器宽度: ${containerWidth.value}px`)
  console.log(`================================`)
}

// 组件挂载时初始化数据
onMounted(async () => {
  try {
    // 加载系统配置
    await systemConfigStore.loadConfig()

    // 并行加载游戏数据和用户数据
    await Promise.all([gameStore.initializeData(), loadUserData()])
    // 初始化购物车
    cartStore.loadFromStorage()
    cartStore.startAutoSave()

    // 等待DOM渲染完成后再获取容器宽度
    await new Promise((resolve) => setTimeout(resolve, 100))
    updateContainerWidth()

    // 数据加载完成后再次更新容器宽度（确保布局稳定）
    await new Promise((resolve) => setTimeout(resolve, 200))
    updateContainerWidth()

    // 监听窗口大小变化
    window.addEventListener('resize', updateContainerWidth)
  } catch (error) {
    console.error('[GameStoreView] Failed to initialize data:', error)
  }
})

// 组件卸载时清理事件监听器
onUnmounted(() => {
  window.removeEventListener('resize', updateContainerWidth)
})
</script>

<style scoped>
.backdrop-blur-md {
  backdrop-filter: blur(12px);
}

.bg-opacity-80 {
  background-color: rgba(17, 24, 39, 0.8); /* bg-gray-900 with 80% opacity */
}

.bg-opacity-60 {
  background-color: rgba(31, 41, 55, 0.6); /* bg-gray-800 with 60% opacity */
}

.category-btn {
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: rgb(209 213 219);
  background-color: rgba(55, 65, 81, 0.5);
  border-radius: 0.375rem;
  white-space: nowrap;
  transition: background-color 0.2s;
}

.category-btn:hover {
  background-color: rgb(75 85 99);
}

.category-btn.active {
  background-color: rgb(37 99 235);
  color: white;
}

/* Custom scrollbar for better aesthetics */
.custom-scrollbar::-webkit-scrollbar {
  height: 8px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(31, 41, 55, 0.5);
  border-radius: 10px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(75, 85, 99, 0.7);
  border-radius: 10px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(107, 114, 128, 0.8);
}
</style>
