<template>
  <div>
    <div
      class="flex flex-col xl:flex-row xl:flex-wrap xl:justify-between xl:items-start mb-6 gap-4"
    >
      <div class="flex-shrink-0">
        <h2 class="text-lg sm:text-xl lg:text-2xl font-bold">{{ currentCategoryName }}</h2>
        <p class="text-xs sm:text-sm text-gray-400 mt-1 break-words">
          配置项数量: {{ totalSettings }} | 加载状态:
          {{ settingsStore.loading.settings ? '加载中' : '已完成' }}
        </p>
      </div>
      <div
        class="flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center gap-2 sm:gap-3 xl:flex-shrink-0 xl:min-w-0 max-w-full overflow-hidden"
      >
        <!-- 搜索框 -->
        <div
          class="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3 sm:flex-1 sm:min-w-[200px]"
        >
          <div class="relative">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索设置项..."
              class="bg-gray-700 border border-gray-600 rounded-md py-2 pl-8 pr-3 focus:outline-none focus:ring-2 focus:ring-blue-500 w-full sm:w-40 text-sm"
              @input="handleSearch"
            />
            <i
              class="fas fa-search absolute left-2 top-1/2 transform -translate-y-1/2 text-gray-400 text-sm"
            ></i>
          </div>
        </div>

        <!-- 按钮盒子 -->
        <div
          class="flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center gap-2 sm:gap-3 sm:min-w-[340px]"
        >
          <!-- 刷新按钮 -->
          <button
            @click="refreshData"
            :disabled="settingsStore.loading.settings"
            class="w-full sm:w-auto sm:min-w-[70px] bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-3 py-2 rounded transition-colors text-xs font-medium"
          >
            <i
              class="fas fa-sync-alt mr-1"
              :class="{ 'animate-spin': settingsStore.loading.settings }"
            ></i>
            <span>刷新</span>
          </button>

          <!-- 保存按钮 -->
          <button
            @click="saveAllChanges"
            :disabled="!hasChanges || settingsStore.loading.updating"
            class="w-full sm:w-auto sm:min-w-[70px] bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white px-3 py-2 rounded transition-colors text-xs font-medium"
          >
            <i
              class="fas fa-save mr-1"
              :class="{ 'animate-spin': settingsStore.loading.updating }"
            ></i>
            <span>{{ settingsStore.loading.updating ? '保存中' : '保存' }}</span>
          </button>

          <!-- 重置按钮 -->
          <div class="relative">
            <button
              @click="showResetDropdown = !showResetDropdown"
              class="w-full sm:w-auto sm:min-w-[70px] bg-yellow-600 hover:bg-yellow-700 text-white px-3 py-2 rounded transition-colors flex items-center text-xs font-medium"
            >
              <i class="fas fa-undo mr-1"></i>
              <span>重置</span>
              <i
                class="fas fa-chevron-down ml-1 text-xs"
                :class="{ 'rotate-180': showResetDropdown }"
              ></i>
            </button>

            <!-- 重置下拉菜单 -->
            <div
              v-if="showResetDropdown"
              class="absolute right-0 mt-1 w-full bg-gray-700 border border-gray-600 rounded-md shadow-lg z-50"
            >
              <button
                @click="resetCurrentCategory"
                :disabled="settingsStore.loading.resetting"
                class="w-full text-left px-4 py-2 text-sm text-white hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                <i class="fas fa-undo mr-2 text-yellow-400"></i>
                重置{{ currentCategoryName }}
              </button>
              <button
                @click="resetAllSettings"
                :disabled="settingsStore.loading.resetting"
                class="w-full text-left px-4 py-2 text-sm text-white hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                <i class="fas fa-exclamation-triangle mr-2 text-red-400"></i>
                重置所有设置
              </button>
              <hr class="border-gray-600 my-1" />
              <button
                @click="showResetDropdown = false"
                class="w-full text-left px-4 py-2 text-sm text-white hover:bg-gray-600 flex items-center"
              >
                <i class="fas fa-times mr-2 text-gray-400"></i>
                关闭菜单
              </button>
            </div>

            <!-- 点击外部关闭下拉菜单 -->
            <div
              v-if="showResetDropdown"
              @click="showResetDropdown = false"
              class="fixed inset-0 z-40"
            ></div>
          </div>

          <!-- 导出按钮 -->
          <button
            @click="exportSettings"
            class="w-full sm:w-auto sm:min-w-[70px] bg-purple-600 hover:bg-purple-700 text-white px-3 py-2 rounded transition-colors text-xs font-medium"
          >
            <i class="fas fa-download mr-1"></i>
            <span>导出</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 错误提示 -->
    <div
      v-if="settingsStore.errors.settings"
      class="mb-6 p-4 bg-red-900/50 border border-red-500 rounded-lg"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center">
          <i class="fas fa-exclamation-triangle text-red-400 mr-2"></i>
          <span class="text-red-200">{{ settingsStore.errors.settings }}</span>
        </div>
        <button
          @click="settingsStore.clearError('settings')"
          class="text-red-400 hover:text-red-300"
        >
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
      <div
        v-if="settingsStore.loading.settings && displayedSettings.length === 0"
        class="text-center py-8"
      >
        <i class="fas fa-spinner fa-spin text-2xl text-gray-400 mb-2"></i>
        <p class="text-gray-400">加载系统设置中...</p>
      </div>

      <!-- 空状态 -->
      <div
        v-else-if="!settingsStore.loading.settings && displayedSettings.length === 0"
        class="text-center py-8"
      >
        <i class="fas fa-cogs text-4xl text-gray-500 mb-4"></i>
        <p class="text-gray-400 mb-4">
          {{ searchQuery || selectedCategoryId ? '没有找到匹配的设置项' : '暂无系统设置' }}
        </p>
        <p class="text-sm text-gray-500">
          {{
            searchQuery || selectedCategoryId ? '尝试调整搜索条件' : '请联系管理员初始化系统设置'
          }}
        </p>
      </div>

      <!-- 设置列表 -->
      <div v-else class="space-y-1">
        <!-- 设置项列表 -->
        <div class="bg-gray-800 rounded-lg overflow-hidden border border-gray-700">
          <div
            v-for="setting in displayedSettings"
            :key="setting.key"
            class="border-b border-gray-700 last:border-b-0"
          >
            <div class="p-4 hover:bg-gray-850 transition-colors duration-200">
              <div class="flex items-start justify-between">
                <!-- 左侧：设置信息 -->
                <div class="flex-1 min-w-0 mr-6">
                  <div class="flex items-center flex-wrap gap-2 mb-2">
                    <label :for="setting.key" class="text-base font-medium text-white">
                      {{ setting.name }}
                      <span v-if="setting.validation?.required" class="text-red-400 ml-1">*</span>
                    </label>
                    <div v-if="changedSettings.has(setting.key)">
                      <span
                        class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-900/50 text-yellow-300 border border-yellow-700"
                      >
                        <i class="fas fa-edit mr-1 text-xs"></i>
                        已修改
                      </span>
                    </div>
                  </div>
                  <p class="text-sm text-gray-400">{{ setting.description }}</p>
                </div>

                <!-- 右侧：输入控件 -->
                <div class="flex-shrink-0 w-80">
                  <div class="setting-input">
                    <!-- 布尔值 -->
                    <div v-if="setting.type === 'boolean'" class="flex items-center justify-end">
                      <label class="relative inline-flex items-center cursor-pointer">
                        <input
                          :id="setting.key"
                          v-model="localSettings[setting.key]"
                          type="checkbox"
                          class="sr-only peer"
                          @change="markAsChanged(setting.key)"
                        />
                        <div
                          class="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"
                        ></div>
                        <span class="ml-3 text-sm font-medium text-gray-300">
                          {{ localSettings[setting.key] ? '启用' : '禁用' }}
                        </span>
                      </label>
                    </div>

                    <!-- 选择框 -->
                    <select
                      v-else-if="setting.type === 'select'"
                      :id="setting.key"
                      v-model="localSettings[setting.key]"
                      class="w-full bg-gray-700 border border-gray-600 rounded-lg py-3 px-4 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                      @change="markAsChanged(setting.key)"
                    >
                      <option
                        v-for="option in setting.options"
                        :key="option.value"
                        :value="option.value"
                      >
                        {{ option.label }}
                      </option>
                    </select>

                    <!-- 多行文本 -->
                    <textarea
                      v-else-if="setting.type === 'textarea'"
                      :id="setting.key"
                      v-model="localSettings[setting.key]"
                      rows="3"
                      class="w-full bg-gray-700 border border-gray-600 rounded-lg py-3 px-4 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors resize-none"
                      :placeholder="setting.default_value"
                      @input="markAsChanged(setting.key)"
                    ></textarea>

                    <!-- 数字输入 -->
                    <div v-else-if="setting.type === 'number'" class="relative">
                      <input
                        :id="setting.key"
                        v-model.number="localSettings[setting.key]"
                        type="number"
                        :min="setting.validation?.min"
                        :max="setting.validation?.max"
                        class="w-full bg-gray-700 border border-gray-600 rounded-lg py-3 px-4 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                        :placeholder="setting.default_value?.toString()"
                        @input="markAsChanged(setting.key)"
                      />
                      <div
                        v-if="
                          setting.validation?.min !== undefined ||
                          setting.validation?.max !== undefined
                        "
                        class="absolute right-3 top-1/2 transform -translate-y-1/2 text-xs text-gray-400"
                      >
                        {{ setting.validation?.min }}-{{ setting.validation?.max }}
                      </div>
                    </div>

                    <!-- 密码输入 -->
                    <div v-else-if="setting.type === 'password'" class="relative">
                      <input
                        :id="setting.key"
                        v-model="localSettings[setting.key]"
                        :type="showPasswords[setting.key] ? 'text' : 'password'"
                        class="w-full bg-gray-700 border border-gray-600 rounded-lg py-3 px-4 pr-12 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                        :placeholder="setting.default_value"
                        @input="markAsChanged(setting.key)"
                      />
                      <button
                        type="button"
                        @click="togglePasswordVisibility(setting.key)"
                        class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-300 transition-colors p-1"
                      >
                        <i
                          :class="showPasswords[setting.key] ? 'fas fa-eye-slash' : 'fas fa-eye'"
                        ></i>
                      </button>
                    </div>

                    <!-- 默认文本输入 -->
                    <input
                      v-else
                      :id="setting.key"
                      v-model="localSettings[setting.key]"
                      type="text"
                      class="w-full bg-gray-700 border border-gray-600 rounded-lg py-3 px-4 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                      :placeholder="setting.default_value"
                      @input="markAsChanged(setting.key)"
                    />
                  </div>

                  <!-- 验证错误提示 -->
                  <div
                    v-if="validationErrors[setting.key]"
                    class="mt-2 text-xs text-red-400 flex items-center"
                  >
                    <i class="fas fa-exclamation-triangle mr-1"></i>
                    {{ validationErrors[setting.key] }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useSettingsStore, SETTING_CATEGORIES } from '@/stores/settingsStore.js'

const route = useRoute()
const settingsStore = useSettingsStore()

// 简单的前端验证函数
const validateSetting = (key, value) => {
  // 基本类型验证
  if (value === null || value === undefined || value === '') {
    return { valid: false, error: '值不能为空' }
  }

  // 根据设置类型进行验证
  const setting = settingsStore.settings[key]
  if (!setting) {
    return { valid: true }
  }

  // 数字类型验证
  if (setting.type === 'number') {
    const num = Number(value)
    if (isNaN(num)) {
      return { valid: false, error: '必须是有效的数字' }
    }
    if (setting.min !== undefined && num < setting.min) {
      return { valid: false, error: `不能小于 ${setting.min}` }
    }
    if (setting.max !== undefined && num > setting.max) {
      return { valid: false, error: `不能大于 ${setting.max}` }
    }
  }

  // 布尔类型验证
  if (setting.type === 'boolean') {
    if (typeof value !== 'boolean') {
      return { valid: false, error: '必须是布尔值' }
    }
  }

  // 字符串类型验证
  if (setting.type === 'string') {
    if (typeof value !== 'string') {
      return { valid: false, error: '必须是字符串' }
    }
    if (setting.minLength && value.length < setting.minLength) {
      return { valid: false, error: `长度不能小于 ${setting.minLength}` }
    }
    if (setting.maxLength && value.length > setting.maxLength) {
      return { valid: false, error: `长度不能大于 ${setting.maxLength}` }
    }
  }

  return { valid: true }
}

// 响应式数据
const searchQuery = ref('')
const successMessage = ref('')
const showResetDropdown = ref(false)

// 本地设置副本（用于编辑）
const localSettings = reactive({})
const changedSettings = ref(new Set())
const validationErrors = reactive({})
const showPasswords = reactive({})

// 分类数据
const categories = computed(() => Object.values(SETTING_CATEGORIES))

// 当前分类ID（从路由获取）
const currentCategoryId = computed(() => route.meta?.category || 'system')

// 当前分类信息
const currentCategory = computed(() => {
  return categories.value.find((cat) => cat.id === currentCategoryId.value) || categories.value[0]
})

// 当前分类名称
const currentCategoryName = computed(() => currentCategory.value?.name || '系统设置')

// 总设置数量（当前分类的设置数量）
const totalSettings = computed(() => {
  return Object.values(settingsStore.settings).filter(
    (setting) => setting.category === currentCategoryId.value,
  ).length
})

// 是否有未保存的更改
const hasChanges = computed(() => changedSettings.value.size > 0)

// 过滤后的设置列表
const filteredSettings = computed(() => {
  let result = Object.values(settingsStore.settings)

  // 分类筛选（只显示当前分类的设置）
  result = result.filter((setting) => setting.category === currentCategoryId.value)

  // 搜索筛选
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase().trim()
    result = result.filter(
      (setting) =>
        setting.name.toLowerCase().includes(query) ||
        setting.description.toLowerCase().includes(query) ||
        setting.key.toLowerCase().includes(query),
    )
  }

  return result
})

// 显示的设置列表
const displayedSettings = computed(() => filteredSettings.value)

// 搜索处理
const handleSearch = () => {
  // 搜索逻辑已在 filteredSettings 计算属性中处理
}

// 标记设置为已更改
const markAsChanged = (key) => {
  changedSettings.value.add(key)
  // 清除该设置的验证错误
  delete validationErrors[key]

  // 实时验证
  const setting = settingsStore.settings[key]
  if (setting) {
    const validation = validateSetting(key, localSettings[key])
    if (!validation.valid) {
      validationErrors[key] = validation.error
    }
  }
}

// 切换密码可见性
const togglePasswordVisibility = (key) => {
  showPasswords[key] = !showPasswords[key]
}

// 初始化本地设置
const initializeLocalSettings = () => {
  Object.values(settingsStore.settings).forEach((setting) => {
    localSettings[setting.key] = setting.value ?? setting.default_value
  })
  changedSettings.value.clear()
}

// 刷新数据
const refreshData = async () => {
  try {
    await settingsStore.loadSettings()
    initializeLocalSettings()
    successMessage.value = '设置刷新成功'
    setTimeout(() => {
      successMessage.value = ''
    }, 3000)
  } catch (error) {
    console.error('[SystemSettings] Failed to refresh data:', error)
  }
}

// 保存所有更改
const saveAllChanges = async () => {
  if (!hasChanges.value) return

  // 验证所有更改的设置
  let hasValidationErrors = false
  const settingsToUpdate = {}

  changedSettings.value.forEach((key) => {
    const validation = validateSetting(key, localSettings[key])
    if (!validation.valid) {
      validationErrors[key] = validation.error
      hasValidationErrors = true
    } else {
      settingsToUpdate[key] = localSettings[key]
      delete validationErrors[key]
    }
  })

  if (hasValidationErrors) {
    return
  }

  try {
    await settingsStore.updateBatchSettings(settingsToUpdate)
    changedSettings.value.clear()
    successMessage.value = `成功保存 ${Object.keys(settingsToUpdate).length} 项设置`
    setTimeout(() => {
      successMessage.value = ''
    }, 3000)
  } catch (error) {
    console.error('[SystemSettings] Failed to save settings:', error)
  }
}

// 重置当前分类
const resetCurrentCategory = async () => {
  const categoryName = currentCategoryName.value

  if (!confirm(`确定要重置"${categoryName}"分类下的所有设置到默认值吗？\n\n此操作不可撤销！`)) {
    return
  }

  try {
    await settingsStore.resetCategorySettings(currentCategoryId.value)
    initializeLocalSettings()
    showResetDropdown.value = false
    successMessage.value = `${categoryName}设置重置成功`
    setTimeout(() => {
      successMessage.value = ''
    }, 3000)
  } catch (error) {
    console.error('[SystemSettings] Failed to reset category settings:', error)
  }
}

// 重置所有设置
const resetAllSettings = async () => {
  if (!confirm('确定要重置所有系统设置到默认值吗？\n\n此操作将清除所有自定义配置，不可撤销！')) {
    return
  }

  try {
    await settingsStore.resetAllSettings()
    initializeLocalSettings()
    showResetDropdown.value = false
    successMessage.value = '所有设置重置成功'
    setTimeout(() => {
      successMessage.value = ''
    }, 3000)
  } catch (error) {
    console.error('[SystemSettings] Failed to reset all settings:', error)
  }
}

// 导出设置
const exportSettings = async () => {
  try {
    const categories = [currentCategoryId.value]
    const response = await settingsStore.exportSettings({
      format: 'json',
      categories,
    })

    if (response.success && response.data) {
      // 创建下载链接
      const blob = new Blob([JSON.stringify(response.data, null, 2)], {
        type: 'application/json',
      })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `system-settings-${currentCategoryId.value}-${new Date().toISOString().split('T')[0]}.json`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)

      successMessage.value = '设置导出成功'
      setTimeout(() => {
        successMessage.value = ''
      }, 3000)
    }
  } catch (error) {
    console.error('[SystemSettings] Failed to export settings:', error)
  }
}

// 组件挂载时加载数据
onMounted(async () => {
  try {
    // 如果store中没有设置，则加载
    if (Object.keys(settingsStore.settings).length === 0) {
      await settingsStore.loadSettings()
    }
    initializeLocalSettings()
  } catch (error) {
    console.error('[SystemSettings] Failed to initialize:', error)
    // 如果API加载失败，显示错误信息
    // 不再使用本地默认设置，因为所有配置都应该从后端获取
    initializeLocalSettings()
  }
})
</script>
