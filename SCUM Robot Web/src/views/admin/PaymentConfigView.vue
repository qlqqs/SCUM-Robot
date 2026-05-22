<template>
  <div>
    <!-- 页面头部 -->
    <div
      class="flex flex-col xl:flex-row xl:flex-wrap xl:justify-between xl:items-start mb-6 gap-4"
    >
      <div class="flex-shrink-0">
        <h2 class="text-lg sm:text-xl lg:text-2xl font-bold">支付配置管理</h2>
        <p class="text-xs sm:text-sm text-gray-400 mt-1 break-words">
          配置数量: {{ paymentConfigs.length }} | 加载状态:
          {{ loading ? '加载中' : '已完成' }}
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
            <span class="hidden lg:inline">充值套餐</span>
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

          <!-- 添加配置按钮 -->
          <button
            @click="openCreateModal"
            class="w-full sm:w-auto sm:min-w-[70px] bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded transition-colors text-xs font-medium"
          >
            <i class="fas fa-plus mr-1"></i>
            <span>添加配置</span>
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
      <div v-if="loading && paymentConfigs.length === 0" class="text-center py-8">
        <i class="fas fa-spinner fa-spin text-2xl text-gray-400 mb-2"></i>
        <p class="text-gray-400">加载支付配置中...</p>
      </div>

      <!-- 空状态 -->
      <div v-else-if="!loading && paymentConfigs.length === 0" class="text-center py-8">
        <i class="fas fa-credit-card text-4xl text-gray-500 mb-4"></i>
        <p class="text-gray-400 mb-4">暂无支付配置</p>
        <p class="text-sm text-gray-500">点击"添加配置"按钮创建第一个支付配置</p>
      </div>

      <!-- 配置表格 -->
      <div v-else class="overflow-x-auto" style="min-width: 0">
        <table class="w-full text-left" style="min-width: 1000px">
          <thead>
            <tr class="border-b border-gray-700">
              <th class="p-2 min-w-[120px] text-center">支付方式</th>
              <th class="p-2 min-w-[150px] text-center">描述</th>
              <th class="p-2 min-w-[100px] text-center">提供商</th>
              <th class="p-2 min-w-[60px] text-center">排序</th>
              <th class="p-2 min-w-[80px] text-center">状态</th>
              <th class="p-2 min-w-[150px] text-center">创建时间</th>
              <th class="p-2 min-w-[200px] text-center">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="config in paymentConfigs"
              :key="config.id"
              class="border-b border-gray-700 hover:bg-gray-700/30 transition-colors"
            >
              <!-- 支付方式 -->
              <td class="p-2 text-center">
                <div class="flex items-center justify-center gap-2">
                  <span class="font-medium text-sm">{{ config.provider_name }}</span>
                  <span
                    v-if="config.is_default"
                    class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-500/20 text-blue-400 border border-blue-500/30"
                  >
                    <i class="fas fa-star mr-1"></i>
                    默认
                  </span>
                </div>
              </td>

              <!-- 描述 -->
              <td class="p-2 text-center">
                <span class="text-sm text-gray-400">{{ config.description || '-' }}</span>
              </td>

              <!-- 提供商 -->
              <td class="p-2 text-center">
                <span class="text-sm text-gray-300">{{ config.provider_code }}</span>
              </td>

              <!-- 排序 -->
              <td class="p-2 text-center">
                <span class="text-sm text-gray-400">{{ config.sort_order }}</span>
              </td>

              <!-- 状态 -->
              <td class="p-2 text-center">
                <span
                  class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
                  :class="
                    config.is_active
                      ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                      : 'bg-gray-500/20 text-gray-400 border border-gray-500/30'
                  "
                >
                  <i :class="config.is_active ? 'fas fa-check' : 'fas fa-times'" class="mr-1"></i>
                  {{ config.is_active ? '启用' : '禁用' }}
                </span>
              </td>

              <!-- 创建时间 -->
              <td class="p-2 text-center">
                <span class="text-sm text-gray-400">{{ formatDate(config.created_at) }}</span>
              </td>

              <!-- 操作 -->
              <td class="p-2">
                <div class="flex items-center justify-center gap-1">
                  <button
                    @click="testConfig(config.id)"
                    :disabled="testingConfigs.has(config.id)"
                    class="text-blue-400 hover:text-blue-300 disabled:opacity-50 px-2 py-1 text-base"
                    title="测试配置"
                  >
                    <i
                      class="fas fa-vial"
                      :class="{ 'animate-spin': testingConfigs.has(config.id) }"
                    ></i>
                  </button>

                  <button
                    @click="editConfig(config)"
                    class="text-yellow-400 hover:text-yellow-300 px-2 py-1 text-base"
                    title="编辑"
                  >
                    <i class="fas fa-edit"></i>
                  </button>

                  <button
                    @click="deleteConfig(config.id)"
                    :disabled="deletingConfigs.has(config.id)"
                    class="text-red-400 hover:text-red-300 disabled:opacity-50 px-2 py-1 text-base"
                    title="删除"
                  >
                    <i
                      class="fas fa-trash"
                      :class="{ 'animate-spin': deletingConfigs.has(config.id) }"
                    ></i>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 创建/编辑配置模态框 -->
    <teleport to="body">
      <div
        v-if="showCreateModal || showEditModal"
        class="fixed inset-0 flex items-center justify-center z-[9999]"
      >
        <!-- 背景遮罩 -->
        <div class="absolute inset-0 bg-gray-800/60 backdrop-blur-md" @click="closeModal"></div>

        <!-- 模态框内容 -->
        <div
          class="bg-gray-800 bg-opacity-50 backdrop-blur-md rounded-lg shadow-2xl border border-gray-600 p-8 w-full max-w-2xl mx-4 transform transition-all duration-300 max-h-[90vh] overflow-y-auto relative z-10"
          :class="modalAnimationClass"
          @click.stop
        >
          <!-- 模态框头部 -->
          <div class="flex items-center justify-between mb-6 border-b border-gray-600 pb-4">
            <h3 class="text-lg font-semibold text-white">
              {{ showCreateModal ? '添加支付配置' : '编辑支付配置' }}
            </h3>
            <button @click="closeModal" class="text-gray-400 hover:text-gray-300 transition-colors">
              <i class="fas fa-times text-xl"></i>
            </button>
          </div>

          <!-- 模态框内容 -->
          <form @submit.prevent="saveConfig" class="space-y-6">
            <!-- 错误信息显示 -->
            <div
              v-if="error"
              class="bg-red-900/50 border border-red-500 text-red-200 px-4 py-3 rounded-lg"
            >
              <div class="flex items-center">
                <i class="fas fa-exclamation-triangle mr-2"></i>
                <span>{{ error }}</span>
              </div>
            </div>

            <!-- 成功信息显示 -->
            <div
              v-if="successMessage"
              class="bg-green-900/50 border border-green-500 text-green-200 px-4 py-3 rounded-lg"
            >
              <div class="flex items-center">
                <i class="fas fa-check-circle mr-2"></i>
                <span>{{ successMessage }}</span>
              </div>
            </div>

            <!-- 现有配置提示 -->
            <div
              v-if="showCreateModal && paymentConfigs.length > 0"
              class="bg-blue-900/20 border border-blue-700 text-blue-200 px-4 py-3 rounded-lg"
            >
              <div class="flex items-center">
                <i class="fas fa-info-circle mr-2"></i>
                <span>{{ getExistingConfigsInfo() }}</span>
              </div>
            </div>

            <!-- 基础信息 -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">
                  支付提供商 <span class="text-red-400">*</span>
                </label>
                <select
                  v-model="configForm.provider_code"
                  required
                  class="w-full bg-gray-700 border border-gray-600 rounded-lg py-2 px-3 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">请选择支付提供商</option>
                  <option value="alipay">支付宝</option>
                  <option value="epay">易支付</option>
                </select>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">
                  提供商名称 <span class="text-red-400">*</span>
                </label>
                <input
                  v-model="configForm.provider_name"
                  type="text"
                  required
                  class="w-full bg-gray-700 border border-gray-600 rounded-lg py-2 px-3 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="如：支付宝"
                />
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-300 mb-2">排序</label>
              <input
                v-model.number="configForm.sort_order"
                type="number"
                min="1"
                class="w-full bg-gray-700 border border-gray-600 rounded-lg py-2 px-3 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-300 mb-2">描述</label>
              <textarea
                v-model="configForm.description"
                rows="2"
                class="w-full bg-gray-700 border border-gray-600 rounded-lg py-2 px-3 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                placeholder="支付配置描述"
              ></textarea>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-300 mb-2">图标URL</label>
              <input
                v-model="configForm.icon"
                type="text"
                class="w-full bg-gray-700 border border-gray-600 rounded-lg py-2 px-3 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="/static/icons/alipay.png"
              />
            </div>

            <!-- 开关选项 -->
            <div class="flex items-center gap-6">
              <label class="flex items-center cursor-pointer">
                <input v-model="configForm.is_active" type="checkbox" class="sr-only peer" />
                <div
                  class="relative w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"
                ></div>
                <span class="ml-3 text-sm font-medium text-gray-300">启用配置</span>
              </label>

              <label class="flex items-center cursor-pointer">
                <input v-model="configForm.is_default" type="checkbox" class="sr-only peer" />
                <div
                  class="relative w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"
                ></div>
                <span class="ml-3 text-sm font-medium text-gray-300">设为默认</span>
              </label>
            </div>

            <!-- 配置参数 -->
            <div class="space-y-4">
              <h4 class="text-sm font-medium text-gray-300 mb-3">
                配置参数 <span class="text-red-400">*</span>
              </h4>

              <!-- 支付宝配置 -->
              <div v-if="configForm.provider_code === 'alipay'" class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-gray-400 mb-2"
                    >应用ID (app_id)</label
                  >
                  <input
                    v-model="configForm.config.app_id"
                    type="text"
                    required
                    class="w-full bg-gray-700 border border-gray-600 rounded-lg py-2 px-3 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="请输入支付宝应用ID"
                  />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-400 mb-2"
                    >应用私钥 (private_key)</label
                  >
                  <textarea
                    v-model="configForm.config.private_key"
                    rows="4"
                    required
                    class="w-full bg-gray-700 border border-gray-600 rounded-lg py-2 px-3 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                    placeholder="请输入应用私钥"
                  ></textarea>
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-400 mb-2"
                    >支付宝公钥 (public_key)</label
                  >
                  <textarea
                    v-model="configForm.config.public_key"
                    rows="4"
                    required
                    class="w-full bg-gray-700 border border-gray-600 rounded-lg py-2 px-3 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                    placeholder="请输入支付宝公钥"
                  ></textarea>
                </div>
              </div>

              <!-- 易支付配置 -->
              <div v-else-if="configForm.provider_code === 'epay'" class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-gray-400 mb-2">商户ID (pid)</label>
                  <input
                    v-model="configForm.config.pid"
                    type="text"
                    required
                    class="w-full bg-gray-700 border border-gray-600 rounded-lg py-2 px-3 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="请输入商户ID"
                  />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-400 mb-2">商户密钥 (key)</label>
                  <input
                    v-model="configForm.config.key"
                    type="text"
                    required
                    class="w-full bg-gray-700 border border-gray-600 rounded-lg py-2 px-3 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="请输入商户密钥"
                  />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-400 mb-2"
                    >API地址 (api_url)</label
                  >
                  <input
                    v-model="configForm.config.api_url"
                    type="url"
                    required
                    class="w-full bg-gray-700 border border-gray-600 rounded-lg py-2 px-3 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="https://api.example.com"
                  />
                </div>
              </div>

              <!-- 未选择提供商时的提示 -->
              <div v-else class="text-center py-8 text-gray-500">
                <i class="fas fa-info-circle text-2xl mb-2"></i>
                <p>请先选择支付提供商</p>
              </div>
            </div>

            <!-- 按钮组 -->
            <div class="flex justify-end gap-3 pt-4">
              <button
                type="button"
                @click="closeModal"
                class="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded transition-colors"
              >
                取消
              </button>
              <button
                type="submit"
                :disabled="saving"
                class="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded transition-colors"
              >
                <i class="fas fa-save mr-1" :class="{ 'animate-spin': saving }"></i>
                {{ saving ? '保存中...' : '保存' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { paymentApi } from '@/api/services/paymentApi.js'

// 响应式数据
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const successMessage = ref('')

// 配置数据
const paymentConfigs = ref([])

// 模态框状态
const showCreateModal = ref(false)
const showEditModal = ref(false)
const editingConfig = ref(null)

// 操作状态
const testingConfigs = ref(new Set())
const deletingConfigs = ref(new Set())

// 配置表单
const configForm = reactive({
  provider_code: '',
  provider_name: '',
  environment: 'production', // 添加环境字段，默认为production
  config: {
    // 支付宝配置
    app_id: '',
    private_key: '',
    public_key: '',
    // 易支付配置
    pid: '',
    key: '',
    api_url: '',
  },
  is_active: true,
  is_default: false,
  sort_order: 1,
  icon: '',
  description: '',
})

// 模态框动画类
const modalAnimationClass = computed(() => {
  return showCreateModal.value || showEditModal.value
    ? 'scale-100 opacity-100'
    : 'scale-95 opacity-0'
})

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

// 加载支付配置
const loadConfigs = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await paymentApi.getConfigs({
      include_sensitive: false,
    })
    if (response.success) {
      paymentConfigs.value = response.data || []
    } else {
      error.value = response.message || '加载支付配置失败'
    }
  } catch (err) {
    error.value = '加载支付配置失败: ' + (err.message || '未知错误')
    console.error('[PaymentConfig] Load configs error:', err)
  } finally {
    loading.value = false
  }
}

// 刷新数据
const refreshData = async () => {
  await loadConfigs()
}

// 测试配置
const testConfig = async (configId) => {
  testingConfigs.value.add(configId)
  try {
    const response = await paymentApi.testConfig(configId)
    if (response.success) {
      successMessage.value = '配置测试成功'
    } else {
      error.value = response.message || '配置测试失败'
    }
  } catch (err) {
    error.value = '配置测试失败: ' + (err.message || '未知错误')
    console.error('[PaymentConfig] Test config error:', err)
  } finally {
    testingConfigs.value.delete(configId)
  }
}

// 编辑配置
const editConfig = async (config) => {
  editingConfig.value = config

  // 清除之前的错误和成功信息
  error.value = ''
  successMessage.value = ''

  // 填充表单数据
  Object.assign(configForm, {
    provider_code: config.provider_code,
    provider_name: config.provider_name,
    environment: config.environment || 'production', // 添加environment字段
    is_active: config.is_active,
    is_default: config.is_default,
    sort_order: config.sort_order,
    icon: config.icon || '',
    description: config.description || '',
  })

  // 获取完整配置（包含敏感信息）
  try {
    const response = await paymentApi.getConfig(config.id, true)
    if (response.success && response.data.config) {
      Object.assign(configForm.config, response.data.config)
    }
  } catch (err) {
    console.warn('[PaymentConfig] Failed to load sensitive config:', err)
    // 重置配置
    Object.assign(configForm.config, {
      app_id: '',
      private_key: '',
      public_key: '',
      pid: '',
      key: '',
      api_url: '',
    })
  }

  showEditModal.value = true
}

// 获取现有配置的提示信息
const getExistingConfigsInfo = () => {
  const existingConfigs = paymentConfigs.value
    .map(
      (config) =>
        `${config.provider_code}(${config.environment === 'production' ? '生产' : '测试'})`,
    )
    .join(', ')
  return existingConfigs ? `现有配置: ${existingConfigs}` : '暂无配置'
}

// 打开创建模态框
const openCreateModal = async () => {
  // 清除之前的错误和成功信息
  error.value = ''
  successMessage.value = ''

  // 刷新配置列表以获取最新数据
  await loadConfigs()

  // 重置表单
  Object.assign(configForm, {
    provider_code: '',
    provider_name: '',
    environment: 'production', // 重置时也要包含environment字段
    config: {
      app_id: '',
      private_key: '',
      public_key: '',
      pid: '',
      key: '',
      api_url: '',
    },
    is_active: true,
    is_default: false,
    sort_order: 1,
    icon: '',
    description: '',
  })

  showCreateModal.value = true
}

// 删除配置
const deleteConfig = async (configId) => {
  if (!confirm('确定要删除这个支付配置吗？此操作不可恢复。')) {
    return
  }

  deletingConfigs.value.add(configId)
  try {
    const response = await paymentApi.deleteConfig(configId)
    if (response.success) {
      successMessage.value = '配置删除成功'
      await loadConfigs()
    } else {
      error.value = response.message || '配置删除失败'
    }
  } catch (err) {
    error.value = '配置删除失败: ' + (err.message || '未知错误')
    console.error('[PaymentConfig] Delete config error:', err)
  } finally {
    deletingConfigs.value.delete(configId)
  }
}

// 检查是否存在重复配置
const checkDuplicateConfig = () => {
  if (!showEditModal.value) {
    // 只在创建新配置时检查重复
    const existingConfig = paymentConfigs.value.find(
      (config) =>
        config.provider_code === configForm.provider_code &&
        config.environment === configForm.environment,
    )
    if (existingConfig) {
      return `该支付提供商(${configForm.provider_code})在${configForm.environment}环境下的配置已存在，请选择其他提供商或环境，或编辑现有配置`
    }
  }
  return null
}

// 自动添加PEM格式头尾标记
const formatPEMKey = (key, keyType = 'PRIVATE') => {
  if (!key || typeof key !== 'string') {
    return key
  }

  // 去除所有空白字符
  let cleanKey = key.trim().replace(/\s+/g, '')

  // 检查是否已经有头尾标记
  const hasHeader = cleanKey.includes('-----BEGIN')
  const hasFooter = cleanKey.includes('-----END')

  // 如果已经有完整的PEM格式，直接返回
  if (hasHeader && hasFooter) {
    return key
  }

  // 移除可能存在的不完整头尾标记
  cleanKey = cleanKey
    .replace(/-----BEGIN[^-]*-----/g, '')
    .replace(/-----END[^-]*-----/g, '')
    .trim()

  // 如果是空字符串，返回原值
  if (!cleanKey) {
    return key
  }

  // 将Base64字符串按每64字符分行
  const lines = []
  for (let i = 0; i < cleanKey.length; i += 64) {
    lines.push(cleanKey.substring(i, i + 64))
  }

  // 添加PEM头尾标记
  const header = `-----BEGIN ${keyType} KEY-----`
  const footer = `-----END ${keyType} KEY-----`

  return `${header}\n${lines.join('\n')}\n${footer}`
}

// 保存配置
const saveConfig = async () => {
  saving.value = true
  error.value = ''

  try {
    // 在检查重复配置前，先刷新配置列表以获取最新数据
    await loadConfigs()

    // 检查重复配置
    const duplicateError = checkDuplicateConfig()
    if (duplicateError) {
      error.value = duplicateError
      saving.value = false
      return
    }

    // 根据支付提供商过滤配置参数
    let configData = {}
    if (configForm.provider_code === 'alipay') {
      // 自动格式化支付宝密钥为PEM格式
      configData = {
        app_id: configForm.config.app_id,
        private_key: formatPEMKey(configForm.config.private_key, 'PRIVATE'),
        public_key: formatPEMKey(configForm.config.public_key, 'PUBLIC'),
      }
    } else if (configForm.provider_code === 'epay') {
      configData = {
        pid: configForm.config.pid,
        key: configForm.config.key,
        api_url: configForm.config.api_url,
      }
    }

    const payload = {
      ...configForm,
      config: configData,
    }

    let response
    if (showEditModal.value && editingConfig.value) {
      // 更新配置
      response = await paymentApi.updateConfig(editingConfig.value.id, payload)
    } else {
      // 创建配置
      response = await paymentApi.createConfig(payload)
    }

    if (response.success) {
      successMessage.value = showEditModal.value ? '配置更新成功' : '配置创建成功'
      closeModal()
      await loadConfigs()
    } else {
      // 处理特定的错误类型
      let errorMsg = response.message || '保存配置失败'
      if (errorMsg.includes('UNIQUE constraint failed') || errorMsg.includes('IntegrityError')) {
        errorMsg = `该支付提供商(${configForm.provider_code})在${configForm.environment}环境下的配置已存在，请选择其他提供商或环境，或编辑现有配置`
      }
      error.value = errorMsg
    }
  } catch (err) {
    error.value = '保存配置失败: ' + (err.message || '未知错误')
    console.error('[PaymentConfig] Save config error:', err)
  } finally {
    saving.value = false
  }
}

// 关闭模态框
const closeModal = () => {
  showCreateModal.value = false
  showEditModal.value = false
  editingConfig.value = null

  // 重置表单
  Object.assign(configForm, {
    provider_code: '',
    provider_name: '',
    config: {
      app_id: '',
      private_key: '',
      public_key: '',
      pid: '',
      key: '',
      api_url: '',
    },
    is_active: true,
    is_default: false,
    sort_order: 1,
    icon: '',
    description: '',
  })
}

// 组件挂载时加载数据
onMounted(async () => {
  await loadConfigs()
})
</script>

<style scoped>
/* 继承系统设置页面的样式 */
.bg-gray-850 {
  background-color: rgba(31, 41, 55, 0.8);
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
@media (max-width: 640px) {
  .grid-cols-1.md\\:grid-cols-2 {
    grid-template-columns: 1fr;
  }
}
</style>
