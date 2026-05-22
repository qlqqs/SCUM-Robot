<template>
  <div class="min-h-screen bg-gray-900 flex items-center justify-center px-4">
    <div class="max-w-md w-full text-center">
      <!-- 404图标 -->
      <div class="mb-8">
        <i class="fas fa-exclamation-triangle text-6xl text-yellow-500 mb-4"></i>
        <h1 class="text-6xl font-bold text-white mb-2">404</h1>
        <h2 class="text-2xl font-semibold text-gray-300 mb-4">页面未找到</h2>
        <p class="text-gray-400 mb-8">
          抱歉，您访问的页面不存在或已被移动。
        </p>
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
      </div>

      <!-- 帮助信息 -->
      <div class="mt-8 text-sm text-gray-500">
        <p>如果您认为这是一个错误，请联系管理员</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { authApi } from '@/api/services/authApi.js'

const router = useRouter()

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
  // 根据登录状态决定跳转到哪里
  if (authApi.isLoggedIn()) {
    router.push('/store')
  } else {
    router.push('/login')
  }
}
</script>

<style scoped>
/* 添加一些动画效果 */
.fas {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}
</style>
