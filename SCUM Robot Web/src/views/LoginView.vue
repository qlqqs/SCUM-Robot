<template>
  <div
    class="min-h-screen bg-cover bg-center bg-no-repeat flex items-center justify-center text-gray-200"
    style="
      background-image: url('https://images.unsplash.com/photo-1444464666168-49d633b86797?q=80&w=2069&auto=format&fit=crop');
    "
  >
    <!-- 主容器 -->
    <div
      class="w-full max-w-md mx-auto bg-black bg-opacity-50 rounded-2xl shadow-2xl backdrop-blur-lg border border-gray-700 p-8"
    >
      <!-- 头部 -->
      <div class="flex flex-col items-center mb-8">
        <h1 class="text-4xl font-bold tracking-wider mb-2">{{ siteName }}</h1>
        <p class="text-xs text-gray-400">{{ siteDescription }}</p>
      </div>

      <!-- 标签页切换 -->
      <div class="w-full flex mb-6">
        <button
          @click="activeTab = 'login'"
          :class="[
            'flex-1 pb-2 text-sm font-semibold transition',
            activeTab === 'login'
              ? 'text-white border-b-2 border-blue-500'
              : 'text-gray-500 hover:text-white',
          ]"
        >
          登录
        </button>
        <button
          @click="activeTab = 'register'"
          :class="[
            'flex-1 pb-2 text-sm font-semibold transition',
            activeTab === 'register'
              ? 'text-white border-b-2 border-blue-500'
              : 'text-gray-500 hover:text-white',
          ]"
        >
          新用户注册
        </button>
      </div>

      <!-- 登录表单 -->
      <form v-if="activeTab === 'login'" @submit.prevent="handleLogin" class="space-y-4">
        <div class="relative">
          <input
            type="text"
            id="login-username"
            v-model="loginForm.username"
            class="auth-input"
            placeholder="请输入昵称或SteamID"
            required
          />
        </div>

        <div class="relative">
          <input
            :type="showLoginPassword ? 'text' : 'password'"
            id="login-password"
            v-model="loginForm.password"
            class="auth-input pr-12"
            placeholder="请输入密码"
            required
          />
          <button
            type="button"
            @click="showLoginPassword = !showLoginPassword"
            class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-300 transition-colors"
          >
            <i :class="showLoginPassword ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
          </button>
        </div>

        <div class="flex items-center">
          <input
            type="checkbox"
            id="remember-me"
            v-model="loginForm.rememberMe"
            class="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500"
          />
          <label for="remember-me" class="ml-2 text-sm text-gray-300">记住我</label>
        </div>

        <button
          type="submit"
          :disabled="isLoading"
          class="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold py-3 px-4 rounded-lg shadow-lg transform hover:scale-105 transition duration-300 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
        >
          <span v-if="isLoading" class="flex items-center justify-center">
            <i class="fas fa-spinner fa-spin mr-2"></i>
            登录中...
          </span>
          <span v-else>登录</span>
        </button>
      </form>

      <!-- 注册表单 -->
      <form v-if="activeTab === 'register'" @submit.prevent="handleRegister" class="space-y-4">
        <div class="relative">
          <input
            type="text"
            id="register-username"
            v-model="registerForm.username"
            class="auth-input"
            placeholder="请输入昵称"
            required
          />
        </div>

        <div class="relative">
          <input
            type="text"
            id="register-steamid"
            v-model="registerForm.steamId"
            class="auth-input"
            placeholder="请输入SteamID"
            required
          />
        </div>

        <div class="relative">
          <input
            type="email"
            id="register-email"
            v-model="registerForm.email"
            class="auth-input"
            placeholder="请输入邮箱地址 (用于密码找回)"
            required
          />
        </div>

        <div class="relative">
          <input
            :type="showRegisterPassword ? 'text' : 'password'"
            id="register-password"
            v-model="registerForm.password"
            class="auth-input pr-12"
            placeholder="请输入密码"
            required
          />
          <button
            type="button"
            @click="showRegisterPassword = !showRegisterPassword"
            class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-300 transition-colors"
          >
            <i :class="showRegisterPassword ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
          </button>
        </div>

        <div class="relative">
          <input
            :type="showRegisterConfirmPassword ? 'text' : 'password'"
            id="register-confirm-password"
            v-model="registerForm.confirmPassword"
            class="auth-input pr-12"
            placeholder="请确认密码"
            required
          />
          <button
            type="button"
            @click="showRegisterConfirmPassword = !showRegisterConfirmPassword"
            class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-300 transition-colors"
          >
            <i :class="showRegisterConfirmPassword ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
          </button>
        </div>

        <div class="flex items-center">
          <input
            type="checkbox"
            id="agree-terms"
            v-model="registerForm.agreeTerms"
            class="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500"
            required
          />
          <label for="agree-terms" class="ml-2 text-sm text-gray-300">
            我同意
            <a href="#" class="text-blue-400 hover:text-blue-300">服务条款</a>
            和
            <a href="#" class="text-blue-400 hover:text-blue-300">隐私政策</a>
          </label>
        </div>

        <button
          type="submit"
          :disabled="isLoading"
          class="w-full bg-gradient-to-r from-green-600 to-teal-600 hover:from-green-700 hover:to-teal-700 text-white font-bold py-3 px-4 rounded-lg shadow-lg transform hover:scale-105 transition duration-300 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
        >
          <span v-if="isLoading" class="flex items-center justify-center">
            <i class="fas fa-spinner fa-spin mr-2"></i>
            注册中...
          </span>
          <span v-else>注册</span>
        </button>
      </form>

      <!-- 错误/成功消息 -->
      <div
        v-if="errorMessage"
        class="mt-4 p-3 bg-red-600 bg-opacity-20 border border-red-500 rounded-lg"
      >
        <p class="text-red-300 text-sm">{{ errorMessage }}</p>
      </div>

      <div
        v-if="successMessage"
        class="mt-4 p-3 bg-green-600 bg-opacity-20 border border-green-500 rounded-lg"
      >
        <p class="text-green-300 text-sm">{{ successMessage }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useSystemConfigStore } from '@/stores/systemConfigStore'
import { authApi } from '../api/services/authApi.js'

const router = useRouter()
const route = useRoute()
const systemConfigStore = useSystemConfigStore()

// 网站信息（从系统配置获取）
const siteName = computed(() => systemConfigStore.siteName || 'SCUM')
const siteDescription = computed(() => systemConfigStore.siteDescription || 'SCUM服务器')

// 响应式数据
const activeTab = ref('login')
const isLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const showLoginPassword = ref(false)
const showRegisterPassword = ref(false)
const showRegisterConfirmPassword = ref(false)

// 登录表单数据
const loginForm = reactive({
  username: '',
  password: '',
  rememberMe: false,
})

// 注册表单数据
const registerForm = reactive({
  username: '',
  steamId: '',
  email: '',
  password: '',
  confirmPassword: '',
  agreeTerms: false,
})

// 清除消息
const clearMessages = () => {
  errorMessage.value = ''
  successMessage.value = ''
}

// SteamID验证函数
const validateSteamId = (steamId) => {
  const steamId64Regex = /^7656\d{13}$/
  return steamId64Regex.test(steamId)
}

// 处理登录
const handleLogin = async () => {
  clearMessages()

  if (!loginForm.username || !loginForm.password) {
    errorMessage.value = '请填写完整的登录信息'
    return
  }

  isLoading.value = true

  try {
    // 使用用户名登录，包含记住我状态
    const loginData = {
      username: loginForm.username,
      password: loginForm.password,
      remember_me: loginForm.rememberMe,
    }

    const result = await authApi.login(loginData)

    if (result.success) {
      successMessage.value = '登录成功！正在跳转...'

      // 处理前端"记住我"功能（保存用户名以便下次自动填充）
      if (loginForm.rememberMe) {
        // 如果选择记住我，将用户名保存到localStorage以便下次自动填充
        localStorage.setItem(
          'rememberedUser',
          JSON.stringify({
            username: loginForm.username,
            rememberMe: true,
            loginTime: Date.now(),
          }),
        )
      } else {
        // 如果没有选择记住我，清除记住的用户信息
        localStorage.removeItem('rememberedUser')
      }

      // 跳转到原始请求的页面或默认页面
      setTimeout(() => {
        const redirectPath = route.query.redirect || '/store'
        console.log('[Login] Redirecting to:', redirectPath)
        router.push(redirectPath)
      }, 1000)
    }
  } catch (apiError) {
    errorMessage.value = apiError.message || '登录失败，请检查用户名和密码'
  } finally {
    isLoading.value = false
  }
}

// 处理注册
const handleRegister = async () => {
  clearMessages()

  if (
    !registerForm.username ||
    !registerForm.steamId ||
    !registerForm.email ||
    !registerForm.password ||
    !registerForm.confirmPassword
  ) {
    errorMessage.value = '请填写完整的注册信息'
    return
  }

  if (!validateSteamId(registerForm.steamId)) {
    errorMessage.value = 'SteamID格式不正确，请输入正确的SteamID64格式'
    return
  }

  if (registerForm.password !== registerForm.confirmPassword) {
    errorMessage.value = '两次输入的密码不一致'
    return
  }

  if (registerForm.password.length < 6) {
    errorMessage.value = '密码长度至少为6位'
    return
  }

  if (!registerForm.agreeTerms) {
    errorMessage.value = '请同意服务条款和隐私政策'
    return
  }

  isLoading.value = true

  try {
    // 验证密码强度
    const passwordValidation = authApi.validatePassword(registerForm.password)
    if (!passwordValidation.isValid) {
      errorMessage.value = passwordValidation.errors.join(', ')
      return
    }

    const result = await authApi.register({
      steam_id: registerForm.steamId, // 保持字符串格式，避免精度丢失
      username: registerForm.username,
      email: registerForm.email,
      password: registerForm.password,
    })

    if (result.success) {
      successMessage.value = '注册成功！请登录您的账户'

      // 切换到登录标签页
      setTimeout(() => {
        activeTab.value = 'login'
        // 清空注册表单
        Object.keys(registerForm).forEach((key) => {
          if (typeof registerForm[key] === 'boolean') {
            registerForm[key] = false
          } else {
            registerForm[key] = ''
          }
        })
      }, 1500)
    }
  } catch (apiError) {
    errorMessage.value = apiError.message || '注册失败，请稍后重试'
  } finally {
    isLoading.value = false
  }
}

// 组件挂载时检查记住的用户信息
onMounted(async () => {
  // 加载系统配置
  await systemConfigStore.loadConfig()

  const rememberedUser = localStorage.getItem('rememberedUser')
  if (rememberedUser) {
    try {
      const userData = JSON.parse(rememberedUser)
      // 检查记住的时间是否超过30天
      const thirtyDaysInMs = 30 * 24 * 60 * 60 * 1000
      if (Date.now() - userData.loginTime < thirtyDaysInMs) {
        loginForm.username = userData.username
        loginForm.rememberMe = userData.rememberMe
      } else {
        // 超过30天，清除记住的信息
        localStorage.removeItem('rememberedUser')
      }
    } catch (error) {
      console.error('解析记住的用户信息失败:', error)
      localStorage.removeItem('rememberedUser')
    }
  }
})
</script>

<style scoped>
/* 认证输入框样式 */
.auth-input {
  width: 100%;
  padding: 12px 16px;
  background: rgba(31, 41, 55, 0.8);
  border: 1px solid rgba(75, 85, 99, 0.5);
  border-radius: 8px;
  color: white;
  font-size: 14px;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
}

.auth-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  background: rgba(31, 41, 55, 0.9);
}

.auth-input::placeholder {
  color: rgba(156, 163, 175, 0.8);
}

/* 按钮悬停效果 */
button:disabled {
  cursor: not-allowed !important;
  transform: none !important;
}

/* 动画效果 */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.auth-input,
button {
  animation: fadeIn 0.3s ease-out;
}

/* 标签页切换动画 */
form {
  animation: fadeIn 0.4s ease-out;
}

/* 错误和成功消息动画 */
.mt-4 {
  animation: fadeIn 0.3s ease-out;
}
</style>
