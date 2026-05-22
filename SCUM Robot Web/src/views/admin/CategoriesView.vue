<template>
  <div>
    <div
      class="flex flex-col xl:flex-row xl:flex-wrap xl:justify-between xl:items-start mb-6 gap-4"
    >
      <div class="flex-shrink-0">
        <h2 class="text-lg sm:text-xl lg:text-2xl font-bold">类目管理</h2>
        <p class="text-xs sm:text-sm text-gray-400 mt-1 break-words">
          当前类目数量: {{ categories.length }} | 加载状态:
          {{ gameStore.loading.categories ? '加载中' : '已完成' }}
        </p>
      </div>
      <div
        class="flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center gap-2 sm:gap-3 xl:flex-shrink-0 xl:min-w-0"
      >
        <!-- 三级菜单切换按钮 -->
        <div class="flex bg-gray-700 rounded-lg p-1 w-full sm:w-auto sm:min-w-[200px]">
          <router-link
            to="/admin/categories"
            class="flex-1 sm:flex-none px-2 py-2 rounded-md text-xs font-medium transition-colors text-center whitespace-nowrap"
            :class="
              $route.path === '/admin/categories'
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:text-white hover:bg-gray-600'
            "
          >
            <i class="fas fa-folder mr-1"></i>
            <span class="hidden lg:inline">主类目管理</span>
            <span class="lg:hidden">主类目</span>
          </router-link>
          <router-link
            to="/admin/subcategories"
            class="flex-1 sm:flex-none px-2 py-2 rounded-md text-xs font-medium transition-colors text-center whitespace-nowrap"
            :class="
              $route.path === '/admin/subcategories'
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:text-white hover:bg-gray-600'
            "
          >
            <i class="fas fa-folder-open mr-1"></i>
            <span class="hidden lg:inline">子类目管理</span>
            <span class="lg:hidden">子类目</span>
          </router-link>
        </div>

        <!-- 刷新按钮 -->
        <button
          @click="refreshData"
          :disabled="gameStore.loading.categories"
          class="w-full sm:w-auto sm:min-w-[70px] bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-3 py-2 rounded transition-colors text-xs font-medium"
        >
          <i
            class="fas fa-sync-alt mr-1"
            :class="{ 'animate-spin': gameStore.loading.categories }"
          ></i>
          <span>刷新</span>
        </button>
      </div>
    </div>

    <!-- 错误提示 -->
    <div
      v-if="gameStore.errors.categories"
      class="mb-6 p-4 bg-red-900/50 border border-red-500 rounded-lg"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center">
          <i class="fas fa-exclamation-triangle text-red-400 mr-2"></i>
          <span class="text-red-200">{{ gameStore.errors.categories }}</span>
        </div>
        <button @click="gameStore.clearError('categories')" class="text-red-400 hover:text-red-300">
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
      <form
        @submit.prevent="addCategory"
        class="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 mb-6"
      >
        <input
          v-model="newCategoryName"
          type="text"
          placeholder="输入新类目名称"
          class="w-full sm:flex-grow sm:min-w-[120px] bg-gray-700 border border-gray-600 rounded-md py-2 px-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
          :disabled="isSubmitting"
          required
        />
        <input
          v-model="newCategoryDescription"
          type="text"
          placeholder="类目描述（可选）"
          class="w-full sm:flex-grow sm:min-w-[120px] bg-gray-700 border border-gray-600 rounded-md py-2 px-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
          :disabled="isSubmitting"
        />
        <button
          type="submit"
          :disabled="isSubmitting || !newCategoryName.trim()"
          class="w-full sm:w-auto bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold py-2 px-4 rounded transition-colors whitespace-nowrap"
        >
          <i class="fas fa-plus mr-2" :class="{ 'animate-spin': isSubmitting }"></i>
          {{ isSubmitting ? '添加中...' : '添加类目' }}
        </button>
      </form>

      <!-- 加载状态 -->
      <div v-if="gameStore.loading.categories && categories.length === 0" class="text-center py-8">
        <i class="fas fa-spinner fa-spin text-2xl text-gray-400 mb-2"></i>
        <p class="text-gray-400">加载类目数据中...</p>
      </div>

      <!-- 空状态 -->
      <div
        v-else-if="!gameStore.loading.categories && categories.length === 0"
        class="text-center py-8"
      >
        <i class="fas fa-folder-open text-4xl text-gray-500 mb-4"></i>
        <p class="text-gray-400 mb-4">暂无类目数据</p>
        <p class="text-sm text-gray-500">点击上方"添加类目"按钮创建第一个类目</p>
      </div>

      <!-- 数据表格 -->
      <div v-else class="overflow-x-auto" style="min-width: 0">
        <table class="w-full text-left" style="min-width: 800px">
          <thead>
            <tr class="border-b border-gray-700">
              <th class="p-2 min-w-[50px] w-[60px] text-center">ID</th>
              <th class="p-2 min-w-[150px] w-[180px] text-center">类目名称</th>
              <th class="p-2 min-w-[200px] w-[220px] text-center">描述</th>
              <th class="p-2 min-w-[70px] w-[80px] text-center">状态</th>
              <th class="p-2 min-w-[80px] w-[100px] text-center">物品数量</th>
              <th class="p-2 min-w-[100px] w-[120px] text-center">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="category in paginatedCategories"
              :key="category.id"
              class="border-b border-gray-700 hover:bg-gray-700/50"
            >
              <td class="p-2 text-center" :class="{ 'opacity-50': category.is_active === false }">
                {{ category.id }}
              </td>
              <td class="p-2 text-center">
                <div
                  v-if="!category.editing"
                  :class="{ 'opacity-50': category.is_active === false }"
                >
                  <div class="font-medium text-base">{{ category.name }}</div>
                </div>
                <div v-else class="space-y-2">
                  <input
                    v-model="category.editName"
                    @keyup.enter="saveCategory(category)"
                    @keyup.escape="cancelEdit(category)"
                    class="w-full bg-gray-600 border border-gray-500 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500 text-center"
                    placeholder="类目名称"
                    ref="editInput"
                  />
                </div>
              </td>
              <td class="p-2 text-center">
                <div
                  v-if="!category.editing"
                  :class="{ 'opacity-50': category.is_active === false }"
                >
                  <span class="text-sm text-gray-400">{{ category.description || '无描述' }}</span>
                </div>
                <div v-else>
                  <input
                    v-model="category.editDescription"
                    @keyup.enter="saveCategory(category)"
                    @keyup.escape="cancelEdit(category)"
                    class="w-full bg-gray-600 border border-gray-500 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500 text-center"
                    placeholder="类目描述（可选）"
                  />
                </div>
              </td>
              <td class="p-2 text-center">
                <span
                  :class="[
                    'px-2 py-1 rounded-full text-sm font-medium inline-block',
                    category.is_active !== false
                      ? 'bg-green-900/50 text-green-400 border border-green-500/50'
                      : 'bg-red-900/50 text-red-400 border border-red-500/50',
                  ]"
                >
                  {{ category.is_active !== false ? '活跃' : '停用' }}
                </span>
              </td>
              <td class="p-2 text-center">
                <span
                  class="text-sm text-gray-400"
                  :class="{ 'opacity-50': category.is_active === false }"
                >
                  {{ getItemCount(category.id) }} 个物品
                </span>
              </td>
              <td class="p-2 text-center">
                <template v-if="!category.editing">
                  <button
                    @click="editCategory(category)"
                    :disabled="category.updating || category.is_active === false"
                    class="text-blue-400 hover:text-blue-300 mr-2 disabled:opacity-50"
                    title="编辑"
                  >
                    <i class="fas fa-edit text-base"></i>
                  </button>
                  <button
                    @click="toggleCategoryStatus(category)"
                    :disabled="category.updating"
                    class="text-yellow-400 hover:text-yellow-300 mr-2 disabled:opacity-50"
                    :title="category.is_active !== false ? '停用' : '启用'"
                  >
                    <i
                      :class="
                        category.is_active !== false
                          ? 'fas fa-pause text-base'
                          : 'fas fa-play text-base'
                      "
                    ></i>
                  </button>
                  <button
                    @click="deleteCategory(category.id)"
                    :disabled="category.updating || category.is_active === false"
                    class="text-red-500 hover:text-red-400 disabled:opacity-50"
                    title="删除"
                  >
                    <i class="fas fa-trash text-base"></i>
                  </button>
                </template>
                <template v-else>
                  <button
                    @click="saveCategory(category)"
                    :disabled="category.updating"
                    class="text-green-400 hover:text-green-300 mr-2 disabled:opacity-50"
                    title="保存"
                  >
                    <i
                      class="fas fa-check text-base"
                      :class="{ 'animate-spin': category.updating }"
                    ></i>
                  </button>
                  <button
                    @click="cancelEdit(category)"
                    :disabled="category.updating"
                    class="text-gray-400 hover:text-gray-300 disabled:opacity-50"
                    title="取消"
                  >
                    <i class="fas fa-times text-base"></i>
                  </button>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 分页控件 -->
      <div v-if="totalPages > 1" class="flex justify-between items-center mt-6">
        <div class="text-sm text-gray-400">
          显示第 {{ (currentPage - 1) * pageSize + 1 }} -
          {{ Math.min(currentPage * pageSize, totalCategories) }} 条，共 {{ totalCategories }} 条
        </div>
        <div class="flex items-center gap-2">
          <button
            @click="previousPage"
            :disabled="currentPage === 1"
            class="px-3 py-1 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded transition-colors"
          >
            上一页
          </button>
          <div class="flex items-center gap-1">
            <button
              v-for="page in Math.min(totalPages, 5)"
              :key="page"
              @click="goToPage(page)"
              :class="page === currentPage ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'"
              class="px-3 py-1 text-white rounded transition-colors"
            >
              {{ page }}
            </button>
            <span v-if="totalPages > 5" class="text-gray-400 px-2">...</span>
          </div>
          <button
            @click="nextPage"
            :disabled="currentPage === totalPages"
            class="px-3 py-1 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded transition-colors"
          >
            下一页
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { useGameStore } from '@/stores/gameStore'
import { useSystemConfigStore } from '@/stores/systemConfigStore'

const gameStore = useGameStore()
const systemConfigStore = useSystemConfigStore()
const newCategoryName = ref('')
const newCategoryDescription = ref('')
const editInput = ref(null)
const isSubmitting = ref(false)
const successMessage = ref('')

// 分页相关
const currentPage = ref(1)
const pageSize = computed(() => systemConfigStore.categoriesPerPage)

// 从store中获取categories
const categories = computed(() => gameStore.categories)

// 分页计算属性
const totalCategories = computed(() => categories.value.length)
const totalPages = computed(() => Math.ceil(totalCategories.value / pageSize.value))
const paginatedCategories = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return categories.value.slice(start, end)
})

// 分页方法
const goToPage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
  }
}

const previousPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
  }
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
  }
}

// 获取类目下的物品数量
const getItemCount = (categoryId) => {
  return gameStore.getItemsByCategory(categoryId).length
}

// 刷新数据
const refreshData = async () => {
  try {
    await gameStore.loadCategories()
    successMessage.value = '数据刷新成功'
    setTimeout(() => {
      successMessage.value = ''
    }, 3000)
  } catch (error) {
    console.error('[Categories] Failed to refresh data:', error)
  }
}

// 添加新类目
const addCategory = async () => {
  if (!newCategoryName.value.trim()) return

  isSubmitting.value = true
  try {
    console.log('[Categories] Adding category:', newCategoryName.value.trim())
    const result = await gameStore.addCategory(
      newCategoryName.value.trim(),
      newCategoryDescription.value.trim(),
    )
    console.log('[Categories] Add category result:', result)

    // 强制刷新数据
    await gameStore.loadCategories()
    console.log('[Categories] After manual reload, categories count:', gameStore.categories.length)

    // 确保DOM更新
    await nextTick()

    newCategoryName.value = ''
    newCategoryDescription.value = ''
    successMessage.value = '类目添加成功'

    setTimeout(() => {
      successMessage.value = ''
    }, 3000)
  } catch (error) {
    console.error('[Categories] Failed to add category:', error)
    alert('添加类目失败: ' + error.message)
  } finally {
    isSubmitting.value = false
  }
}

// 编辑类目
const editCategory = async (category) => {
  category.editing = true
  category.editName = category.name
  category.editDescription = category.description || ''

  await nextTick()

  // 聚焦第一个输入框
  const inputs = document.querySelectorAll('input[type="text"]')
  const targetInput = Array.from(inputs).find((input) => input.value === category.editName)
  if (targetInput) {
    targetInput.focus()
    targetInput.select()
  }
}

// 保存类目
const saveCategory = async (category) => {
  if (!category.editName?.trim()) {
    alert('类目名称不能为空')
    return
  }

  // 检查是否有变更
  const hasNameChange = category.editName.trim() !== category.name
  const hasDescChange = (category.editDescription || '') !== (category.description || '')

  if (!hasNameChange && !hasDescChange) {
    cancelEdit(category)
    return
  }

  category.updating = true
  try {
    await gameStore.updateCategory(category.id, {
      name: category.editName.trim(),
      description: category.editDescription?.trim() || undefined,
    })

    category.editing = false
    delete category.editName
    delete category.editDescription

    successMessage.value = '类目更新成功'
    setTimeout(() => {
      successMessage.value = ''
    }, 3000)
  } catch (error) {
    console.error('[Categories] Failed to update category:', error)
    alert('更新类目失败: ' + error.message)
  } finally {
    category.updating = false
  }
}

// 取消编辑
const cancelEdit = (category) => {
  category.editing = false
  delete category.editName
  delete category.editDescription
}

// 切换类目状态
const toggleCategoryStatus = async (category) => {
  const newStatus = category.is_active === false
  const action = newStatus ? '启用' : '停用'

  // 不需要查询具体的关联数据，API会自动处理级联更新

  // 构建详细的确认消息
  let confirmMessage = `确定要${action}类目"${category.name}"吗？\n\n`

  if (!newStatus) {
    // 停用时的简单提示
    confirmMessage += `停用该类目则会关联停用该类目下的所有子类目和物品。\n\n确定要继续吗？`
  } else {
    confirmMessage += `确定要继续吗？`
  }

  if (!confirm(confirmMessage)) return

  // 立即禁用当前条目的所有按钮（除了启用/停用按钮）
  category.updating = true
  try {
    const response = await gameStore.updateCategoryActiveStatus(category.id, newStatus)

    if (response.success) {
      // 更新本地数据
      category.is_active = newStatus

      // 构建成功消息
      let successMsg = `类目${action}成功`
      if (response.data?.updated_subcategories > 0) {
        successMsg += `，同时${action}了 ${response.data.updated_subcategories} 个子类目`
      }
      if (response.data?.updated_items > 0) {
        successMsg += `，${response.data.updated_items} 个物品`
      }

      successMessage.value = successMsg
      setTimeout(() => {
        successMessage.value = ''
      }, 5000)

      // 数据已经在gameStore方法中重新加载了
    }
  } catch (error) {
    console.error('[Categories] Failed to toggle category status:', error)
    alert(`${action}类目失败: ` + error.message)
  } finally {
    category.updating = false
  }
}

// 删除类目
const deleteCategory = async (id) => {
  const category = categories.value.find((c) => c.id === id)
  if (!category) return

  const itemCount = getItemCount(id)
  let confirmMessage = '确定要删除这个类目吗？此操作不可撤销。'

  if (itemCount > 0) {
    confirmMessage = `该类目下有 ${itemCount} 个物品，无法删除。请先删除或移动类目下的所有物品。`
    alert(confirmMessage)
    return
  }

  if (!confirm(confirmMessage)) return

  category.updating = true
  try {
    await gameStore.deleteCategory(id)

    successMessage.value = '类目删除成功'
    setTimeout(() => {
      successMessage.value = ''
    }, 3000)
  } catch (error) {
    console.error('[Categories] Failed to delete category:', error)
    alert('删除类目失败: ' + error.message)
  } finally {
    if (category) {
      category.updating = false
    }
  }
}

onMounted(async () => {
  // 加载系统配置
  await systemConfigStore.loadConfig()

  // 如果没有数据，则加载数据
  if (categories.value.length === 0) {
    await gameStore.loadCategories()
  }
})
</script>
