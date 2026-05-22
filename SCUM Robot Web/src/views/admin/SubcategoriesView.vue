<template>
  <div>
    <div
      class="flex flex-col xl:flex-row xl:flex-wrap xl:justify-between xl:items-start mb-6 gap-4"
    >
      <div class="flex-shrink-0">
        <h2 class="text-lg sm:text-xl lg:text-2xl font-bold">子类目管理</h2>
        <p class="text-xs sm:text-sm text-gray-400 mt-1 break-words">
          当前子类目数量: {{ totalSubcategories }} | 显示: {{ paginatedSubcategories.length }} |
          加载状态:
          {{ gameStore.loading.subcategories ? '加载中' : '已完成' }}
        </p>
      </div>
      <div
        class="flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center gap-2 sm:gap-3 xl:flex-shrink-0 xl:min-w-0"
      >
        <!-- 主类目筛选 -->
        <select
          v-model="selectedCategoryId"
          @change="handleCategoryFilter"
          class="w-full sm:w-auto sm:min-w-[100px] bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">全部主类目</option>
          <option v-for="category in categories" :key="category.id" :value="category.id">
            {{ category.name }}
          </option>
        </select>
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
          :disabled="gameStore.loading.subcategories"
          class="w-full sm:w-auto sm:min-w-[70px] bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-3 py-2 rounded transition-colors text-xs font-medium"
        >
          <i
            class="fas fa-sync-alt mr-1"
            :class="{ 'animate-spin': gameStore.loading.subcategories }"
          ></i>
          <span>刷新</span>
        </button>
      </div>
    </div>

    <!-- 错误提示 -->
    <div
      v-if="gameStore.errors.subcategories"
      class="mb-6 p-4 bg-red-900/50 border border-red-500 rounded-lg"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center">
          <i class="fas fa-exclamation-triangle text-red-400 mr-2"></i>
          <span class="text-red-200">{{ gameStore.errors.subcategories }}</span>
        </div>
        <button
          @click="gameStore.clearError('subcategories')"
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
      <!-- 添加子类目表单 -->
      <form
        @submit.prevent="addSubcategory"
        class="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 mb-6"
      >
        <select
          v-model="newSubcategoryData.categoryId"
          class="w-full sm:w-auto sm:min-w-[140px] bg-gray-700 border border-gray-600 rounded-md py-2 px-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
          :disabled="isSubmitting"
          required
        >
          <option value="">选择主类目</option>
          <option v-for="category in categories" :key="category.id" :value="category.id">
            {{ category.name }}
          </option>
        </select>
        <input
          v-model="newSubcategoryData.name"
          type="text"
          placeholder="输入子类目名称"
          class="w-full sm:flex-grow sm:min-w-[90px] bg-gray-700 border border-gray-600 rounded-md py-2 px-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
          :disabled="isSubmitting"
          required
        />
        <input
          v-model="newSubcategoryData.description"
          type="text"
          placeholder="子类目描述（可选）"
          class="w-full sm:flex-grow sm:min-w-[90px] bg-gray-700 border border-gray-600 rounded-md py-2 px-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
          :disabled="isSubmitting"
        />
        <button
          type="submit"
          :disabled="
            isSubmitting || !newSubcategoryData.name.trim() || !newSubcategoryData.categoryId
          "
          class="w-full sm:w-auto sm:min-w-[140px] bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold py-2 px-4 rounded transition-colors whitespace-nowrap"
        >
          <i class="fas fa-plus mr-2" :class="{ 'animate-spin': isSubmitting }"></i>
          {{ isSubmitting ? '添加中...' : '添加子类目' }}
        </button>
      </form>
      <!-- 加载状态 -->
      <div
        v-if="gameStore.loading.subcategories && paginatedSubcategories.length === 0"
        class="text-center py-8"
      >
        <i class="fas fa-spinner fa-spin text-2xl text-gray-400 mb-2"></i>
        <p class="text-gray-400">加载子类目数据中...</p>
      </div>

      <!-- 空状态 -->
      <div
        v-else-if="!gameStore.loading.subcategories && paginatedSubcategories.length === 0"
        class="text-center py-8"
      >
        <i class="fas fa-folder-open text-4xl text-gray-500 mb-4"></i>
        <p class="text-gray-400 mb-4">
          {{ selectedCategoryId ? '该主类目下暂无子类目' : '暂无子类目数据' }}
        </p>
        <p class="text-sm text-gray-500">点击上方"添加子类目"按钮创建第一个子类目</p>
      </div>

      <!-- 数据表格 -->
      <div v-else class="overflow-x-auto" style="min-width: 0">
        <table class="w-full text-left" style="min-width: 900px">
          <thead>
            <tr class="border-b border-gray-700">
              <th class="p-2 min-w-[50px] w-[60px] text-center">ID</th>
              <th class="p-2 min-w-[140px] w-[160px] text-center">子类目名称</th>
              <th class="p-2 min-w-[120px] w-[140px] text-center">主类目</th>
              <th class="p-2 min-w-[160px] w-[180px] text-center">描述</th>
              <th class="p-2 min-w-[70px] w-[80px] text-center">状态</th>
              <th class="p-2 min-w-[80px] w-[100px] text-center">物品数量</th>
              <th class="p-2 min-w-[100px] w-[120px] text-center">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="subcategory in paginatedSubcategories"
              :key="subcategory.id"
              class="border-b border-gray-700 hover:bg-gray-700/50"
            >
              <td
                class="p-2 text-center"
                :class="{ 'opacity-50': subcategory.is_active === false }"
              >
                {{ subcategory.id }}
              </td>
              <td class="p-2 text-center">
                <div
                  v-if="!subcategory.editing"
                  :class="{ 'opacity-50': subcategory.is_active === false }"
                >
                  <div class="font-medium text-base">{{ subcategory.name }}</div>
                </div>
                <div v-else class="space-y-2">
                  <input
                    v-model="subcategory.editName"
                    @keyup.enter="saveSubcategory(subcategory)"
                    @keyup.escape="cancelEdit(subcategory)"
                    class="w-full bg-gray-600 border border-gray-500 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500 text-center"
                    placeholder="子类目名称"
                    ref="editInput"
                  />
                </div>
              </td>
              <td class="p-2 text-center">
                <span class="text-sm" :class="{ 'opacity-50': subcategory.is_active === false }">{{
                  getCategoryName(subcategory.category_id)
                }}</span>
              </td>
              <td class="p-2 text-center">
                <div
                  v-if="!subcategory.editing"
                  :class="{ 'opacity-50': subcategory.is_active === false }"
                >
                  <span class="text-sm text-gray-400">{{
                    subcategory.description || '无描述'
                  }}</span>
                </div>
                <div v-else>
                  <input
                    v-model="subcategory.editDescription"
                    @keyup.enter="saveSubcategory(subcategory)"
                    @keyup.escape="cancelEdit(subcategory)"
                    class="w-full bg-gray-600 border border-gray-500 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500 text-center"
                    placeholder="子类目描述（可选）"
                  />
                </div>
              </td>
              <td class="p-2 text-center">
                <span
                  :class="[
                    'px-2 py-1 rounded-full text-sm font-medium inline-block',
                    subcategory.is_active !== false
                      ? 'bg-green-900/50 text-green-400 border border-green-500/50'
                      : 'bg-red-900/50 text-red-400 border border-red-500/50',
                  ]"
                >
                  {{ subcategory.is_active !== false ? '活跃' : '停用' }}
                </span>
              </td>
              <td class="p-2 text-center">
                <span
                  class="text-sm text-gray-400"
                  :class="{ 'opacity-50': subcategory.is_active === false }"
                >
                  {{ getItemCount(subcategory.id) }} 个物品
                </span>
              </td>
              <td class="p-2 text-center">
                <template v-if="!subcategory.editing">
                  <button
                    @click="editSubcategory(subcategory)"
                    :disabled="subcategory.updating || subcategory.is_active === false"
                    class="text-blue-400 hover:text-blue-300 mr-2 disabled:opacity-50"
                    title="编辑"
                  >
                    <i class="fas fa-edit text-base"></i>
                  </button>
                  <button
                    @click="toggleSubcategoryStatus(subcategory)"
                    :disabled="subcategory.updating"
                    class="text-yellow-400 hover:text-yellow-300 mr-2 disabled:opacity-50"
                    :title="subcategory.is_active !== false ? '停用' : '启用'"
                  >
                    <i
                      :class="
                        subcategory.is_active !== false
                          ? 'fas fa-pause text-base'
                          : 'fas fa-play text-base'
                      "
                    ></i>
                  </button>
                  <button
                    @click="deleteSubcategory(subcategory.id)"
                    :disabled="subcategory.updating || subcategory.is_active === false"
                    class="text-red-500 hover:text-red-400 disabled:opacity-50"
                    title="删除"
                  >
                    <i class="fas fa-trash text-base"></i>
                  </button>
                </template>
                <template v-else>
                  <button
                    @click="saveSubcategory(subcategory)"
                    :disabled="subcategory.updating"
                    class="text-green-400 hover:text-green-300 mr-2 disabled:opacity-50"
                    title="保存"
                  >
                    <i
                      class="fas fa-check text-base"
                      :class="{ 'animate-spin': subcategory.updating }"
                    ></i>
                  </button>
                  <button
                    @click="cancelEdit(subcategory)"
                    :disabled="subcategory.updating"
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
          {{ Math.min(currentPage * pageSize, totalSubcategories) }} 条，共
          {{ totalSubcategories }} 条
        </div>
        <div class="flex items-center gap-2">
          <button
            @click="previousPage"
            :disabled="currentPage === 1"
            class="px-3 py-1 bg-gray-700 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-600"
          >
            上一页
          </button>
          <span class="text-sm text-gray-400"> 第 {{ currentPage }} / {{ totalPages }} 页 </span>
          <button
            @click="nextPage"
            :disabled="currentPage === totalPages"
            class="px-3 py-1 bg-gray-700 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-600"
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
const selectedCategoryId = ref('')
const successMessage = ref('')
const isSubmitting = ref(false)
const editInput = ref(null)

// 分页相关
const currentPage = ref(1)
const pageSize = computed(() => systemConfigStore.subcategoriesPerPage)

// 新子类目数据（用于内联表单）
const newSubcategoryData = ref({
  categoryId: '',
  name: '',
  description: '',
})

// 从store中获取数据
const categories = computed(() => gameStore.categories)
const subcategories = computed(() => gameStore.subcategories)

// 显示的子类目列表（经过筛选）
const displayedSubcategories = computed(() => {
  let result = subcategories.value

  // 主类目筛选
  if (selectedCategoryId.value) {
    result = result.filter((sub) => sub.category_id == selectedCategoryId.value)
  }

  return result
})

// 分页计算属性
const totalSubcategories = computed(() => displayedSubcategories.value.length)
const totalPages = computed(() => Math.ceil(totalSubcategories.value / pageSize.value))

// 分页后的子类目列表
const paginatedSubcategories = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return displayedSubcategories.value.slice(start, end)
})

// 获取主类目名称
const getCategoryName = (categoryId) => {
  const category = categories.value.find((c) => c.id === categoryId)
  return category ? category.name : '未知类目'
}

// 获取子类目下的物品数量
const getItemCount = (subcategoryId) => {
  return gameStore.items.filter(
    (item) => (item.subcategoryId || item.subcategory_id) === subcategoryId,
  ).length
}

// 筛选处理
const handleCategoryFilter = () => {
  // 筛选逻辑已在 displayedSubcategories 计算属性中处理
  // 重置到第一页
  currentPage.value = 1
}

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

// 刷新数据
const refreshData = async () => {
  try {
    await Promise.all([gameStore.loadCategories(), gameStore.loadSubcategories()])
    successMessage.value = '数据刷新成功'
    setTimeout(() => {
      successMessage.value = ''
    }, 3000)
  } catch (error) {
    console.error('[Subcategories] Failed to refresh data:', error)
  }
}

// 添加子类目（内联表单）
const addSubcategory = async () => {
  if (!newSubcategoryData.value.name.trim() || !newSubcategoryData.value.categoryId) {
    alert('请填写完整信息')
    return
  }

  isSubmitting.value = true
  try {
    await gameStore.addSubcategory(
      parseInt(newSubcategoryData.value.categoryId),
      newSubcategoryData.value.name.trim(),
      newSubcategoryData.value.description.trim(),
    )

    // 重置表单
    newSubcategoryData.value = {
      categoryId: '',
      name: '',
      description: '',
    }

    successMessage.value = '子类目添加成功'

    setTimeout(() => {
      successMessage.value = ''
    }, 3000)
  } catch (error) {
    console.error('[Subcategories] Failed to add subcategory:', error)
    alert('添加子类目失败: ' + error.message)
  } finally {
    isSubmitting.value = false
  }
}

// 编辑子类目
const editSubcategory = async (subcategory) => {
  subcategory.editing = true
  subcategory.editName = subcategory.name
  subcategory.editDescription = subcategory.description || ''

  await nextTick()

  // 聚焦第一个输入框
  const inputs = document.querySelectorAll('input[type="text"]')
  const targetInput = Array.from(inputs).find((input) => input.value === subcategory.editName)
  if (targetInput) {
    targetInput.focus()
    targetInput.select()
  }
}

// 保存子类目
const saveSubcategory = async (subcategory) => {
  if (!subcategory.editName?.trim()) {
    alert('子类目名称不能为空')
    return
  }

  // 检查是否有变更
  const hasNameChange = subcategory.editName.trim() !== subcategory.name
  const hasDescChange = (subcategory.editDescription || '') !== (subcategory.description || '')

  if (!hasNameChange && !hasDescChange) {
    cancelEdit(subcategory)
    return
  }

  subcategory.updating = true
  try {
    await gameStore.updateSubcategory(subcategory.id, {
      name: subcategory.editName.trim(),
      description: subcategory.editDescription?.trim() || undefined,
    })

    subcategory.editing = false
    delete subcategory.editName
    delete subcategory.editDescription

    successMessage.value = '子类目更新成功'
    setTimeout(() => {
      successMessage.value = ''
    }, 3000)
  } catch (error) {
    console.error('[Subcategories] Failed to update subcategory:', error)
    alert('更新子类目失败: ' + error.message)
  } finally {
    subcategory.updating = false
  }
}

// 取消编辑
const cancelEdit = (subcategory) => {
  subcategory.editing = false
  delete subcategory.editName
  delete subcategory.editDescription
}

// 切换子类目状态
const toggleSubcategoryStatus = async (subcategory) => {
  const newStatus = subcategory.is_active === false
  const action = newStatus ? '启用' : '停用'

  // 构建确认消息
  let confirmMessage = `确定要${action}子类目"${subcategory.name}"吗？\n\n`

  if (!newStatus) {
    // 停用时的级联提示
    confirmMessage += `⚠️ 注意：停用该子类目会自动下架该子类目下的所有物品。\n\n确定要继续吗？`
  } else {
    // 启用时的级联提示
    confirmMessage += `✅ 启用该子类目会自动上架该子类目下的所有物品。\n\n确定要继续吗？`
  }

  if (!confirm(confirmMessage)) return

  // 立即禁用当前条目的所有按钮（除了启用/停用按钮）
  subcategory.updating = true
  try {
    console.log(`[Subcategories] ${action}子类目:`, subcategory.name, `(ID: ${subcategory.id})`)
    const response = await gameStore.updateSubcategoryActiveStatus(subcategory.id, newStatus)
    console.log(`[Subcategories] ${action}子类目响应:`, response)

    if (response.success) {
      // 更新本地数据
      subcategory.is_active = newStatus

      // 构建成功消息 - 优先使用后端返回的消息
      let successMsg = response.message || `子类目${action}成功`

      // 如果响应中包含级联影响的统计信息，添加到消息中
      if (response.data?.updated_items > 0) {
        successMsg += `，同时${action === '停用' ? '下架' : '上架'}了 ${response.data.updated_items} 个物品`
      }

      successMessage.value = successMsg
      setTimeout(() => {
        successMessage.value = ''
      }, 5000)

      console.log(`[Subcategories] ${action}子类目成功:`, successMsg)
    }
  } catch (error) {
    console.error(`[Subcategories] ${action}子类目失败:`, error)
    const errorMsg = error.message || `${action}子类目失败`
    alert(`${errorMsg}`)
  } finally {
    subcategory.updating = false
  }
}

// 删除子类目
const deleteSubcategory = async (id) => {
  const subcategory = displayedSubcategories.value.find((s) => s.id === id)
  if (!subcategory) return

  const itemCount = getItemCount(id)
  let confirmMessage = '确定要删除这个子类目吗？此操作不可撤销。'

  if (itemCount > 0) {
    confirmMessage = `该子类目下有 ${itemCount} 个物品，无法删除。请先删除或移动这些物品。`
    alert(confirmMessage)
    return
  }

  if (!confirm(confirmMessage)) return

  subcategory.updating = true
  try {
    await gameStore.deleteSubcategory(id)

    successMessage.value = '子类目删除成功'
    setTimeout(() => {
      successMessage.value = ''
    }, 3000)
  } catch (error) {
    console.error('[Subcategories] Failed to delete subcategory:', error)
    alert('删除子类目失败: ' + error.message)
  } finally {
    if (subcategory) {
      subcategory.updating = false
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
  if (subcategories.value.length === 0) {
    await gameStore.loadSubcategories()
  }
})
</script>

<style scoped>
/* Modal animation */
.transition-all {
  transition-property: all;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
}

.scale-95 {
  transform: scale(0.95);
}

.scale-100 {
  transform: scale(1);
}
</style>
