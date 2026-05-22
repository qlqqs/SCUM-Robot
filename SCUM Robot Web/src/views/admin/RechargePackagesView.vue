<template>
  <div>
    <!-- 页面头部 -->
    <div
      class="flex flex-col xl:flex-row xl:flex-wrap xl:justify-between xl:items-start mb-6 gap-4"
    >
      <div class="flex-shrink-0">
        <h2 class="text-lg sm:text-xl lg:text-2xl font-bold">充值套餐管理</h2>
        <p class="text-xs sm:text-sm text-gray-400 mt-1 break-words">
          套餐数量: {{ packages.length }} | 加载状态: {{ loading ? '加载中' : '已完成' }}
        </p>
      </div>
      <div
        class="flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center gap-2 sm:gap-3 xl:flex-shrink-0 xl:min-w-0 max-w-full overflow-hidden"
      >
        <!-- 导航切换按钮 -->
        <div class="flex bg-gray-700 rounded-lg p-1 w-full sm:w-auto sm:min-w-[160px]">
          <router-link
            to="/admin/packages"
            class="flex-1 sm:flex-none px-2 py-2 rounded-md text-xs font-medium transition-colors text-center whitespace-nowrap"
            :class="
              $route.path === '/admin/packages'
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:text-white hover:bg-gray-600'
            "
          >
            <i class="fas fa-box-open mr-1"></i>
            <span class="hidden lg:inline">套餐管理</span>
            <span class="lg:hidden">套餐</span>
          </router-link>
          <router-link
            to="/admin/payment"
            class="flex-1 sm:flex-none px-2 py-2 rounded-md text-xs font-medium transition-colors text-center whitespace-nowrap"
            :class="
              $route.path === '/admin/payment'
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:text-white hover:bg-gray-600'
            "
          >
            <i class="fas fa-credit-card mr-1"></i>
            <span class="hidden lg:inline">支付配置</span>
            <span class="lg:hidden">配置</span>
          </router-link>
        </div>

        <!-- 按钮组 -->
        <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-3">
          <!-- 刷新按钮 -->
          <button
            @click="refreshData"
            :disabled="loading"
            class="w-full sm:w-auto sm:min-w-[70px] bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-3 py-2 rounded transition-colors text-xs font-medium"
          >
            <i class="fas fa-sync-alt mr-1" :class="{ 'animate-spin': loading }"></i>
            <span>刷新</span>
          </button>

          <!-- 添加套餐按钮 -->
          <button
            @click="openCreateModal"
            class="w-full sm:w-auto sm:min-w-[70px] bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded transition-colors text-xs font-medium"
          >
            <i class="fas fa-plus mr-1"></i>
            <span>添加套餐</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="mb-6 p-4 bg-red-900/50 border border-red-500 rounded-lg">
      <div class="flex items-center justify-between">
        <div class="flex items-center">
          <i class="fas fa-exclamation-triangle text-red-400 mr-2"></i>
          <span class="text-red-200">{{ error }}</span>
        </div>
        <button @click="error = ''" class="text-red-400 hover:text-red-300">
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
      <div v-if="loading && packages.length === 0" class="text-center py-8">
        <i class="fas fa-spinner fa-spin text-2xl text-gray-400 mb-2"></i>
        <p class="text-gray-400">加载充值套餐中...</p>
      </div>

      <!-- 空状态 -->
      <div v-else-if="!loading && packages.length === 0" class="text-center py-8">
        <i class="fas fa-box-open text-4xl text-gray-500 mb-4"></i>
        <p class="text-gray-400 mb-4">暂无充值套餐</p>
        <p class="text-sm text-gray-500">点击"添加套餐"按钮创建第一个充值套餐</p>
      </div>

      <!-- 套餐表格 -->
      <div v-else class="overflow-x-auto" style="min-width: 0">
        <table class="w-full text-left" style="min-width: 1200px">
          <thead>
            <tr class="border-b border-gray-700">
              <th class="p-2 min-w-[120px] text-center">套餐名称</th>
              <th class="p-2 min-w-[150px] text-center">描述</th>
              <th class="p-2 min-w-[180px] text-center">支付项目名称</th>
              <th class="p-2 min-w-[80px] text-center">价格</th>
              <th class="p-2 min-w-[80px] text-center">商城币</th>
              <th class="p-2 min-w-[80px] text-center">赠送</th>
              <th class="p-2 min-w-[80px] text-center">总计</th>
              <th class="p-2 min-w-[80px] text-center">徽章</th>
              <th class="p-2 min-w-[60px] text-center">排序</th>
              <th class="p-2 min-w-[80px] text-center">状态</th>
              <th class="p-2 min-w-[180px] text-center">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="pkg in packages"
              :key="pkg.id"
              class="border-b border-gray-700 hover:bg-gray-700/30 transition-colors"
            >
              <!-- 套餐名称 -->
              <td class="p-2 text-center">
                <span class="font-medium text-sm">{{ pkg.name }}</span>
              </td>

              <!-- 描述 -->
              <td class="p-2 text-center">
                <span class="text-sm text-gray-400">{{ pkg.description || '-' }}</span>
              </td>

              <!-- 支付项目名称 -->
              <td class="p-2 text-center">
                <span class="text-sm text-blue-400" :title="pkg.product_name">
                  {{ pkg.product_name || '-' }}
                </span>
              </td>

              <!-- 价格 -->
              <td class="p-2 text-center">
                <span class="text-sm text-green-400">¥{{ pkg.price }}</span>
              </td>

              <!-- 商城币 -->
              <td class="p-2 text-center">
                <span class="text-sm text-yellow-400">{{ pkg.coins }}</span>
              </td>

              <!-- 赠送 -->
              <td class="p-2 text-center">
                <span class="text-sm text-purple-400">{{ pkg.bonus_coins || 0 }}</span>
              </td>

              <!-- 总计 -->
              <td class="p-2 text-center">
                <span class="text-sm text-cyan-400 font-medium">{{
                  pkg.total_coins || pkg.coins + (pkg.bonus_coins || 0)
                }}</span>
              </td>

              <!-- 徽章 -->
              <td class="p-2 text-center">
                <span
                  v-if="pkg.badge"
                  class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
                  :class="{
                    'bg-red-500/20 text-red-400 border border-red-500/30': pkg.badge === 'HOT',
                    'bg-green-500/20 text-green-400 border border-green-500/30':
                      pkg.badge === 'NEW',
                    'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30':
                      pkg.badge === 'VIP',
                  }"
                >
                  {{ pkg.badge }}
                </span>
                <span v-else class="text-sm text-gray-500">-</span>
              </td>

              <!-- 排序 -->
              <td class="p-2 text-center">
                <span class="text-sm text-gray-400">{{ pkg.sort_order }}</span>
              </td>

              <!-- 状态 -->
              <td class="p-2 text-center">
                <span
                  class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
                  :class="
                    pkg.is_active
                      ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                      : 'bg-gray-500/20 text-gray-400 border border-gray-500/30'
                  "
                >
                  {{ pkg.is_active ? '启用' : '禁用' }}
                </span>
              </td>

              <!-- 操作 -->
              <td class="p-2">
                <div class="flex items-center justify-center gap-1">
                  <button
                    @click="editPackage(pkg)"
                    class="text-blue-400 hover:text-blue-300 px-2 py-1 text-base"
                    title="编辑"
                  >
                    <i class="fas fa-edit"></i>
                  </button>
                  <button
                    @click="togglePackageStatus(pkg)"
                    class="px-2 py-1 text-base"
                    :class="
                      pkg.is_active
                        ? 'text-yellow-400 hover:text-yellow-300'
                        : 'text-green-400 hover:text-green-300'
                    "
                    :title="pkg.is_active ? '禁用' : '启用'"
                  >
                    <i :class="pkg.is_active ? 'fas fa-ban' : 'fas fa-check'"></i>
                  </button>
                  <button
                    @click="deletePackage(pkg)"
                    class="text-red-400 hover:text-red-300 px-2 py-1 text-base"
                    title="删除"
                  >
                    <i class="fas fa-trash"></i>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 创建/编辑套餐模态框 -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="showModal"
          class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
        >
          <div
            class="bg-gray-800 rounded-lg shadow-2xl border border-gray-600 p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto"
            @click.stop
          >
            <!-- 模态框头部 -->
            <div class="flex items-center justify-between mb-6 border-b border-gray-600 pb-4">
              <h3 class="text-xl font-semibold text-white">
                {{ editingPackage ? '编辑套餐' : '添加套餐' }}
              </h3>
              <button @click="closeModal" class="text-gray-400 hover:text-gray-300">
                <i class="fas fa-times text-xl"></i>
              </button>
            </div>

            <!-- 表单 -->
            <form @submit.prevent="savePackage" class="space-y-4">
              <!-- 套餐名称 -->
              <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">
                  套餐名称 <span class="text-red-400">*</span>
                </label>
                <input
                  v-model="packageForm.name"
                  type="text"
                  required
                  class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="例如: 标准充值"
                />
              </div>

              <!-- 套餐描述 -->
              <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">套餐描述</label>
                <input
                  v-model="packageForm.description"
                  type="text"
                  class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="例如: 最受欢迎，超值优惠"
                />
              </div>

              <!-- 支付项目名称 -->
              <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">
                  支付项目名称
                  <span class="text-xs text-gray-400 ml-2">(显示在支付宝账单中)</span>
                </label>
                <input
                  v-model="packageForm.product_name"
                  type="text"
                  maxlength="64"
                  class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="例如: SCUM游戏币充值 - 性价比之选"
                />
                <p class="text-xs text-gray-400 mt-1">
                  建议格式: 游戏名称 + 充值类型 + 套餐名称 (最多64个字符)
                </p>
              </div>

              <!-- 标签和徽章 -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-300 mb-2">标签</label>
                  <input
                    v-model="packageForm.tag"
                    type="text"
                    class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="例如: 性价比之选"
                  />
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-300 mb-2">徽章</label>
                  <select
                    v-model="packageForm.badge"
                    class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">无徽章</option>
                    <option value="HOT">HOT（热门）</option>
                    <option value="NEW">NEW（新品）</option>
                    <option value="VIP">VIP（尊享）</option>
                  </select>
                </div>
              </div>

              <!-- 价格和商城币 -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-300 mb-2">
                    价格 (元) <span class="text-red-400">*</span>
                  </label>
                  <input
                    v-model.number="packageForm.price"
                    type="number"
                    step="0.01"
                    min="0.01"
                    required
                    class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="30.00"
                  />
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-300 mb-2">
                    商城币 <span class="text-red-400">*</span>
                  </label>
                  <input
                    v-model.number="packageForm.coins"
                    type="number"
                    min="1"
                    required
                    class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="300"
                  />
                </div>
              </div>

              <!-- 赠送和排序 -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-300 mb-2">赠送商城币</label>
                  <input
                    v-model.number="packageForm.bonus_coins"
                    type="number"
                    min="0"
                    class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="50"
                  />
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-300 mb-2">排序</label>
                  <input
                    v-model.number="packageForm.sort_order"
                    type="number"
                    min="0"
                    class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="1"
                  />
                </div>
              </div>

              <!-- 开关选项 -->
              <div class="space-y-3">
                <label class="flex items-center cursor-pointer">
                  <input
                    v-model="packageForm.is_active"
                    type="checkbox"
                    class="w-5 h-5 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500"
                  />
                  <span class="ml-3 text-sm text-gray-300">启用套餐</span>
                </label>
              </div>

              <!-- 错误提示 -->
              <div v-if="error" class="p-3 bg-red-900/50 border border-red-500 rounded-lg">
                <p class="text-sm text-red-200">{{ error }}</p>
              </div>

              <!-- 按钮 -->
              <div class="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  @click="closeModal"
                  class="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                >
                  取消
                </button>
                <button
                  type="submit"
                  :disabled="saving"
                  class="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg transition-colors"
                >
                  <i v-if="saving" class="fas fa-spinner fa-spin mr-2"></i>
                  {{ saving ? '保存中...' : '保存' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { rechargePackageApi } from '@/api/services/rechargePackageApi.js'

// 状态
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const successMessage = ref('')
const packages = ref([])
const showModal = ref(false)
const editingPackage = ref(null)

// 表单数据
const packageForm = ref({
  name: '',
  description: '',
  product_name: 'SCUM游戏币充值', // 默认支付项目名称
  tag: '',
  price: 0,
  coins: 0,
  bonus_coins: 0,
  badge: '',
  sort_order: 1,
  is_active: true,
  is_hot: false,
  is_recommended: false,
})

// 加载套餐列表
const loadPackages = async () => {
  loading.value = true
  error.value = ''

  try {
    // 从后端API获取套餐列表（包括禁用的套餐）
    const response = await rechargePackageApi.getPackages({ active_only: false })

    if (response.success && response.data) {
      // 按排序顺序排列
      packages.value = response.data.sort((a, b) => a.sort_order - b.sort_order)
      console.log('[RechargePackages] Loaded packages:', packages.value.length)
    } else {
      throw new Error(response.message || '获取套餐列表失败')
    }
  } catch (err) {
    console.error('[RechargePackages] Failed to load packages:', err)
    error.value = err.message || '加载套餐列表失败'
  } finally {
    loading.value = false
  }
}

// 刷新数据
const refreshData = () => {
  loadPackages()
}

// 打开创建模态框
const openCreateModal = () => {
  editingPackage.value = null
  packageForm.value = {
    name: '',
    description: '',
    product_name: 'SCUM游戏币充值', // 默认支付项目名称
    tag: '',
    price: 0,
    coins: 0,
    bonus_coins: 0,
    badge: '',
    sort_order: packages.value.length + 1,
    is_active: true,
    is_hot: false,
    is_recommended: false,
  }
  showModal.value = true
}

// 编辑套餐
const editPackage = (pkg) => {
  editingPackage.value = pkg
  packageForm.value = { ...pkg }
  showModal.value = true
}

// 关闭模态框
const closeModal = () => {
  showModal.value = false
  editingPackage.value = null
  error.value = ''
}

// 保存套餐
const savePackage = async () => {
  saving.value = true
  error.value = ''

  try {
    let response

    if (editingPackage.value) {
      // 更新套餐
      response = await rechargePackageApi.updatePackage(editingPackage.value.id, packageForm.value)
    } else {
      // 创建套餐
      response = await rechargePackageApi.createPackage(packageForm.value)
    }

    if (response.success) {
      successMessage.value =
        response.message || (editingPackage.value ? '套餐更新成功' : '套餐创建成功')
      closeModal()
      // 重新加载套餐列表
      await loadPackages()
      setTimeout(() => {
        successMessage.value = ''
      }, 3000)
    } else {
      throw new Error(response.message || '保存套餐失败')
    }
  } catch (err) {
    console.error('[RechargePackages] Failed to save package:', err)
    error.value = err.message || '保存套餐失败'
  } finally {
    saving.value = false
  }
}

// 切换套餐状态
const togglePackageStatus = async (pkg) => {
  try {
    // 更新套餐状态
    const response = await rechargePackageApi.updatePackage(pkg.id, {
      is_active: !pkg.is_active,
    })

    if (response.success) {
      pkg.is_active = !pkg.is_active
      successMessage.value = `套餐已${pkg.is_active ? '启用' : '禁用'}`
      setTimeout(() => {
        successMessage.value = ''
      }, 3000)
    } else {
      throw new Error(response.message || '切换状态失败')
    }
  } catch (err) {
    console.error('[RechargePackages] Failed to toggle status:', err)
    error.value = err.message || '切换状态失败'
  }
}

// 删除套餐
const deletePackage = async (pkg) => {
  if (!confirm(`确定要删除套餐"${pkg.name}"吗？此操作不可恢复！`)) {
    return
  }

  try {
    const response = await rechargePackageApi.deletePackage(pkg.id)

    if (response.success) {
      successMessage.value = response.message || '套餐删除成功'
      // 重新加载套餐列表
      await loadPackages()
      setTimeout(() => {
        successMessage.value = ''
      }, 3000)
    } else {
      throw new Error(response.message || '删除套餐失败')
    }
  } catch (err) {
    console.error('[RechargePackages] Failed to delete package:', err)
    error.value = err.message || '删除套餐失败'
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadPackages()
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

.modal-enter-active > div,
.modal-leave-active > div {
  transition: transform 0.3s ease;
}

.modal-enter-from > div,
.modal-leave-to > div {
  transform: scale(0.9);
}
</style>
