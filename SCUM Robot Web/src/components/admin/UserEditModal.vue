<template>
  <teleport to="body">
    <div
      v-if="isVisible"
      class="fixed inset-0 flex backdrop-blur-sm items-center justify-center z-[9999]"
    >
      <div
        class="bg-gray-800 bg-opacity-50 backdrop-blur-md rounded-lg shadow-2xl border border-gray-600 p-8 w-full max-w-2xl mx-4 transform transition-all duration-300 max-h-[90vh] overflow-y-auto"
        :class="modalAnimationClass"
        @click.stop
      >
        <!-- 模态框标题 -->
        <div class="flex justify-between items-center mb-6">
          <h2 class="text-xl font-bold text-white">
            {{ isCreating ? '创建用户' : isEditing ? '编辑用户' : '查看用户' }}
          </h2>
          <button @click="closeModal" class="text-gray-400 hover:text-white transition-colors">
            <i class="fas fa-times text-xl"></i>
          </button>
        </div>

        <!-- 用户信息表单 -->
        <form @submit.prevent="saveUser" class="space-y-4">
          <!-- 基本信息 -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- 用户名 -->
            <div>
              <label for="username" class="block text-sm font-medium mb-1 text-white">
                用户名
              </label>
              <input
                v-model="form.username"
                id="username"
                type="text"
                :disabled="isSubmitting"
                class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 text-white"
                placeholder="请输入用户名"
                required
              />
            </div>

            <!-- 邮箱 -->
            <div>
              <label for="email" class="block text-sm font-medium mb-1 text-white">
                邮箱地址
              </label>
              <input
                v-model="form.email"
                id="email"
                type="email"
                :disabled="isSubmitting"
                class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 text-white"
                placeholder="请输入邮箱地址"
                required
              />
            </div>
          </div>

          <!-- SteamID和积分 -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- SteamID -->
            <div>
              <label for="steam_id" class="block text-sm font-medium mb-1 text-white">
                SteamID
              </label>
              <input
                v-model="form.steam_id"
                id="steam_id"
                type="text"
                :disabled="isSubmitting"
                :class="[
                  'w-full bg-gray-700 border rounded-md py-2 px-3 focus:outline-none focus:ring-2 disabled:opacity-50 text-white font-mono',
                  form.steam_id && !validateSteamId(form.steam_id)
                    ? 'border-red-500 focus:ring-red-500'
                    : 'border-gray-600 focus:ring-blue-500',
                ]"
                placeholder="请输入17位Steam ID64（以7656开头）"
              />
              <p
                v-if="form.steam_id && !validateSteamId(form.steam_id)"
                class="text-red-400 text-xs mt-1"
              >
                Steam ID格式不正确，应为17位数字且以7656开头
              </p>
              <p v-else-if="form.steam_id" class="text-green-400 text-xs mt-1">Steam ID格式正确</p>
            </div>

            <!-- 积分 -->
            <div>
              <label for="points" class="block text-sm font-medium mb-1 text-white"> 积分 </label>
              <input
                v-model.number="form.points"
                id="points"
                type="number"
                min="0"
                :disabled="isSubmitting"
                class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 text-white"
                placeholder="请输入积分数量"
              />
            </div>
          </div>

          <!-- 权限设置 -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- 用户类型 -->
            <div>
              <label for="user_type" class="block text-sm font-medium mb-1 text-white">
                用户类型
              </label>
              <select
                v-model="form.user_type"
                id="user_type"
                :disabled="isSubmitting"
                class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 text-white"
              >
                <option value="user">普通用户</option>
                <option value="admin">管理员</option>
                <option value="super_admin">超级管理员</option>
              </select>
            </div>

            <!-- 账户状态 -->
            <div>
              <label for="is_active" class="block text-sm font-medium mb-1 text-white">
                账户状态
              </label>
              <select
                v-model="form.is_active"
                id="is_active"
                :disabled="isSubmitting"
                class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 text-white"
              >
                <option :value="true">激活</option>
                <option :value="false">未激活</option>
              </select>
            </div>
          </div>

          <!-- 密码和资产管理 -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- 密码 -->
            <div>
              <label for="password" class="block text-sm font-medium mb-1 text-white">
                密码 <span class="text-gray-400 text-xs">(留空则不修改)</span>
              </label>
              <div class="relative">
                <input
                  v-model="form.password"
                  id="password"
                  :type="showPassword ? 'text' : 'password'"
                  :disabled="isSubmitting"
                  class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 pr-10 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 text-white"
                  placeholder="请输入新密码"
                />
                <button
                  type="button"
                  @click="showPassword = !showPassword"
                  class="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-white"
                >
                  <i :class="showPassword ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
                </button>
              </div>
            </div>

            <!-- 商城币 -->
            <div>
              <label for="shop_coins" class="block text-sm font-medium mb-1 text-white">
                商城币
              </label>
              <input
                v-model.number="form.shop_coins"
                id="shop_coins"
                type="number"
                min="0"
                :disabled="isSubmitting"
                class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 text-white"
                placeholder="请输入商城币数量"
              />
            </div>
          </div>

          <!-- 用户信息显示 (仅编辑模式) -->
          <div v-if="!isCreating" class="bg-gray-700 rounded-md p-4 space-y-2">
            <h3 class="text-sm font-medium text-white mb-2">用户信息</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <span class="text-gray-400">用户ID:</span>
                <span class="text-white ml-2">{{ user?.id || user?.user_id || 'N/A' }}</span>
              </div>
              <div>
                <span class="text-gray-400">注册时间:</span>
                <span class="text-white ml-2">{{ formatDate(user?.created_at) }}</span>
              </div>
              <div>
                <span class="text-gray-400">最后登录:</span>
                <span class="text-white ml-2">{{ formatDate(user?.last_login_at) }}</span>
              </div>
              <div>
                <span class="text-gray-400">登录次数:</span>
                <span class="text-white ml-2">{{ user?.login_count || 0 }}</span>
              </div>
              <div>
                <span class="text-gray-400">游戏币:</span>
                <span class="text-white ml-2">{{ user?.game_coins || 0 }}</span>
              </div>
              <div>
                <span class="text-gray-400">商城币:</span>
                <span class="text-white ml-2">{{ user?.shop_coins || 0 }}</span>
              </div>
              <div>
                <span class="text-gray-400">积分:</span>
                <span class="text-white ml-2">{{ user?.points || 0 }}</span>
              </div>
              <div>
                <span class="text-gray-400">VIP等级:</span>
                <span class="text-white ml-2">{{ user?.vip_level || 0 }}</span>
              </div>
            </div>
          </div>

          <!-- 错误信息 -->
          <div v-if="error" class="bg-red-900/50 border border-red-500/50 rounded-md p-3">
            <p class="text-red-400 text-sm">{{ error }}</p>
          </div>

          <!-- 操作按钮 -->
          <div class="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              @click="closeModal"
              :disabled="isSubmitting"
              class="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50 transition-colors"
            >
              取消
            </button>
            <button
              v-if="isEditing || isCreating"
              type="submit"
              :disabled="isSubmitting"
              class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center"
            >
              <i v-if="isSubmitting" class="fas fa-spinner fa-spin mr-2"></i>
              {{
                isSubmitting
                  ? isCreating
                    ? '创建中...'
                    : '保存中...'
                  : isCreating
                    ? '创建'
                    : '保存'
              }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'

// Props
const props = defineProps({
  isVisible: {
    type: Boolean,
    default: false,
  },
  user: {
    type: Object,
    default: null,
  },
  isEditing: {
    type: Boolean,
    default: true,
  },
  isCreating: {
    type: Boolean,
    default: false,
  },
})

// Emits
const emit = defineEmits(['close', 'save'])

// 响应式数据
const isSubmitting = ref(false)
const error = ref('')
const showPassword = ref(false)

// 表单数据
const form = reactive({
  username: '',
  email: '',
  steam_id: '',
  password: '',
  user_type: 'user',
  is_active: true,
  shop_coins: 0,
  points: 0,
})

// 计算属性
const modalAnimationClass = computed(() => {
  return props.isVisible ? 'scale-100 opacity-100' : 'scale-95 opacity-0'
})

// 监听用户数据变化，更新表单
watch(
  () => props.user,
  (newUser) => {
    if (newUser) {
      console.log('[UserEditModal] 接收到用户数据:', newUser)
      form.username = newUser.username || ''
      form.email = newUser.email || ''
      form.steam_id = newUser.steam_id || ''
      form.password = '' // 密码字段始终为空，用于修改
      form.user_type = newUser.user_type || 'user'
      // 处理数据库中的1/0布尔值
      form.is_active = newUser.is_active === 1 || newUser.is_active === true
      form.shop_coins = newUser.shop_coins || 0
      form.points = newUser.points || 0
      console.log('[UserEditModal] 表单数据更新:', form)
    }
    error.value = ''
    showPassword.value = false // 重置密码显示状态
  },
  { immediate: true },
)

// 方法
const closeModal = () => {
  if (!isSubmitting.value) {
    emit('close')
  }
}

// Steam ID验证函数
const validateSteamId = (steamId) => {
  if (!steamId) return true // 允许空值，由后端处理
  const steamId64Regex = /^7656\d{13}$/
  return steamId64Regex.test(steamId)
}

const saveUser = async () => {
  if (!props.isEditing && !props.isCreating) return

  isSubmitting.value = true
  error.value = ''

  try {
    // 验证Steam ID格式
    if (form.steam_id && !validateSteamId(form.steam_id)) {
      error.value = 'Steam ID格式不正确，请输入正确的17位Steam ID64格式（以7656开头）'
      return
    }

    // 验证必填字段
    if (!form.username?.trim()) {
      error.value = '用户名不能为空'
      return
    }

    if (!form.email?.trim()) {
      error.value = '邮箱不能为空'
      return
    }

    // 构建更新数据
    const updateData = {
      username: form.username.trim(),
      email: form.email.trim(),
      steam_id: form.steam_id?.trim() || '',
      user_type: form.user_type,
      is_active: form.is_active ? 1 : 0, // 转换为数据库的1/0格式
    }

    // 创建模式下，密码是必填的
    if (props.isCreating) {
      if (!form.password || !form.password.trim()) {
        error.value = '创建用户时密码不能为空'
        return
      }
      updateData.password = form.password.trim()
      updateData.shop_coins = form.shop_coins
      updateData.points = form.points
    } else {
      // 编辑模式下，密码是可选的
      if (form.password && form.password.trim()) {
        updateData.password = form.password.trim()
      }

      // 如果商城币有变化，添加到更新数据中
      if (form.shop_coins !== (props.user?.shop_coins || 0)) {
        updateData.shop_coins = form.shop_coins
      }

      // 如果积分有变化，添加到更新数据中
      if (form.points !== (props.user?.points || 0)) {
        updateData.points = form.points
      }
    }

    emit('save', updateData)
  } catch (err) {
    console.error('保存用户失败:', err)
    error.value = err.message || '保存用户失败，请稍后重试'
  } finally {
    isSubmitting.value = false
  }
}

// 工具方法
const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleString('zh-CN')
}

// 监听ESC键关闭模态框
const handleKeydown = (event) => {
  if (event.key === 'Escape' && props.isVisible) {
    closeModal()
  }
}

// 组件挂载时添加键盘事件监听
import { onMounted, onUnmounted } from 'vue'

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
/* 自定义样式 */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: #374151;
}

::-webkit-scrollbar-thumb {
  background: #6b7280;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}
</style>
