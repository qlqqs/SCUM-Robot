<template>
  <teleport to="body">
    <div v-if="show" class="fixed inset-0 flex items-center justify-center z-[9999]">
      <!-- 背景遮罩 -->
      <div class="absolute inset-0 bg-gray-800/60 backdrop-blur-md" @click="$emit('close')"></div>

      <!-- 模态框内容 -->
      <div
        class="bg-gray-800 bg-opacity-50 backdrop-blur-md rounded-lg shadow-2xl border border-gray-600 p-8 w-full max-w-4xl mx-4 transform transition-all duration-300 max-h-[90vh] overflow-y-auto relative z-10"
        :class="modalAnimationClass"
        @click.stop
      >
        <!-- 模态框头部 -->
        <div class="flex items-center justify-between mb-6 border-b border-gray-600 pb-4">
          <h3 class="text-xl font-bold text-white">
            {{ isEditing ? '编辑礼包' : '创建礼包' }}
          </h3>
          <button @click="$emit('close')" class="text-gray-400 hover:text-white transition-colors">
            <i class="fas fa-times text-xl"></i>
          </button>
        </div>

        <!-- 模态框内容 -->
        <form @submit.prevent="handleSubmit" class="space-y-6">
          <!-- 基础信息 -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-2">
                礼包名称 <span class="text-red-400">*</span>
              </label>
              <input
                v-model="formData.name"
                type="text"
                required
                class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="请输入礼包名称"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-300 mb-2">
                礼包类型 <span class="text-red-400">*</span>
              </label>
              <select
                v-model="formData.gift_type"
                required
                @change="handleTypeChange"
                class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">请选择礼包类型</option>
                <option value="one_time">一次性礼包</option>
                <option value="daily">每日礼包</option>
                <option value="limited_quantity">限量礼包</option>
                <option value="limited_time">限时礼包</option>
                <option value="limited_time_quantity">限时限量礼包</option>
              </select>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-300 mb-2"> 礼包描述 </label>
            <textarea
              v-model="formData.description"
              rows="3"
              class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="请输入礼包描述"
            ></textarea>
          </div>

          <!-- 礼包图片 -->
          <div class="md:col-span-2">
            <label class="block text-sm font-medium text-gray-300 mb-2"> 礼包图片 </label>

            <!-- 图片上传控件 - 横向铺满 -->
            <div class="w-full">
              <input
                ref="imageFileInput"
                type="file"
                accept="image/jpeg,image/jpg,image/png,image/gif,image/webp,image/bmp"
                @change="handleImageSelect"
                class="hidden"
              />

              <!-- 上传按钮和状态显示 -->
              <div
                class="w-full bg-gray-700 border border-gray-600 rounded-md p-4 flex items-center justify-between"
              >
                <div class="flex items-center gap-3">
                  <button
                    type="button"
                    @click="$refs.imageFileInput?.click()"
                    :disabled="isSubmitting || isUploadingImage"
                    class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <i class="fas fa-upload mr-2"></i>
                    {{ imageFile || formData.image_url ? '更换图片' : '选择图片' }}
                  </button>

                  <!-- 图片状态文字 -->
                  <div class="text-sm text-gray-300">
                    <span v-if="isUploadingImage" class="text-blue-400">
                      <i class="fas fa-spinner fa-spin mr-2"></i>
                      上传中...
                    </span>
                    <span v-else-if="imageFile">
                      已选择: {{ imageFile.name }} ({{ (imageFile.size / 1024).toFixed(1) }}KB)
                    </span>
                    <span v-else-if="formData.image_url">
                      当前图片: {{ formData.image_url.split('/').pop() }}
                    </span>
                    <span v-else class="text-gray-400"> 未选择图片 </span>
                  </div>
                </div>

                <!-- 删除按钮 -->
                <button
                  v-if="imageFile || formData.image_url"
                  type="button"
                  @click="removeImage"
                  class="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 transition-colors text-sm"
                  title="删除图片"
                >
                  <i class="fas fa-times mr-1"></i>
                  删除
                </button>
              </div>

              <!-- 图片格式说明 -->
              <div class="mt-2 text-xs text-gray-400">
                支持 JPG、PNG、GIF、WebP、BMP 格式，最大 5MB
              </div>
            </div>
          </div>

          <!-- 物品配置 -->
          <div class="md:col-span-2">
            <label for="item-code" class="block text-sm font-medium mb-1 text-white">
              物品代码 <span class="text-red-400">*</span>
            </label>
            <textarea
              v-model="formData.itemCode"
              id="item-code"
              rows="3"
              :disabled="isSubmitting"
              class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 font-mono text-white"
              required
              placeholder="输入游戏内物品代码（#命令 物品 数量格式）
单个物品：#spawnitem Weapon_AK47 1
多个物品：#spawnitem Weapon_AK47 1
         #spawnitem Magazine_AK47 3
         #spawnitem Cal_7_62x39mm_Ammobox 3"
            ></textarea>

            <!-- 物品代码预览 -->
            <div
              v-if="formData.itemCode && formData.itemCode.trim()"
              class="mt-2 p-3 bg-gray-800 rounded-md border border-gray-600"
            >
              <div class="text-xs text-white mb-1">JSON格式预览：</div>
              <pre class="text-xs text-green-400 font-mono whitespace-pre-wrap">{{
                itemCodePreview
              }}</pre>
            </div>
          </div>

          <!-- 配置选项 -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-2"> 最大领取次数 </label>
              <input
                v-model.number="formData.max_claims"
                type="number"
                min="-1"
                class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="-1表示无限制"
              />
              <p class="text-xs text-gray-400 mt-1">-1表示无限制</p>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-300 mb-2"> 冷却时间（小时） </label>
              <input
                v-model.number="formData.cooldown_hours"
                type="number"
                min="0"
                :disabled="!isCooldownEditable"
                class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                placeholder="0表示无冷却"
              />
              <p class="text-xs text-gray-400 mt-1">
                <span v-if="formData.gift_type === 'daily'">每日礼包固定24小时冷却时间</span>
                <span v-else-if="!isCooldownEditable">此类型礼包不需要冷却时间</span>
                <span v-else>0表示无冷却时间</span>
              </p>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-300 mb-2"> 所需等级 </label>
              <input
                v-model.number="formData.required_level"
                type="number"
                min="0"
                class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="0表示无等级要求"
              />
            </div>
          </div>

          <!-- 限量配置 -->
          <div
            v-if="showQuantityConfig"
            class="bg-gray-700/50 p-4 rounded-lg border border-gray-600"
          >
            <h4 class="text-lg font-medium text-white mb-4">限量配置</h4>
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-2">
                总数量 <span class="text-red-400">*</span>
              </label>
              <input
                v-model.number="formData.total_quantity"
                type="number"
                min="1"
                required
                class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="请输入总数量"
              />
            </div>
          </div>

          <!-- 限时配置 -->
          <div v-if="showTimeConfig" class="bg-gray-700/50 p-4 rounded-lg border border-gray-600">
            <h4 class="text-lg font-medium text-white mb-4">限时配置</h4>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">
                  开始时间 <span class="text-red-400">*</span>
                </label>
                <input
                  v-model="formData.start_time"
                  type="datetime-local"
                  required
                  class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">
                  结束时间 <span class="text-red-400">*</span>
                </label>
                <input
                  v-model="formData.end_time"
                  type="datetime-local"
                  required
                  class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          <!-- 按钮组 -->
          <div class="flex justify-end gap-3 pt-4 border-t border-gray-700">
            <button
              type="button"
              @click="$emit('close')"
              class="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              :disabled="isSubmitting"
              class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              <i v-if="isSubmitting" class="fas fa-spinner fa-spin mr-2"></i>
              {{ isSubmitting ? '保存中...' : isEditing ? '更新' : '创建' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { giftsApi } from '@/api/services/giftsApi.js'

const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
  gift: {
    type: Object,
    default: null,
  },
  isEditing: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close', 'save'])

// 响应式数据
const isSubmitting = ref(false)

const formData = ref({
  name: '',
  description: '',
  gift_type: '',
  items_config: {},
  itemCode: '',
  is_active: true,
  max_claims: 1,
  cooldown_hours: 0,
  required_level: 0,
  total_quantity: null,
  start_time: '',
  end_time: '',
  image_url: '',
})

// 图片上传相关状态
const imageFile = ref(null)
const imagePreviewUrl = ref('')
const isUploadingImage = ref(false)

// 计算属性
const showQuantityConfig = computed(() => {
  return ['limited_quantity', 'limited_time_quantity'].includes(formData.value.gift_type)
})

const showTimeConfig = computed(() => {
  return ['limited_time', 'limited_time_quantity'].includes(formData.value.gift_type)
})

// 冷却时间是否可编辑
const isCooldownEditable = computed(() => {
  // 一次性礼包、每日礼包、限量礼包和限时限量礼包不需要冷却时间编辑
  return !['one_time', 'daily', 'limited_quantity', 'limited_time_quantity'].includes(
    formData.value.gift_type,
  )
})

// 动画相关
const modalAnimationClass = computed(() => {
  return props.show ? 'scale-100 opacity-100' : 'scale-95 opacity-0'
})

// 物品代码预览
const itemCodePreview = computed(() => {
  if (!formData.value.itemCode || !formData.value.itemCode.trim()) return ''

  try {
    const itemsConfig = parseItemCode(formData.value.itemCode)
    return JSON.stringify(itemsConfig, null, 2)
  } catch {
    return '格式错误：请使用 #命令 物品 数量 格式'
  }
})

// 解析物品代码
const parseItemCode = (itemCode) => {
  if (!itemCode || !itemCode.trim()) {
    return []
  }

  const lines = itemCode
    .trim()
    .split('\n')
    .filter((line) => line.trim())

  if (lines.length === 0) {
    return []
  }

  const commands = []

  for (const line of lines) {
    const trimmedLine = line.trim()

    if (trimmedLine.startsWith('#')) {
      // 解析命令格式：#命令 物品 数量
      const parts = trimmedLine.split(/\s+/)
      if (parts.length >= 2) {
        const command = parts[0] // #命令
        const item = parts[1] // 物品名称
        const amount = parts.length >= 3 ? parseInt(parts[2]) || 1 : 1 // 数量，默认为1

        commands.push({
          command: command,
          item: item,
          amount: amount,
        })
      } else {
        throw new Error(`命令格式错误: ${trimmedLine}`)
      }
    } else {
      throw new Error(`不支持的格式: ${trimmedLine}，请使用 #命令 物品 数量 格式`)
    }
  }

  // 返回数组格式
  return commands
}

// 监听器
watch(
  () => props.show,
  (newVal) => {
    if (newVal) {
      resetForm()
      if (props.isEditing && props.gift) {
        loadGiftData()
      }
    }
  },
)

// 方法
const resetForm = () => {
  formData.value = {
    name: '',
    description: '',
    gift_type: '',
    items_config: {},
    itemCode: '',
    is_active: true,
    max_claims: 1,
    cooldown_hours: 0,
    required_level: 0,
    total_quantity: null,
    start_time: '',
    end_time: '',
    image_url: '',
  }
}

const loadGiftData = () => {
  const gift = props.gift

  // 如果没有礼包数据，直接返回
  if (!gift) {
    return
  }

  formData.value = {
    name: gift.name || '',
    description: gift.description || '',
    gift_type: gift.gift_type || '',
    is_active: gift.is_active !== false,
    max_claims: gift.max_claims || 1,
    cooldown_hours: gift.cooldown_hours || 0,
    required_level: gift.required_level || 0,
    total_quantity: gift.total_quantity || null,
    start_time: gift.start_time ? formatDateTimeLocal(gift.start_time) : '',
    end_time: gift.end_time ? formatDateTimeLocal(gift.end_time) : '',
    image_url: gift.image_url || '',
  }

  // 清理图片上传状态
  imageFile.value = null
  imagePreviewUrl.value = ''

  // 加载物品配置
  if (gift.items_config) {
    let itemCodeLines = []

    if (gift.items_config.items && Array.isArray(gift.items_config.items)) {
      // 新格式：{ items: [...] } - 数组格式，显示完整命令
      itemCodeLines = gift.items_config.items
        .map((item) => {
          if (item.command && item.item) {
            const amount = item.amount || 1
            return `${item.command} ${item.item} ${amount}`
          }
          return ''
        })
        .filter((line) => line)
    } else if (Array.isArray(gift.items_config)) {
      // 数组格式：[...] - 显示完整命令
      itemCodeLines = gift.items_config
        .map((item) => {
          if (item.command && item.item) {
            const amount = item.amount || 1
            return `${item.command} ${item.item} ${amount}`
          }
          return ''
        })
        .filter((line) => line)
    } else if (typeof gift.items_config === 'object') {
      // 字典格式：{"item_name": quantity} - 转换为命令格式
      itemCodeLines = Object.entries(gift.items_config).map(([itemName, quantity]) => {
        return `#spawnitem ${itemName} ${quantity || 1}`
      })
    }

    formData.value.itemCode = itemCodeLines.join('\n')
  }
}

const handleTypeChange = () => {
  // 根据类型设置默认值
  switch (formData.value.gift_type) {
    case 'one_time':
      formData.value.max_claims = 1
      formData.value.cooldown_hours = 0
      break
    case 'daily':
      formData.value.max_claims = -1
      formData.value.cooldown_hours = 24
      break
    case 'limited_quantity':
      formData.value.max_claims = 1
      formData.value.cooldown_hours = 0
      if (!formData.value.total_quantity) {
        formData.value.total_quantity = 100
      }
      break
    case 'limited_time':
      formData.value.max_claims = 3
      formData.value.cooldown_hours = 8
      break
    case 'limited_time_quantity':
      formData.value.max_claims = 1
      formData.value.cooldown_hours = 0
      if (!formData.value.total_quantity) {
        formData.value.total_quantity = 50
      }
      break
  }
}

const buildItemsConfig = () => {
  try {
    const parsed = parseItemCode(formData.value.itemCode)

    // 将命令格式转换为后端期望的字典格式 {"item_name": quantity}
    if (!parsed || !Array.isArray(parsed)) return {}

    const itemsConfig = {}

    // 处理数组格式的命令
    parsed.forEach((cmd) => {
      if (cmd.command === '#spawnitem' && cmd.item) {
        itemsConfig[cmd.item] = (itemsConfig[cmd.item] || 0) + (cmd.amount || 1)
      }
    })

    return itemsConfig
  } catch (error) {
    console.error('解析物品代码失败:', error)
    return {}
  }
}

// 图片处理函数
const handleImageSelect = (event) => {
  const file = event.target.files?.[0]
  if (!file) return

  // 验证文件类型
  const allowedTypes = [
    'image/jpeg',
    'image/jpg',
    'image/png',
    'image/gif',
    'image/webp',
    'image/bmp',
  ]
  if (!allowedTypes.includes(file.type)) {
    alert('不支持的文件格式，请上传 JPG、PNG、GIF、WebP 或 BMP 格式的图片')
    return
  }

  // 验证文件大小 (5MB)
  const maxSize = 5 * 1024 * 1024
  if (file.size > maxSize) {
    alert('文件大小不能超过5MB')
    return
  }

  // 存储文件并创建预览URL
  imageFile.value = file
  imagePreviewUrl.value = URL.createObjectURL(file)
}

const removeImage = () => {
  imageFile.value = null
  imagePreviewUrl.value = ''
  formData.value.image_url = ''

  // 清空文件输入框
  const fileInput = document.querySelector('input[type="file"]')
  if (fileInput) {
    fileInput.value = ''
  }
}

const validateForm = () => {
  // 基础验证
  if (!formData.value.name.trim()) {
    alert('请输入礼包名称')
    return false
  }

  if (!formData.value.gift_type) {
    alert('请选择礼包类型')
    return false
  }

  // 物品配置验证
  const itemsConfig = buildItemsConfig()
  if (Object.keys(itemsConfig).length === 0) {
    alert('请至少配置一个物品')
    return false
  }

  // 使用API的验证方法
  const giftData = {
    ...formData.value,
    items_config: itemsConfig,
  }

  const validation = giftsApi.validateGiftConfig(giftData)
  if (!validation.isValid) {
    alert('配置验证失败：\n' + validation.errors.join('\n'))
    return false
  }

  return true
}

const handleSubmit = async () => {
  if (!validateForm()) return

  isSubmitting.value = true
  try {
    const submitData = {
      ...formData.value,
      items_config: buildItemsConfig(),
    }

    // 清理不需要的字段
    if (!showQuantityConfig.value) {
      delete submitData.total_quantity
    }
    if (!showTimeConfig.value) {
      delete submitData.start_time
      delete submitData.end_time
    }

    // 清理图片相关字段，因为图片上传是单独处理的
    delete submitData.itemCode

    emit('save', submitData, imageFile.value)
  } catch (error) {
    console.error('[GiftModal] Submit failed:', error)
  } finally {
    isSubmitting.value = false
  }
}

const formatDateTimeLocal = (dateTime) => {
  if (!dateTime) return ''
  const date = new Date(dateTime)
  return date.toISOString().slice(0, 16)
}
</script>
