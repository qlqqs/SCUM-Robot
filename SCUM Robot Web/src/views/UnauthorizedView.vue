<template>
  <div class="min-h-screen bg-gray-900 flex items-center justify-center px-4">
    <div class="max-w-md w-full text-center">
      <!-- 权限不足图标 -->
      <div class="mb-8">
        <i class="fas fa-shield-alt text-6xl text-red-500 mb-4"></i>
        <h1 class="text-6xl font-bold text-white mb-2">403</h1>
        <h2 class="text-2xl font-semibold text-gray-300 mb-4">权限不足</h2>
        <p class="text-gray-400 mb-8">
          抱歉，您没有权限访问此页面。请联系管理员获取相应权限。
        </p>
      </div>

      <!-- 错误信息 -->
      <div v-if="errorMessage" class="mb-6 p-4 bg-red-900/50 border border-red-500 rounded-lg">
        <div class="flex items-center justify-center">
          <i class="fas fa-exclamation-triangle text-red-400 mr-2"></i>
          <span class="text-red-200">{{ errorMessage }}</span>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="space-y-4">
        <button
          @click="goBack"
          class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
        >
          <i class="fas fa-arrow-left mr-2"></i>
          返回上一页
        </button>
        
        <button
          @click="goHome"
          class="w-full bg-gray-700 hover:bg-gray-600 text-white font-medium py-3 px-6 rounded-lg transition-colors"
        >
          <i class="fas fa-home mr-2"></i>
          返回首页
        </button>

        <button
          @click="logout"
          class="w-full bg-red-600 hover:bg-red-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
        >
          <i class="fas fa-sign-out-alt mr-2"></i>
          退出登录
        </button>
      </div>

      <!-- 帮助信息 -->
      <div class="mt-8 text-sm text-gray-500">
        <p>需要管理员权限才能访问此功能</p>
        <p class="mt-2">如有疑问，请联系系统管理员</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { authApi } from '@/api/services/authApi.js'

const router = useRouter()
const route = useRoute()

const errorMessage = ref('')

onMounted(() => {
  // 从查询参数获取错误信息
  if (route.query.error === 'insufficient_permissions') {
    errorMessage.value = '您的账户权限不足，无法访问管理员功能'
  }
})

// 返回上一页
const goBack = () => {
  if (window.history.length > 1) {
    router.go(-1)
  } else {
    goHome()
  }
}

// 返回首页
const goHome = () => {
  router.push('/store')
}

// 退出登录
const logout = async () => {
  try {
    await authApi.logout()
    router.push('/login')
  } catch (error) {
    console.error('Logout failed:', error)
    // 即使退出失败，也清除本地数据并跳转
    localStorage.clear()
    router.push('/login')
  }
}
</script>

<style scoped>
/* 添加一些动画效果 */
.fas.fa-shield-alt {
  animation: shake 1s infinite;
}

@keyframes shake {
  0%, 100% {
    transform: translateX(0);
  }
  25% {
    transform: translateX(-5px);
  }
  75% {
    transform: translateX(5px);
  }
}
</style>
