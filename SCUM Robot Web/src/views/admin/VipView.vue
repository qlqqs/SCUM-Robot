<template>
  <div>
    <!-- 页面标题 -->
    <div
      class="flex flex-col xl:flex-row xl:flex-wrap xl:justify-between xl:items-start mb-6 gap-4"
    >
      <div class="flex-shrink-0">
        <h2 class="text-lg sm:text-xl lg:text-2xl font-bold">VIP配置管理</h2>
        <p class="text-xs sm:text-sm text-gray-400 mt-1 break-words">
          当前VIP配置数量: {{ vipConfigs.length }} | 加载状态:
          {{ loading ? '加载中' : '已完成' }}
        </p>
      </div>
      <div
        class="flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center gap-2 sm:gap-3 xl:flex-shrink-0 xl:min-w-0"
      >
        <!-- 刷新按钮 -->
        <button
          @click="loadVipConfigs"
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
      <!-- 添加VIP配置表单 -->
      <form @submit.prevent="addVipConfig" class="flex flex-wrap items-end gap-4 mb-6">
        <div class="flex-1 min-w-[100px]">
          <label class="block text-xs text-gray-400 mb-1"
            >VIP等级 <span class="text-red-400">*</span></label
          >
          <input
            v-model.number="newVipData.level"
            type="number"
            min="0"
            placeholder="0"
            class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
            :disabled="isSubmitting"
            required
          />
        </div>

        <div class="flex-1 min-w-[120px]">
          <label class="block text-xs text-gray-400 mb-1"
            >等级名称 <span class="text-red-400">*</span></label
          >
          <input
            v-model="newVipData.name"
            type="text"
            maxlength="50"
            placeholder="输入名称"
            class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
            :disabled="isSubmitting"
            required
          />
        </div>

        <div class="flex-1 min-w-[140px]">
          <label class="block text-xs text-gray-400 mb-1">每日礼包</label>
          <select
            v-model="newVipData.daily_gift_id"
            class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
            :disabled="isSubmitting"
          >
            <option value="">请选择（可选）</option>
            <option v-for="gift in giftsList" :key="gift.id" :value="gift.id">
              {{ gift.name }}
            </option>
          </select>
        </div>

        <div class="flex-1 min-w-[120px]">
          <label class="block text-xs text-gray-400 mb-1"
            >升级积分 <span class="text-red-400">*</span></label
          >
          <input
            v-model.number="newVipData.upgrade_required_points"
            type="number"
            min="0"
            placeholder="0"
            class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
            :disabled="isSubmitting"
            required
          />
        </div>

        <div class="flex-shrink-0">
          <label class="block text-xs text-gray-400 mb-1">进服公告</label>
          <div class="flex items-center h-[38px]">
            <label class="flex items-center cursor-pointer">
              <input
                v-model="newVipData.enable_login_announcement"
                type="checkbox"
                class="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500 focus:ring-2 mr-2"
                :disabled="isSubmitting"
              />
              <span class="text-sm text-gray-300">启用</span>
            </label>
          </div>
        </div>

        <div class="flex-shrink-0">
          <button
            type="submit"
            :disabled="isSubmitting || !newVipData.name.trim()"
            class="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-6 py-2 rounded-md font-medium transition-colors flex items-center space-x-2 h-[38px]"
          >
            <i class="fas fa-plus" v-if="!isSubmitting"></i>
            <i class="fas fa-spinner fa-spin" v-if="isSubmitting"></i>
            <span>{{ isSubmitting ? '添加中...' : '添加配置' }}</span>
          </button>
        </div>
      </form>

      <!-- 加载状态 -->
      <div v-if="loading && vipConfigs.length === 0" class="text-center py-8">
        <i class="fas fa-spinner fa-spin text-2xl text-gray-400 mb-2"></i>
        <p class="text-gray-400">加载VIP配置数据中...</p>
      </div>

      <!-- 空状态 -->
      <div v-else-if="!loading && vipConfigs.length === 0" class="text-center py-8">
        <i class="fas fa-crown text-4xl text-gray-500 mb-4"></i>
        <p class="text-gray-400 mb-4">暂无VIP配置数据</p>
        <p class="text-sm text-gray-500">点击上方"添加VIP配置"按钮创建第一个VIP配置</p>
      </div>

      <!-- 数据表格 -->
      <div v-else class="overflow-x-auto" style="min-width: 0">
        <table class="w-full text-left" style="min-width: 800px">
          <thead>
            <tr class="border-b border-gray-700">
              <th class="p-2 min-w-[100px] w-[120px] text-center">VIP等级</th>
              <th class="p-2 min-w-[100px] w-[120px] text-center">等级名称</th>
              <th class="p-2 min-w-[120px] w-[140px] text-center">每日礼包</th>
              <th class="p-2 min-w-[100px] w-[120px] text-center">升级所需积分</th>
              <th class="p-2 min-w-[120px] w-[140px] text-center">进服公告</th>
              <th class="p-2 min-w-[100px] w-[120px] text-center">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="config in vipConfigs"
              :key="config.level"
              class="border-b border-gray-700 hover:bg-gray-700/30 transition-colors"
            >
              <td class="p-2 text-center">
                <div class="flex items-center justify-center">
                  <i class="fas fa-crown text-yellow-400 mr-1"></i>
                  <span class="font-medium text-sm">VIP {{ config.level }}</span>
                </div>
              </td>
              <td class="p-2 text-center">
                <span v-if="editingConfig?.level === config.level">
                  <input
                    v-model="editingConfig.name"
                    type="text"
                    maxlength="50"
                    class="w-full bg-gray-700 border border-gray-600 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 text-center"
                    :disabled="isSubmitting"
                    required
                  />
                </span>
                <span v-else class="text-base font-medium">{{ config.name }}</span>
              </td>
              <td class="p-2 text-center">
                <span v-if="editingConfig?.level === config.level">
                  <select
                    v-model="editingConfig.daily_gift_id"
                    class="w-full bg-gray-700 border border-gray-600 rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 text-center"
                    :disabled="isSubmitting"
                  >
                    <option value="">请选择礼包（可选）</option>
                    <option v-for="gift in giftsList" :key="gift.id" :value="gift.id">
                      {{ gift.name }}
                    </option>
                  </select>
                </span>
                <span v-else-if="config.daily_gift_id" class="text-green-400 text-base">
                  {{ getGiftNameById(config.daily_gift_id) }}
                </span>
                <span v-else class="text-gray-500 text-base">未设置</span>
              </td>
              <td class="p-2 text-center">
                <span v-if="editingConfig?.level === config.level">
                  <input
                    v-model.number="editingConfig.upgrade_required_points"
                    type="number"
                    min="0"
                    class="w-full bg-gray-700 border border-gray-600 rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 text-center"
                    :disabled="isSubmitting"
                    required
                  />
                </span>
                <span v-else class="text-blue-400 text-base">
                  {{ (config.upgrade_required_points || 0).toLocaleString() }}
                </span>
              </td>
              <td class="p-2 text-center">
                <span v-if="editingConfig?.level === config.level">
                  <label class="flex items-center justify-center">
                    <input
                      v-model="editingConfig.enable_login_announcement"
                      type="checkbox"
                      :disabled="isSubmitting"
                      class="mr-1"
                    />
                    <span class="text-sm">启用</span>
                  </label>
                </span>
                <span
                  v-else
                  :class="config.enable_login_announcement ? 'text-green-400' : 'text-gray-500'"
                  class="text-base"
                >
                  {{ config.enable_login_announcement ? '已启用' : '已禁用' }}
                </span>
              </td>
              <td class="p-2 text-center">
                <div
                  v-if="editingConfig?.level === config.level"
                  class="flex justify-center space-x-1"
                >
                  <button
                    @click="saveEdit"
                    :disabled="isSubmitting"
                    class="text-green-400 hover:text-green-300 disabled:opacity-50 px-2 py-1 text-base"
                    title="保存"
                  >
                    <i class="fas fa-check"></i>
                  </button>
                  <button
                    @click="cancelEdit"
                    :disabled="isSubmitting"
                    class="text-gray-400 hover:text-gray-300 disabled:opacity-50 px-2 py-1 text-base"
                    title="取消"
                  >
                    <i class="fas fa-times"></i>
                  </button>
                </div>
                <div v-else class="flex justify-center space-x-1">
                  <button
                    @click="startEdit(config)"
                    class="text-blue-400 hover:text-blue-300 px-2 py-1 text-base"
                    title="编辑"
                  >
                    <i class="fas fa-edit"></i>
                  </button>
                  <button
                    @click="deleteConfig(config)"
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { vipApi } from '../../api/services/vipApi.js'
import { giftsApi } from '../../api/services/giftsApi.js'

// 响应式数据
const vipConfigs = ref([])
const giftsList = ref([])
const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const isSubmitting = ref(false)
const editingConfig = ref(null)

// 新VIP配置数据
const newVipData = ref({
  level: 0,
  name: '',
  daily_gift_id: '',
  upgrade_required_points: 0,
  enable_login_announcement: false,
})

// 加载礼包列表
const loadGiftsList = async () => {
  try {
    const response = await giftsApi.getAllGifts()
    if (response.success) {
      console.log('[DEBUG] 礼包列表API响应:', response)
      console.log('[DEBUG] 礼包列表数据:', response.data)
      // API返回的数据结构是 {gifts: Array}
      giftsList.value = response.data.gifts || []
      console.log('[DEBUG] 设置礼包列表:', giftsList.value)
    }
  } catch (error) {
    console.error('加载礼包列表失败:', error)
    // 不显示错误，因为这不是关键功能
  }
}

// 加载VIP配置列表
const loadVipConfigs = async () => {
  try {
    loading.value = true
    errorMessage.value = ''

    const response = await vipApi.getAllVipConfigs()
    if (response.success) {
      console.log('[DEBUG] VIP配置API响应:', response)
      console.log('[DEBUG] VIP配置数据:', response.data)
      // API返回的数据结构是 {configs: Array, total_count: number}
      vipConfigs.value = response.data.configs || []
    } else {
      errorMessage.value = response.message
    }
  } catch (error) {
    console.error('加载VIP配置失败:', error)
    errorMessage.value = error.message || '加载VIP配置失败'
  } finally {
    loading.value = false
  }
}

// 添加VIP配置
const addVipConfig = async () => {
  try {
    isSubmitting.value = true
    errorMessage.value = ''

    const configData = {
      ...newVipData.value,
      daily_gift_id: newVipData.value.daily_gift_id || null,
    }

    const response = await vipApi.createVipConfig(configData)
    if (response.success) {
      successMessage.value = 'VIP配置创建成功'
      // 重置表单
      newVipData.value = {
        level: 0,
        name: '',
        daily_gift_id: '',
        upgrade_required_points: 0,
        enable_login_announcement: false,
      }
      await loadVipConfigs()
    } else {
      errorMessage.value = response.message
    }
  } catch (error) {
    console.error('创建VIP配置失败:', error)
    errorMessage.value = error.message || '创建VIP配置失败'
  } finally {
    isSubmitting.value = false
  }
}

// 开始编辑
const startEdit = (config) => {
  editingConfig.value = {
    level: config.level,
    name: config.name || '',
    daily_gift_id: config.daily_gift_id || '',
    upgrade_required_points: config.upgrade_required_points || 0,
    enable_login_announcement: config.enable_login_announcement || false,
  }
}

// 保存编辑
const saveEdit = async () => {
  try {
    isSubmitting.value = true
    errorMessage.value = ''

    const configData = {
      ...editingConfig.value,
      daily_gift_id: editingConfig.value.daily_gift_id || null,
    }

    const response = await vipApi.updateVipConfig(editingConfig.value.level, configData)
    if (response.success) {
      successMessage.value = 'VIP配置更新成功'
      editingConfig.value = null
      await loadVipConfigs()
    } else {
      errorMessage.value = response.message
    }
  } catch (error) {
    console.error('更新VIP配置失败:', error)
    errorMessage.value = error.message || '更新VIP配置失败'
  } finally {
    isSubmitting.value = false
  }
}

// 取消编辑
const cancelEdit = () => {
  editingConfig.value = null
  isSubmitting.value = false
}

// 根据礼包ID获取礼包名称
const getGiftNameById = (giftId) => {
  if (!giftId) return '未设置'
  const gift = giftsList.value.find((g) => g.id == giftId)
  return gift ? gift.name : `礼包ID: ${giftId}`
}

// 删除配置
const deleteConfig = async (config) => {
  if (!confirm(`确定要删除VIP${config.level}配置吗？`)) {
    return
  }

  try {
    errorMessage.value = ''
    const response = await vipApi.deleteVipConfig(config.level)

    if (response.success) {
      successMessage.value = 'VIP配置删除成功'
      await loadVipConfigs()
    } else {
      errorMessage.value = response.message
    }
  } catch (error) {
    console.error('删除VIP配置失败:', error)
    errorMessage.value = error.message || '删除VIP配置失败'
  }
}

// 页面加载时获取数据
onMounted(() => {
  loadVipConfigs()
  loadGiftsList()
})
</script>
