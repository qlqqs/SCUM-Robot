import { createRouter, createWebHistory } from 'vue-router'
import { authApi } from '@/api/services/authApi.js'

const router = createRouter({
  history: createWebHistory('/'), // 页面路由使用根路径，不受base配置影响
  routes: [
    {
      path: '/',
      redirect: '/store',
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
    },
    {
      path: '/store',
      name: 'store',
      component: () => import('../views/GameStoreView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/cart',
      name: 'cart',
      component: () => import('../views/CartView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('../views/ProfileView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/gifts',
      name: 'gifts',
      component: () => import('../views/GiftsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/recharge',
      name: 'recharge',
      component: () => import('../views/RechargeView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/admin',
      name: 'admin',
      component: () => import('../views/AdminView.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
      children: [
        {
          path: '',
          name: 'admin-default',
          redirect: '/admin/dashboard',
        },
        {
          path: 'dashboard',
          name: 'admin-dashboard',
          component: () => import('../views/admin/DashboardView.vue'),
          meta: { requiresAuth: true, requiresAdmin: true },
        },
        {
          path: 'categories',
          name: 'admin-categories',
          component: () => import('../views/admin/CategoriesView.vue'),
          meta: { requiresAuth: true, requiresAdmin: true },
        },
        {
          path: 'subcategories',
          name: 'admin-subcategories',
          component: () => import('../views/admin/SubcategoriesView.vue'),
          meta: { requiresAuth: true, requiresAdmin: true },
        },
        {
          path: 'items',
          name: 'admin-items',
          component: () => import('../views/admin/ItemsView.vue'),
          meta: { requiresAuth: true, requiresAdmin: true },
        },
        {
          path: 'gifts',
          name: 'admin-gifts',
          component: () => import('../views/admin/GiftsView.vue'),
          meta: { requiresAuth: true, requiresAdmin: true },
        },
        {
          path: 'vip',
          name: 'AdminVip',
          component: () => import('../views/admin/VipView.vue'),
          meta: { requiresAuth: true, requiresAdmin: true },
        },
        {
          path: 'users',
          name: 'AdminUsers',
          component: () => import('../views/admin/UsersView.vue'),
          meta: { requiresAuth: true, requiresAdmin: true },
        },
        {
          path: 'payment',
          name: 'AdminPayment',
          component: () => import('../views/admin/PaymentConfigView.vue'),
          meta: { requiresAuth: true, requiresAdmin: true },
        },
        {
          path: 'packages',
          name: 'AdminPackages',
          component: () => import('../views/admin/RechargePackagesView.vue'),
          meta: { requiresAuth: true, requiresAdmin: true },
        },
        {
          path: 'orders',
          name: 'AdminOrders',
          component: () => import('../views/admin/OrdersView.vue'),
          meta: { requiresAuth: true, requiresAdmin: true },
        },

        {
          path: 'settings',
          component: () => import('../views/admin/SystemSettingsView.vue'),
          meta: { requiresAuth: true, requiresAdmin: true },
          children: [
            {
              path: '',
              name: 'admin-settings',
              redirect: 'system',
            },
            {
              path: 'system',
              name: 'admin-settings-system',
              component: () => import('../views/admin/SystemSettingsView.vue'),
              meta: { requiresAuth: true, requiresAdmin: true, category: 'system' },
            },
            {
              path: 'api',
              name: 'admin-settings-api',
              component: () => import('../views/admin/SystemSettingsView.vue'),
              meta: { requiresAuth: true, requiresAdmin: true, category: 'api' },
            },
            {
              path: 'security',
              name: 'admin-settings-security',
              component: () => import('../views/admin/SystemSettingsView.vue'),
              meta: { requiresAuth: true, requiresAdmin: true, category: 'security' },
            },
            {
              path: 'game',
              name: 'admin-settings-game',
              component: () => import('../views/admin/SystemSettingsView.vue'),
              meta: { requiresAuth: true, requiresAdmin: true, category: 'game' },
            },
            {
              path: 'user',
              name: 'admin-settings-user',
              component: () => import('../views/admin/SystemSettingsView.vue'),
              meta: { requiresAuth: true, requiresAdmin: true, category: 'user' },
            },
            {
              path: 'notification',
              name: 'admin-settings-notification',
              component: () => import('../views/admin/SystemSettingsView.vue'),
              meta: { requiresAuth: true, requiresAdmin: true, category: 'notification' },
            },
            {
              path: 'performance',
              name: 'admin-settings-performance',
              component: () => import('../views/admin/SystemSettingsView.vue'),
              meta: { requiresAuth: true, requiresAdmin: true, category: 'performance' },
            },
          ],
        },
      ],
    },
    {
      path: '/unauthorized',
      name: 'unauthorized',
      component: () => import('../views/UnauthorizedView.vue'),
    },
    {
      path: '/404',
      name: 'not-found',
      component: () => import('../views/NotFoundView.vue'),
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/404',
    },
  ],
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  console.log('[Router] Navigating to:', to.path)

  // 检查是否需要认证
  if (to.matched.some((record) => record.meta.requiresAuth)) {
    // 检查是否已登录
    if (!authApi.isLoggedIn()) {
      console.log('[Router] Not logged in, redirecting to login')
      next({
        path: '/login',
        query: { redirect: to.fullPath }, // 保存原始路径，登录后可以跳转回来
      })
      return
    }

    // 检查是否需要管理员权限
    if (to.matched.some((record) => record.meta.requiresAdmin)) {
      try {
        // 获取当前用户信息
        const userInfo = authApi.getCurrentUserFromStorage()

        if (!userInfo) {
          console.log('[Router] No user info found, redirecting to login')
          next({
            path: '/login',
            query: { redirect: to.fullPath },
          })
          return
        }

        // 检查是否是管理员（包括超级管理员）
        const isAdmin =
          userInfo.role === 'admin' ||
          userInfo.is_admin === true ||
          userInfo.is_super_admin === true ||
          userInfo.permissions?.includes('admin') ||
          userInfo.user_type === 'admin' ||
          userInfo.user_type === 'super_admin'

        if (!isAdmin) {
          console.log('[Router] Not admin, redirecting to unauthorized page')
          next({
            path: '/unauthorized',
            query: { error: 'insufficient_permissions' },
          })
          return
        }
      } catch (error) {
        console.error('[Router] Error checking admin permissions:', error)
        next({
          path: '/login',
          query: { redirect: to.fullPath },
        })
        return
      }
    }
  }

  // 如果已登录且访问登录页，重定向到商店
  if (to.path === '/login' && authApi.isLoggedIn()) {
    console.log('[Router] Already logged in, redirecting to store')
    next('/store')
    return
  }

  // 继续导航
  next()
})

// 路由错误处理
router.onError((error) => {
  console.error('[Router] Navigation error:', error)
})

export default router
