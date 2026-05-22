<template>
  <div>
    <!-- 页面头部 -->
    <div
      class="flex flex-col xl:flex-row xl:flex-wrap xl:justify-between xl:items-start mb-6 gap-4"
    >
      <div class="flex-shrink-0">
        <h2 class="text-lg sm:text-xl lg:text-2xl font-bold">订单管理</h2>
        <p class="text-xs sm:text-sm text-gray-400 mt-1 break-words">
          订单总数: {{ pagination.total || 0 }} | 当前页: {{ pagination.page || 1 }} /
          {{ pagination.total_pages || 1 }}
        </p>
      </div>
      <div
        class="flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center gap-2 sm:gap-3 xl:flex-shrink-0 xl:min-w-0"
      >
        <!-- 状态筛选 -->
        <select
          v-model="filters.status"
          @change="handleFilterChange"
          class="w-full sm:w-auto bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">全部状态</option>
          <option value="pending">待支付</option>
          <option value="processing">处理中</option>
          <option value="success">支付成功</option>
          <option value="failed">支付失败</option>
          <option value="cancelled">已取消</option>
          <option value="refunded">已退款</option>
          <option value="expired">已过期</option>
        </select>

        <!-- 刷新按钮 -->
        <button
          @click="refreshData"
          :disabled="loading"
          class="w-full sm:w-auto sm:min-w-[70px] bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-3 py-2 rounded transition-colors text-sm font-medium"
        >
          <i class="fas fa-sync-alt mr-1" :class="{ 'animate-spin': loading }"></i>
          <span>刷新</span>
        </button>
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

    <div class="bg-transparent p-6 rounded-lg w-full">
      <!-- 加载状态 -->
      <div v-if="loading && orders.length === 0" class="text-center py-8">
        <i class="fas fa-spinner fa-spin text-2xl text-gray-400 mb-2"></i>
        <p class="text-gray-400">加载订单数据中...</p>
      </div>

      <!-- 空状态 -->
      <div v-else-if="!loading && orders.length === 0" class="text-center py-8">
        <i class="fas fa-file-invoice-dollar text-4xl text-gray-500 mb-4"></i>
        <p class="text-gray-400 mb-4">暂无订单数据</p>
        <p class="text-sm text-gray-500">订单数据将在用户充值后显示</p>
      </div>

      <!-- 订单表格 -->
      <div v-else class="overflow-x-auto" style="min-width: 0">
        <table class="w-full text-left" style="min-width: 1200px">
          <thead>
            <tr class="border-b border-gray-700">
              <th class="p-2 min-w-[180px] text-center">订单号</th>
              <th class="p-2 min-w-[100px] text-center">用户</th>
              <th class="p-2 min-w-[120px] text-center">套餐</th>
              <th class="p-2 min-w-[80px] text-center">金额</th>
              <th class="p-2 min-w-[80px] text-center">商城币</th>
              <th class="p-2 min-w-[100px] text-center">支付方式</th>
              <th class="p-2 min-w-[100px] text-center">订单状态</th>
              <th class="p-2 min-w-[150px] text-center">创建时间</th>
              <th class="p-2 min-w-[150px] text-center">支付时间</th>
              <th class="p-2 min-w-[120px] text-center">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="order in orders"
              :key="order.order_id"
              class="border-b border-gray-700 hover:bg-gray-700/30 transition-colors"
            >
              <!-- 订单号 -->
              <td class="p-2 text-center">
                <span class="text-sm font-mono text-gray-300">{{ order.order_id }}</span>
              </td>

              <!-- 用户 -->
              <td class="p-2 text-center">
                <span class="text-sm text-gray-300">{{ order.user_name || order.user_id }}</span>
              </td>

              <!-- 套餐 -->
              <td class="p-2 text-center">
                <span class="text-sm text-gray-300">{{ order.description || '-' }}</span>
              </td>

              <!-- 金额 -->
              <td class="p-2 text-center">
                <span class="text-sm text-green-400">¥{{ order.amount }}</span>
              </td>

              <!-- 商城币 -->
              <td class="p-2 text-center">
                <span class="text-sm text-yellow-400">
                  {{
                    order.coins_added !== null && order.coins_added !== undefined
                      ? order.coins_added
                      : '-'
                  }}
                </span>
              </td>

              <!-- 支付方式 -->
              <td class="p-2 text-center">
                <span class="text-sm text-gray-300">{{ order.provider_name || '-' }}</span>
              </td>

              <!-- 订单状态 -->
              <td class="p-2 text-center">
                <span
                  class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
                  :class="getStatusClass(order.status)"
                >
                  {{ getStatusText(order.status) }}
                </span>
              </td>

              <!-- 创建时间 -->
              <td class="p-2 text-center">
                <span class="text-sm text-gray-400">{{ formatDate(order.created_at) }}</span>
              </td>

              <!-- 支付时间 -->
              <td class="p-2 text-center">
                <span class="text-sm text-gray-400">{{
                  order.paid_at ? formatDate(order.paid_at) : '-'
                }}</span>
              </td>

              <!-- 操作 -->
              <td class="p-2">
                <div class="flex items-center justify-center gap-1">
                  <button
                    @click="viewOrderDetail(order)"
                    class="text-blue-400 hover:text-blue-300 px-2 py-1 text-base"
                    title="查看详情"
                  >
                    <i class="fas fa-eye"></i>
                  </button>
                  <button
                    @click="refreshOrderStatus(order.order_id)"
                    :disabled="refreshingOrders.has(order.order_id)"
                    class="text-green-400 hover:text-green-300 disabled:opacity-50 px-2 py-1 text-base"
                    title="刷新状态"
                  >
                    <i
                      class="fas fa-sync-alt"
                      :class="{ 'animate-spin': refreshingOrders.has(order.order_id) }"
                    ></i>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 分页 -->
      <div
        v-if="pagination.total_pages > 1"
        class="flex items-center justify-center gap-2 mt-6 flex-wrap"
      >
        <button
          @click="goToPage(1)"
          :disabled="!pagination.has_prev"
          class="px-3 py-1 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded text-sm transition-colors"
        >
          <i class="fas fa-angle-double-left"></i>
        </button>
        <button
          @click="goToPage(currentPage - 1)"
          :disabled="!pagination.has_prev"
          class="px-3 py-1 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded text-sm transition-colors"
        >
          <i class="fas fa-angle-left"></i>
        </button>
        <span class="text-sm text-gray-300">
          第 {{ pagination.page }} / {{ pagination.total_pages }} 页
        </span>
        <button
          @click="goToPage(currentPage + 1)"
          :disabled="!pagination.has_next"
          class="px-3 py-1 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded text-sm transition-colors"
        >
          <i class="fas fa-angle-right"></i>
        </button>
        <button
          @click="goToPage(pagination.total_pages)"
          :disabled="!pagination.has_next"
          class="px-3 py-1 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded text-sm transition-colors"
        >
          <i class="fas fa-angle-double-right"></i>
        </button>
      </div>
    </div>

    <!-- 订单详情模态框 -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="showDetailModal"
          class="fixed inset-0 flex items-center justify-center z-[9999]"
          @click="closeDetailModal"
        >
          <!-- 背景遮罩 -->
          <div class="absolute inset-0 bg-gray-800/60 backdrop-blur-md"></div>

          <!-- 模态框内容 -->
          <div
            class="bg-gray-800 rounded-lg shadow-2xl border border-gray-600 p-6 max-w-2xl w-full mx-4 relative z-10 max-h-[90vh] overflow-y-auto"
            @click.stop
          >
            <!-- 模态框头部 -->
            <div class="flex items-center justify-between mb-4 border-b border-gray-600 pb-4">
              <h3 class="text-lg font-semibold text-white">订单详情</h3>
              <button
                @click="closeDetailModal"
                class="text-gray-400 hover:text-gray-300 transition-colors"
              >
                <i class="fas fa-times text-xl"></i>
              </button>
            </div>

            <!-- 订单信息 -->
            <div v-if="selectedOrder" class="space-y-4">
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm text-gray-400 mb-1">订单号</label>
                  <p class="text-white font-mono text-sm">{{ selectedOrder.order_id }}</p>
                </div>
                <div>
                  <label class="block text-sm text-gray-400 mb-1">订单状态</label>
                  <span
                    class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
                    :class="getStatusClass(selectedOrder.status)"
                  >
                    {{ getStatusText(selectedOrder.status) }}
                  </span>
                </div>
                <div>
                  <label class="block text-sm text-gray-400 mb-1">用户ID</label>
                  <p class="text-white text-sm">{{ selectedOrder.user_id || '-' }}</p>
                </div>
                <div>
                  <label class="block text-sm text-gray-400 mb-1">套餐描述</label>
                  <p class="text-white text-sm">{{ selectedOrder.description || '-' }}</p>
                </div>
                <div>
                  <label class="block text-sm text-gray-400 mb-1">金额</label>
                  <p class="text-green-400 text-sm">¥{{ selectedOrder.amount }}</p>
                </div>
                <div>
                  <label class="block text-sm text-gray-400 mb-1">商城币</label>
                  <p class="text-yellow-400 text-sm">{{ selectedOrder.coins_added || '-' }}</p>
                </div>
                <div>
                  <label class="block text-sm text-gray-400 mb-1">币种</label>
                  <p class="text-white text-sm">{{ selectedOrder.currency || 'CNY' }}</p>
                </div>
                <div>
                  <label class="block text-sm text-gray-400 mb-1">是否已发放</label>
                  <p class="text-white text-sm">
                    <span
                      :class="selectedOrder.is_coins_added ? 'text-green-400' : 'text-gray-400'"
                    >
                      {{ selectedOrder.is_coins_added ? '是' : '否' }}
                    </span>
                  </p>
                </div>
                <div>
                  <label class="block text-sm text-gray-400 mb-1">支付方式</label>
                  <p class="text-white text-sm">{{ selectedOrder.provider_name || '-' }}</p>
                </div>
                <div>
                  <label class="block text-sm text-gray-400 mb-1">创建时间</label>
                  <p class="text-white text-sm">{{ formatDate(selectedOrder.created_at) }}</p>
                </div>
                <div>
                  <label class="block text-sm text-gray-400 mb-1">支付时间</label>
                  <p class="text-white text-sm">
                    {{ selectedOrder.paid_at ? formatDate(selectedOrder.paid_at) : '-' }}
                  </p>
                </div>
                <div>
                  <label class="block text-sm text-gray-400 mb-1">过期时间</label>
                  <p class="text-white text-sm">
                    {{ selectedOrder.expired_at ? formatDate(selectedOrder.expired_at) : '-' }}
                  </p>
                </div>
              </div>

              <!-- 关闭按钮 -->
              <div class="flex justify-end pt-4 border-t border-gray-600">
                <button
                  @click="closeDetailModal"
                  class="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded transition-colors"
                >
                  关闭
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { paymentApi } from '@/api/services/paymentApi.js'

// 状态管理
const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const orders = ref([])
const refreshingOrders = ref(new Set())

// 分页和筛选
const currentPage = ref(1)
const pageSize = ref(10)
const pagination = ref({
  page: 1,
  page_size: 10,
  total: 0,
  total_pages: 1,
  has_next: false,
  has_prev: false,
})
const filters = ref({
  status: '',
})

// 模态框状态
const showDetailModal = ref(false)
const selectedOrder = ref(null)

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

// 获取订单状态样式
const getStatusClass = (status) => {
  const statusMap = {
    pending: 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30',
    processing: 'bg-blue-500/20 text-blue-400 border border-blue-500/30',
    success: 'bg-green-500/20 text-green-400 border border-green-500/30',
    failed: 'bg-red-500/20 text-red-400 border border-red-500/30',
    cancelled: 'bg-gray-500/20 text-gray-400 border border-gray-500/30',
    refunded: 'bg-purple-500/20 text-purple-400 border border-purple-500/30',
    expired: 'bg-orange-500/20 text-orange-400 border border-orange-500/30',
  }
  return statusMap[status] || 'bg-gray-500/20 text-gray-400 border border-gray-500/30'
}

// 获取订单状态文本
const getStatusText = (status) => {
  const statusMap = {
    pending: '待支付',
    processing: '处理中',
    success: '支付成功',
    failed: '支付失败',
    cancelled: '已取消',
    refunded: '已退款',
    expired: '已过期',
  }
  return statusMap[status] || status
}

// 加载订单数据
const loadOrders = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
    }

    // 添加筛选条件
    if (filters.value.status) {
      params.status = filters.value.status
    }

    const response = await paymentApi.getOrders(params)
    if (response.success) {
      orders.value = response.data?.orders || []
      pagination.value = response.data?.pagination || {
        page: 1,
        page_size: 10,
        total: 0,
        total_pages: 1,
        has_next: false,
        has_prev: false,
      }

      // 调试日志：查看第一个订单的数据结构
      if (orders.value.length > 0) {
        console.log('[Orders] First order data:', orders.value[0])
        console.log('[Orders] coins_added field:', orders.value[0].coins_added)
      }
    } else {
      errorMessage.value = response.message || '加载订单数据失败'
    }
  } catch (err) {
    errorMessage.value = '加载订单数据失败: ' + (err.message || '未知错误')
    console.error('[Orders] Load orders error:', err)
  } finally {
    loading.value = false
  }
}

// 刷新数据
const refreshData = async () => {
  await loadOrders()
}

// 跳转到指定页
const goToPage = (page) => {
  if (page < 1 || page > pagination.value.total_pages) return
  currentPage.value = page
  loadOrders()
}

// 处理筛选变化
const handleFilterChange = () => {
  currentPage.value = 1 // 重置到第一页
  loadOrders()
}

// 查看订单详情
const viewOrderDetail = (order) => {
  selectedOrder.value = order
  showDetailModal.value = true
}

// 关闭详情模态框
const closeDetailModal = () => {
  showDetailModal.value = false
  selectedOrder.value = null
}

// 刷新订单状态
const refreshOrderStatus = async (orderId) => {
  refreshingOrders.value.add(orderId)
  try {
    const response = await paymentApi.getOrderStatus(orderId)
    if (response.success) {
      // 更新订单状态
      const index = orders.value.findIndex((o) => o.order_id === orderId)
      if (index !== -1) {
        orders.value[index] = { ...orders.value[index], ...response.data }
      }
      successMessage.value = '订单状态已更新'
    } else {
      errorMessage.value = response.message || '刷新订单状态失败'
    }
  } catch (err) {
    errorMessage.value = '刷新订单状态失败: ' + (err.message || '未知错误')
    console.error('[Orders] Refresh order status error:', err)
  } finally {
    refreshingOrders.value.delete(orderId)
  }
}

// 页面加载时获取数据
onMounted(() => {
  loadOrders()
})
</script>

<style scoped>
/* 模态框动画 */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
