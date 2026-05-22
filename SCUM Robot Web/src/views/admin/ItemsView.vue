<template>
  <div>
    <div
      class="flex flex-col xl:flex-row xl:flex-wrap xl:justify-between xl:items-start mb-6 gap-4"
    >
      <div class="flex-shrink-0">
        <h2 class="text-lg sm:text-xl lg:text-2xl font-bold">物品管理</h2>
        <p class="text-xs sm:text-sm text-gray-400 mt-1 break-words">
          当前物品数量: {{ items.length }} | 加载状态:
          {{ gameStore.loading.items ? '加载中' : '已完成' }}
        </p>
      </div>
      <div
        class="flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center gap-2 sm:gap-3 xl:flex-shrink-0 xl:min-w-0 max-w-full"
      >
        <!-- 搜索筛选盒子 -->
        <div
          class="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3 sm:flex-1 sm:min-w-[380px]"
        >
          <!-- 搜索框 -->
          <div class="relative">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索物品..."
              class="bg-gray-700 border border-gray-600 rounded-md py-2 pl-8 pr-3 focus:outline-none focus:ring-2 focus:ring-blue-500 w-full sm:w-40 text-sm"
              @input="handleSearch"
            />
            <i
              class="fas fa-search absolute left-2 top-1/2 transform -translate-y-1/2 text-gray-400 text-sm"
            ></i>
          </div>

          <!-- 类目筛选 -->
          <select
            v-model="selectedCategoryId"
            @change="handleCategoryFilter"
            class="w-full sm:w-auto sm:min-w-[100px] sm:max-w-[200px] bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">全部类目</option>
            <option v-for="category in categories" :key="category.id" :value="category.id">
              {{ category.name }}
            </option>
          </select>

          <!-- 子类目筛选 -->
          <select
            v-model="selectedSubcategoryId"
            @change="handleSubcategoryFilter"
            class="w-full sm:w-auto sm:min-w-[100px] bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            :disabled="!selectedCategoryId"
          >
            <option value="">全部子类目</option>
            <option
              v-for="subcategory in filteredSubcategories"
              :key="subcategory.id"
              :value="subcategory.id"
            >
              {{ subcategory.name }}
            </option>
          </select>
        </div>

        <!-- 按钮盒子 -->
        <div
          class="flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center gap-2 sm:gap-3 sm:min-w-[340px]"
        >
          <!-- 刷新按钮 -->
          <button
            @click="refreshData"
            :disabled="gameStore.loading.items"
            class="w-full sm:w-auto sm:min-w-[70px] bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-3 py-2 rounded transition-colors text-xs font-medium"
          >
            <i
              class="fas fa-sync-alt mr-1"
              :class="{ 'animate-spin': gameStore.loading.items }"
            ></i>
            <span>刷新</span>
          </button>

          <!-- 排序按钮 -->
          <button
            @click="toggleSortMode"
            :class="[
              'w-full sm:w-auto sm:min-w-[70px] px-3 py-2 rounded transition-colors text-white text-xs font-medium',
              sortMode ? 'bg-blue-700 hover:bg-blue-800' : 'bg-blue-600 hover:bg-blue-700',
            ]"
          >
            <i :class="['mr-1', sortMode ? 'fas fa-check' : 'fas fa-sort']"></i>
            <span>{{ sortMode ? '完成' : '排序' }}</span>
          </button>

          <!-- 多选按钮/下拉菜单 -->
          <div class="relative" v-if="!multiSelectMode">
            <button
              @click="toggleMultiSelectMode"
              class="w-full sm:w-auto sm:min-w-[70px] bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded transition-colors text-xs font-medium"
            >
              <i class="fas fa-check-square mr-1"></i>
              <span>多选</span>
            </button>
          </div>
          <div class="relative" v-else>
            <button
              @click="showMultiSelectDropdown = !showMultiSelectDropdown"
              class="w-full sm:w-auto sm:min-w-[90px] bg-purple-700 hover:bg-purple-800 text-white px-3 py-2 rounded transition-colors flex items-center text-xs font-medium"
            >
              <i class="fas fa-check mr-1"></i>
              <span>操作</span>
              <i
                class="fas fa-chevron-down ml-1 text-xs"
                :class="{ 'rotate-180': showMultiSelectDropdown }"
              ></i>
            </button>

            <!-- 下拉菜单 - 改回相对定位 -->
            <div
              v-if="showMultiSelectDropdown"
              class="absolute right-0 top-full mt-1 min-w-[200px] bg-gray-700 border border-gray-600 rounded-md shadow-lg z-[9999]"
            >
              <button
                @click="batchToggleStatus(true)"
                :disabled="selectedItems.size === 0"
                class="w-full text-left px-4 py-2 text-sm text-white hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                <i class="fas fa-eye mr-2 text-green-400"></i>
                批量上架 ({{ selectedItems.size }})
              </button>
              <button
                @click="batchToggleStatus(false)"
                :disabled="selectedItems.size === 0"
                class="w-full text-left px-4 py-2 text-sm text-white hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                <i class="fas fa-eye-slash mr-2 text-yellow-400"></i>
                批量下架 ({{ selectedItems.size }})
              </button>
              <button
                @click="batchDelete"
                :disabled="selectedItems.size === 0"
                class="w-full text-left px-4 py-2 text-sm text-white hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                <i class="fas fa-trash mr-2 text-red-400"></i>
                批量删除 ({{ selectedItems.size }})
              </button>
              <hr class="border-gray-600 my-1" />
              <button
                @click="toggleMultiSelectMode"
                class="w-full text-left px-4 py-2 text-sm text-white hover:bg-gray-600 flex items-center"
              >
                <i class="fas fa-times mr-2 text-gray-400"></i>
                退出多选
              </button>
            </div>

            <!-- 点击外部关闭下拉菜单 -->
            <div
              v-if="showMultiSelectDropdown"
              @click="showMultiSelectDropdown = false"
              class="fixed inset-0 z-40"
            ></div>
          </div>

          <!-- 添加物品按钮 -->
          <button
            @click="openItemModal()"
            class="w-full sm:w-auto sm:min-w-[90px] bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded transition-colors text-xs font-medium"
          >
            <i class="fas fa-plus mr-1"></i>
            <span>上架</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 错误提示 -->
    <div
      v-if="gameStore.errors.items"
      class="mb-6 p-4 bg-red-900/50 border border-red-500 rounded-lg"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center">
          <i class="fas fa-exclamation-triangle text-red-400 mr-2"></i>
          <span class="text-red-200">{{ gameStore.errors.items }}</span>
        </div>
        <button @click="gameStore.clearError('items')" class="text-red-400 hover:text-red-300">
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
      <!-- 排序模式提示 -->
      <div v-if="sortMode" class="mb-4 p-3 bg-blue-900/30 border border-blue-500/50 rounded-lg">
        <div class="flex items-center">
          <i class="fas fa-info-circle text-blue-400 mr-2"></i>
          <span class="text-blue-200">排序模式已启用，您可以拖拽表格行来调整物品顺序</span>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="gameStore.loading.items && displayedItems.length === 0" class="text-center py-8">
        <i class="fas fa-spinner fa-spin text-2xl text-gray-400 mb-2"></i>
        <p class="text-gray-400">加载物品数据中...</p>
      </div>

      <!-- 空状态 -->
      <div
        v-else-if="!gameStore.loading.items && displayedItems.length === 0"
        class="text-center py-8"
      >
        <i class="fas fa-box-open text-4xl text-gray-500 mb-4"></i>
        <p class="text-gray-400 mb-4">
          {{ searchQuery || selectedCategoryId ? '没有找到匹配的物品' : '暂无物品数据' }}
        </p>
        <p class="text-sm text-gray-500">
          {{
            searchQuery || selectedCategoryId
              ? '尝试调整搜索条件'
              : '点击上方"上架新物品"按钮添加第一个物品'
          }}
        </p>
      </div>

      <!-- 数据表格 -->
      <div v-else class="overflow-x-auto" style="min-width: 0">
        <table class="w-full text-left" style="min-width: 1030px">
          <thead>
            <tr class="border-b border-gray-700">
              <th class="p-3 min-w-[60px] w-[60px] text-center">
                <div v-if="multiSelectMode" class="flex items-center justify-center">
                  <input
                    type="checkbox"
                    :checked="isAllSelected"
                    :indeterminate="isIndeterminate"
                    @change="toggleSelectAll"
                    class="w-4 h-4 text-purple-600 bg-gray-700 border-gray-600 rounded focus:ring-purple-500 focus:ring-2"
                  />
                </div>
                <span v-else>序号</span>
              </th>
              <th class="p-2 min-w-[70px] w-[70px] text-center">图片</th>
              <th class="p-2 min-w-[120px] w-[140px] text-center">物品名称</th>
              <th class="p-2 min-w-[180px] w-[200px] text-center">物品代码</th>
              <th class="p-2 min-w-[90px] w-[100px] text-center">类目</th>
              <th class="p-2 min-w-[90px] w-[100px] text-center">子类目</th>
              <th class="p-2 min-w-[70px] w-[80px] text-center">价格</th>
              <th class="p-2 min-w-[70px] w-[80px] text-center">库存</th>
              <th class="p-2 min-w-[60px] w-[70px] text-center">状态</th>
              <th class="p-2 min-w-[90px] w-[110px] text-center">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(item, index) in displayedItems"
              :key="item.id"
              class="border-b border-gray-700 hover:bg-gray-700/50 transition-all duration-200"
              :class="{
                'bg-gray-700/30 scale-98 opacity-80': sortMode && draggedItem === item.id,
                'bg-blue-900/20': sortMode && dragOverIndex === index && draggedItemIndex !== index,
                'bg-blue-900/10': sortMode,
              }"
              :draggable="sortMode && !multiSelectMode"
              @dragstart="handleDragStart(index, item.id)"
              @dragover.prevent="handleDragOver(index)"
              @dragenter.prevent="handleDragEnter(index)"
              @dragleave="handleDragLeave"
              @drop="handleDrop(index)"
              @dragend="handleDragEnd"
            >
              <td class="p-2 text-center">
                <!-- 多选模式下显示复选框 -->
                <div v-if="multiSelectMode" class="flex items-center justify-center">
                  <input
                    type="checkbox"
                    :checked="selectedItems.has(item.id)"
                    @change="toggleItemSelection(item.id)"
                    class="w-4 h-4 text-purple-600 bg-gray-700 border-gray-600 rounded focus:ring-purple-500 focus:ring-2"
                  />
                </div>
                <!-- 普通模式下显示序号 -->
                <span
                  v-else
                  :class="[
                    'text-sm font-medium',
                    sortMode && !multiSelectMode
                      ? 'text-blue-400 cursor-move'
                      : 'text-gray-400 cursor-default',
                  ]"
                  :title="sortMode && !multiSelectMode ? '拖拽排序' : '点击排序按钮进入排序模式'"
                >
                  {{ (currentPage - 1) * pageSize + index + 1 }}
                </span>
              </td>
              <td class="p-2 text-center">
                <!-- 使用缩略图提升加载性能，失败时自动回退到原图 -->
                <div
                  class="w-10 h-10 rounded-md overflow-hidden bg-gray-600 flex items-center justify-center mx-auto"
                >
                  <img
                    :src="getThumbnailUrl(item.image_url || item.image)"
                    :alt="item.name"
                    class="w-full h-full object-cover"
                    :class="{ 'opacity-50': item.is_active === false }"
                    @error="handleImageError"
                  />
                </div>
              </td>
              <td class="p-2 text-center">
                <div
                  class="font-medium text-base"
                  :class="{ 'opacity-50': item.is_active === false }"
                >
                  {{ item.name }}
                </div>
                <div
                  v-if="item.description"
                  class="text-sm text-gray-400 truncate max-w-xs mx-auto"
                  :class="{ 'opacity-50': item.is_active === false }"
                >
                  {{ item.description }}
                </div>
              </td>
              <td class="p-2 text-center">
                <textarea
                  :value="formatItemCodeForDisplay(item.item_code)"
                  readonly
                  class="w-full h-12 p-1 text-base font-mono bg-gray-800 border border-gray-600 rounded resize-none text-gray-300 text-center"
                  :class="{ 'opacity-50': item.is_active === false }"
                  :title="item.item_code || '未设置'"
                ></textarea>
              </td>
              <td class="p-2 text-center">
                <span class="text-base" :class="{ 'opacity-50': item.is_active === false }">{{
                  getCategoryName(item.categoryId || item.category_id)
                }}</span>
              </td>
              <td class="p-2 text-center">
                <span class="text-base" :class="{ 'opacity-50': item.is_active === false }">{{
                  getSubcategoryName(item.subcategoryId || item.subcategory_id)
                }}</span>
              </td>
              <td class="p-2 text-center">
                <span
                  class="font-medium text-base"
                  :class="{ 'opacity-50': item.is_active === false }"
                  >¥{{ (item.price || 0).toFixed(2) }}</span
                >
              </td>
              <td class="p-2 text-center">
                <span
                  :class="[
                    'font-medium text-base',
                    item.stock === -1
                      ? 'text-blue-400'
                      : item.stock === 0
                        ? 'text-red-400'
                        : item.stock <= 10
                          ? 'text-yellow-400'
                          : 'text-green-400',
                    { 'opacity-50': item.is_active === false },
                  ]"
                >
                  {{ item.stock === -1 ? '不限量' : item.stock || 0 }}
                </span>
              </td>
              <td class="p-2 text-center">
                <span
                  :class="[
                    'px-2 py-1 rounded-full text-sm font-medium inline-block',
                    item.is_active !== false
                      ? 'bg-green-900/50 text-green-400 border border-green-500/50'
                      : 'bg-red-900/50 text-red-400 border border-red-500/50',
                  ]"
                >
                  {{ item.is_active !== false ? '上架' : '下架' }}
                </span>
              </td>
              <td class="p-2 text-center">
                <button
                  @click="openItemModal(item)"
                  :disabled="item.updating || item.is_active === false"
                  class="text-blue-400 hover:text-blue-300 mr-2 disabled:opacity-50"
                  title="编辑"
                >
                  <i class="fas fa-edit text-base"></i>
                </button>
                <button
                  @click="toggleItemStatus(item)"
                  :disabled="item.updating"
                  class="text-yellow-400 hover:text-yellow-300 mr-2 disabled:opacity-50"
                  :title="item.is_active !== false ? '下架' : '上架'"
                >
                  <i
                    :class="
                      item.is_active !== false
                        ? 'fas fa-eye-slash text-base'
                        : 'fas fa-eye text-base'
                    "
                  ></i>
                </button>
                <button
                  @click="deleteItem(item.id)"
                  :disabled="item.updating || item.is_active === false"
                  class="text-red-500 hover:text-red-400 disabled:opacity-50"
                  title="删除"
                >
                  <i class="fas fa-trash text-base"></i>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 分页控件 -->
      <div
        v-if="totalPages > 1"
        class="flex flex-col sm:flex-row sm:justify-between sm:items-center mt-6 gap-4"
      >
        <div class="text-xs sm:text-sm text-gray-400 text-center sm:text-left">
          显示第 {{ (currentPage - 1) * pageSize + 1 }} -
          {{ Math.min(currentPage * pageSize, totalItems) }} 条，共 {{ totalItems }} 条
        </div>
        <div class="flex items-center justify-center gap-1 sm:gap-2">
          <button
            @click="previousPage"
            :disabled="currentPage === 1"
            class="px-2 sm:px-3 py-1 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded transition-colors text-xs sm:text-sm"
          >
            上一页
          </button>
          <div class="flex items-center gap-1">
            <button
              v-for="page in Math.min(totalPages, 5)"
              :key="page"
              @click="goToPage(page)"
              :class="page === currentPage ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'"
              class="px-2 sm:px-3 py-1 text-white rounded transition-colors text-xs sm:text-sm"
            >
              {{ page }}
            </button>
            <span v-if="totalPages > 5" class="text-gray-400 px-2">...</span>
          </div>
          <button
            @click="nextPage"
            :disabled="currentPage === totalPages"
            class="px-2 sm:px-3 py-1 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded transition-colors text-xs sm:text-sm"
          >
            下一页
          </button>
        </div>
      </div>
    </div>

    <!-- Item Modal - 相对于整个屏幕背景弹出 -->
    <teleport to="body">
      <div
        v-if="showModal"
        class="fixed inset-0 flex backdrop-blur-sm items-center justify-center z-[9999]"
      >
        <div
          class="bg-gray-800 bg-opacity-50 backdrop-blur-md rounded-lg shadow-2xl border border-gray-600 p-8 w-full max-w-2xl mx-4 transform transition-all duration-300 max-h-[90vh] overflow-y-auto"
          :class="modalAnimationClass"
          @click.stop
        >
          <form @submit.prevent="saveItem">
            <h3 class="text-xl font-bold mb-6 text-white">{{ modalTitle }}</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label for="item-name" class="block text-sm font-medium mb-1 text-white"
                  >物品名称</label
                >
                <input
                  v-model="form.name"
                  type="text"
                  id="item-name"
                  :disabled="isSubmitting"
                  class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 text-white"
                  required
                />
              </div>

              <!-- 图片上传组件 -->
              <div>
                <label for="item-image" class="block text-sm font-medium mb-1 text-white"
                  >物品图片</label
                >
                <div class="space-y-2">
                  <!-- 上传按钮和文件信息的水平布局 -->
                  <div class="flex gap-3 items-start">
                    <!-- 左侧：文件上传按钮 -->
                    <div class="flex-shrink-0">
                      <input
                        ref="imageInput"
                        type="file"
                        id="item-image"
                        accept="image/*"
                        @change="handleImageUpload"
                        :disabled="isSubmitting || isUploading"
                        class="hidden"
                      />
                      <button
                        type="button"
                        @click="$refs.imageInput.click()"
                        :disabled="isSubmitting || isUploading || !form.itemCode.trim()"
                        class="bg-gray-700 border border-gray-600 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 hover:bg-gray-600 transition-colors flex items-center gap-2 text-sm whitespace-nowrap text-white"
                      >
                        <i class="fas fa-cloud-upload-alt text-sm"></i>
                        <span v-if="!isUploading">{{
                          selectedImageFile ? '更换图片' : '选择图片'
                        }}</span>
                        <span v-else>上传中...</span>
                      </button>
                    </div>

                    <!-- 右侧：文件信息 -->
                    <div class="flex-1 min-w-0">
                      <!-- 物品代码提示信息 -->
                      <div v-if="!form.itemCode.trim()" class="text-xs text-yellow-400 mb-1">
                        <i class="fas fa-info-circle mr-1"></i>
                        请先输入物品代码
                      </div>

                      <!-- 上传状态信息 -->
                      <div
                        v-if="uploadMessage"
                        class="text-xs"
                        :class="uploadSuccess ? 'text-green-400' : 'text-red-400'"
                      >
                        {{ uploadMessage }}
                      </div>
                      <!-- 文件信息：文件名和大小 -->
                      <div v-if="selectedImageFile" class="text-xs text-white space-y-1">
                        <div class="flex items-center justify-between">
                          <span class="truncate mr-2">文件名：{{ selectedImageFile.name }}</span>
                          <button
                            type="button"
                            @click="clearSelectedFile"
                            :disabled="isSubmitting"
                            class="text-red-400 hover:text-red-300 disabled:opacity-50 flex-shrink-0"
                            title="清除文件"
                          >
                            <i class="fas fa-times text-xs"></i>
                          </button>
                        </div>
                        <div>大小：{{ formatFileSize(selectedImageFile.size) }}</div>
                      </div>

                      <!-- 已有图片信息 -->
                      <div
                        v-else-if="form.image"
                        class="text-xs text-white flex items-center justify-between"
                      >
                        <span>已有图片</span>
                        <button
                          type="button"
                          @click="clearExistingImage"
                          :disabled="isSubmitting"
                          class="text-red-400 hover:text-red-300 disabled:opacity-50"
                          title="清除图片"
                        >
                          <i class="fas fa-times text-xs"></i>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 主类目选择 -->
              <div class="relative">
                <label for="item-category" class="block text-sm font-medium mb-1 text-white"
                  >主类目</label
                >
                <div class="relative">
                  <!-- 主类目下拉框触发器 -->
                  <button
                    type="button"
                    @click="toggleCategoryDropdown"
                    :disabled="isSubmitting"
                    class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-left focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 flex justify-between items-center text-white"
                  >
                    <span>{{ selectedCategoryText }}</span>
                    <i
                      class="fas fa-chevron-down transition-transform"
                      :class="{ 'rotate-180': categoryDropdownOpen }"
                    ></i>
                  </button>

                  <!-- 主类目下拉菜单 -->
                  <div
                    v-if="categoryDropdownOpen"
                    class="absolute z-50 w-full mt-1 bg-gray-700 border border-gray-600 rounded-md shadow-lg max-h-60 overflow-y-auto"
                  >
                    <button
                      v-for="category in categories"
                      :key="category.id"
                      type="button"
                      @click="selectCategory(category)"
                      class="w-full px-3 py-2 text-left hover:bg-gray-600 text-white"
                      :class="{ 'bg-gray-600': form.categoryId == category.id }"
                    >
                      {{ category.name }}
                    </button>
                  </div>

                  <!-- 点击外部关闭下拉菜单 -->
                  <div
                    v-if="categoryDropdownOpen"
                    @click="closeCategoryDropdown"
                    class="fixed inset-0 z-40"
                  ></div>
                </div>
              </div>

              <!-- 子类目选择 -->
              <div class="relative">
                <label for="item-subcategory" class="block text-sm font-medium mb-1 text-white"
                  >子类目 <span class="text-gray-400 text-xs">(可选)</span></label
                >
                <div class="relative">
                  <!-- 子类目下拉框触发器 -->
                  <button
                    type="button"
                    @click="toggleSubcategoryDropdown"
                    :disabled="isSubmitting || !form.categoryId"
                    class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-left focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 flex justify-between items-center text-white"
                  >
                    <span>{{ selectedSubcategoryText }}</span>
                    <i
                      class="fas fa-chevron-down transition-transform"
                      :class="{ 'rotate-180': subcategoryDropdownOpen }"
                    ></i>
                  </button>

                  <!-- 子类目下拉菜单 -->
                  <div
                    v-if="subcategoryDropdownOpen && availableSubcategories.length > 0"
                    class="absolute z-50 w-full mt-1 bg-gray-700 border border-gray-600 rounded-md shadow-lg max-h-60 overflow-y-auto"
                  >
                    <button
                      type="button"
                      @click="selectSubcategory(null)"
                      class="w-full px-3 py-2 text-left hover:bg-gray-600 text-white"
                      :class="{ 'bg-gray-600': !form.subcategoryId }"
                    >
                      无子类目
                    </button>
                    <button
                      v-for="subcategory in availableSubcategories"
                      :key="subcategory.id"
                      type="button"
                      @click="selectSubcategory(subcategory)"
                      class="w-full px-3 py-2 text-left hover:bg-gray-600 text-white"
                      :class="{ 'bg-gray-600': form.subcategoryId == subcategory.id }"
                    >
                      {{ subcategory.name }}
                    </button>
                  </div>

                  <!-- 点击外部关闭下拉菜单 -->
                  <div
                    v-if="subcategoryDropdownOpen"
                    @click="closeSubcategoryDropdown"
                    class="fixed inset-0 z-40"
                  ></div>
                </div>
              </div>
              <div>
                <label for="item-price" class="block text-sm font-medium mb-1 text-white"
                  >价格</label
                >
                <input
                  v-model="form.price"
                  type="number"
                  id="item-price"
                  step="0.01"
                  min="0"
                  :disabled="isSubmitting"
                  class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 text-white"
                  required
                />
              </div>
              <div>
                <label for="item-stock" class="block text-sm font-medium mb-1 text-white"
                  >库存</label
                >
                <input
                  v-model="form.stock"
                  type="number"
                  id="item-stock"
                  min="-1"
                  :disabled="isSubmitting"
                  class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 text-white"
                  required
                />
              </div>
              <div class="md:col-span-2">
                <label for="item-code" class="block text-sm font-medium mb-1 text-white"
                  >物品代码</label
                >
                <textarea
                  v-model="form.itemCode"
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
                  v-if="form.itemCode.trim()"
                  class="mt-2 p-3 bg-gray-800 rounded-md border border-gray-600"
                >
                  <div class="text-xs text-white mb-1">JSON格式预览：</div>
                  <pre class="text-xs text-green-400 font-mono whitespace-pre-wrap">{{
                    itemCodePreview
                  }}</pre>
                </div>
              </div>

              <div class="md:col-span-2">
                <label for="item-description" class="block text-sm font-medium mb-1 text-white"
                  >物品描述</label
                >
                <textarea
                  v-model="form.description"
                  id="item-description"
                  rows="2"
                  :disabled="isSubmitting"
                  class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 text-white"
                  placeholder="输入物品的详细描述..."
                ></textarea>
              </div>
            </div>
            <div class="mt-8 flex justify-end gap-4">
              <button
                type="button"
                @click="closeItemModal"
                :disabled="isSubmitting"
                class="bg-gray-600 hover:bg-gray-700 disabled:opacity-50 text-white font-bold py-2 px-4 rounded transition-colors"
              >
                取消
              </button>
              <button
                type="submit"
                :disabled="isSubmitting || !form.name.trim() || !form.categoryId"
                class="bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white font-bold py-2 px-4 rounded transition-colors"
              >
                <i v-if="isSubmitting" class="fas fa-spinner fa-spin mr-2"></i>
                {{ isSubmitting ? '保存中...' : '保存物品' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import { useGameStore } from '@/stores/gameStore'
import { useSystemConfigStore } from '@/stores/systemConfigStore'
import { itemsApi } from '@/api/services/itemsApi'
import { fileToBase64, compressImage } from '@/utils/imageUpload'
import { API_CONFIG } from '@/api/config'

const gameStore = useGameStore()
const systemConfigStore = useSystemConfigStore()

// 响应式数据
const showModal = ref(false)
const isEditing = ref(false)
const editingItemId = ref(null)
const modalAnimationClass = ref('')
const isSubmitting = ref(false)
const successMessage = ref('')

// 图片上传相关数据
const selectedImageFile = ref(null)
const imagePreviewUrl = ref('')
const isUploading = ref(false)
const uploadMessage = ref('')
const uploadSuccess = ref(false)

// 搜索和筛选
const searchQuery = ref('')
const selectedCategoryId = ref('')
const selectedSubcategoryId = ref('')

// 分页相关
const currentPage = ref(1)
const pageSize = computed(() => systemConfigStore.itemsPerPage)

// 拖拽相关数据
const draggedItemIndex = ref(null)
const draggedItem = ref(null)
const dragOverIndex = ref(null)

// 排序模式状态
const sortMode = ref(false)

// 多选模式状态
const multiSelectMode = ref(false)
const selectedItems = ref(new Set())
const showMultiSelectDropdown = ref(false)

// 从store中获取数据
const categories = computed(() => gameStore.categories)
const subcategories = computed(() => gameStore.subcategories)
const items = computed(() => gameStore.items)

// 根据选中的类目筛选子类目
const filteredSubcategories = computed(() => {
  if (!selectedCategoryId.value) {
    return []
  }
  return subcategories.value.filter((sub) => sub.category_id == selectedCategoryId.value)
})

// 过滤后的物品列表（经过搜索和筛选，但未分页）
const filteredItems = computed(() => {
  let result = items.value

  // 类目筛选
  if (selectedCategoryId.value) {
    result = result.filter(
      (item) => (item.categoryId || item.category_id) == selectedCategoryId.value,
    )
  }

  // 子类目筛选
  if (selectedSubcategoryId.value) {
    result = result.filter(
      (item) => (item.subcategoryId || item.subcategory_id) == selectedSubcategoryId.value,
    )
  }

  // 搜索筛选
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase().trim()
    result = result.filter(
      (item) =>
        item.name.toLowerCase().includes(query) ||
        (item.description && item.description.toLowerCase().includes(query)),
    )
  }

  // 排序
  return result.sort((a, b) => (a.sortOrder || 0) - (b.sortOrder || 0))
})

// 分页计算属性
const totalItems = computed(() => filteredItems.value.length)
const totalPages = computed(() => Math.ceil(totalItems.value / pageSize.value))

// 显示的物品列表（分页后）
const displayedItems = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredItems.value.slice(start, end)
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

// 重置分页到第一页
const resetPagination = () => {
  currentPage.value = 1
}

// 表单数据
const form = reactive({
  name: '',
  itemCode: '',
  categoryId: '',
  subcategoryId: '',
  price: 0,
  stock: -1,
  description: '',
  image: '',
  pendingImageFile: null, // 用于存储待上传的图片文件
})

// 自定义下拉菜单状态
const categoryDropdownOpen = ref(false)
const subcategoryDropdownOpen = ref(false)

// 计算属性
const modalTitle = computed(() => (isEditing.value ? '编辑物品' : '上架新物品'))

// 获取当前选中的主类目显示文本
const selectedCategoryText = computed(() => {
  if (!form.categoryId) return '请选择主类目'

  const category = categories.value.find((c) => c.id == form.categoryId)
  return category ? category.name : '请选择主类目'
})

// 获取当前选中的子类目显示文本
const selectedSubcategoryText = computed(() => {
  if (!form.categoryId) return '请先选择主类目'
  if (!form.subcategoryId) return '请选择子类目'

  const subcategory = subcategories.value.find((s) => s.id == form.subcategoryId)
  return subcategory ? subcategory.name : '请选择子类目'
})

// 获取当前主类目下可用的子类目
const availableSubcategories = computed(() => {
  if (!form.categoryId) return []
  return subcategories.value.filter((sub) => sub.category_id == form.categoryId)
})

// 物品代码预览
const itemCodePreview = computed(() => {
  if (!form.itemCode.trim()) return ''

  try {
    const processed = processItemCode(form.itemCode.trim())
    // 格式化JSON以便更好地显示
    const parsed = JSON.parse(processed)
    return JSON.stringify(parsed, null, 2)
  } catch {
    return '格式错误：请使用 #命令 物品 数量 格式'
  }
})

// 将JSON格式的物品代码转换回命令格式
const convertJsonToCommands = (itemCode) => {
  if (!itemCode) return ''

  try {
    const parsed = JSON.parse(itemCode)

    // 如果是数组格式
    if (Array.isArray(parsed)) {
      const commands = []
      for (const item of parsed) {
        if (item.command && item.item) {
          const amount = item.amount || 1
          commands.push(`${item.command} ${item.item} ${amount}`)
        }
      }
      return commands.join('\n')
    }
  } catch {
    // 如果不是JSON格式，直接返回原始代码
  }

  return itemCode
}

// 搜索和筛选处理
const handleSearch = async () => {
  // 搜索时重置分页
  resetPagination()
  // 本地搜索已在 filteredItems 计算属性中处理
  // 如果需要服务器端搜索，可以在这里调用 API
}

const handleCategoryFilter = () => {
  // 当类目改变时，清空子类目选择
  selectedSubcategoryId.value = ''
  // 筛选时重置分页
  resetPagination()
  // 筛选逻辑已在 filteredItems 计算属性中处理
}

const handleSubcategoryFilter = () => {
  // 筛选时重置分页
  resetPagination()
  // 筛选逻辑已在 filteredItems 计算属性中处理
}

// 刷新数据
const refreshData = async () => {
  try {
    console.log('[Items] Starting data refresh...')
    await Promise.all([
      gameStore.loadCategories(),
      gameStore.loadSubcategories(),
      gameStore.loadItems(),
    ])
    console.log('[Items] Data refresh completed')
    console.log('[Items] Current data counts:', {
      categories: gameStore.categories.length,
      subcategories: gameStore.subcategories.length,
      items: gameStore.items.length,
    })

    successMessage.value = '数据刷新成功'
    setTimeout(() => {
      successMessage.value = ''
    }, 3000)
  } catch (error) {
    console.error('[Items] Failed to refresh data:', error)
  }
}

// 获取类目名称
const getCategoryName = (categoryId) => {
  const category = categories.value.find((c) => c.id === categoryId)
  return category ? category.name : '未分类'
}

// 获取子类目名称
const getSubcategoryName = (subcategoryId) => {
  if (!subcategoryId) return '无'
  const subcategory = subcategories.value.find((s) => s.id === subcategoryId)
  return subcategory ? subcategory.name : '未知'
}

// 图片加载错误处理
const handleImageError = (event) => {
  const currentSrc = event.target.src

  // 如果当前是新格式缩略图且加载失败，尝试加载原图
  if (currentSrc.includes('/thumbs/') && currentSrc.includes('-thumb.')) {
    // 将 /static/images/items/thumbs/filename-thumb.ext 转换为 /static/images/items/imgs/filename.ext
    const originalUrl = currentSrc.replace('/thumbs/', '/imgs/').replace('-thumb.', '.')
    event.target.src = originalUrl
    return
  }

  // 如果当前是旧格式缩略图且加载失败，尝试加载原图
  if (currentSrc.includes('-thumb.')) {
    const originalUrl = currentSrc.replace('-thumb.', '.')
    event.target.src = originalUrl
    return
  }

  // 如果原图也加载失败，显示占位图
  event.target.src = 'https://placehold.co/100x100/cccccc/666666?text=No+Image'
}

// 获取缩略图URL
const getThumbnailUrl = (imageUrl) => {
  if (!imageUrl) {
    return 'https://placehold.co/100x100/cccccc/666666?text=No+Image'
  }

  // 确保URL包含完整的后端服务器地址
  const getFullUrl = (url) => {
    if (url.startsWith('http')) {
      return url // 已经是完整URL
    }
    // 使用配置中的后端服务器地址
    return `${API_CONFIG.BASE_URL}${url}`
  }

  // 根据后端实际实现，物品图片URL格式：
  // 原图：/static/images/items/imgs/filename.jpg 或 /static/images/filename.jpg
  // 缩略图：/static/images/items/thumbs/filename-thumb.jpg 或 /static/images/filename-thumb.jpg
  if (imageUrl.includes('/static/images/items/imgs/')) {
    // 将原图路径转换为缩略图路径
    const filename = imageUrl.split('/').pop() // 获取文件名
    const lastDotIndex = filename.lastIndexOf('.')
    if (lastDotIndex > 0) {
      const nameWithoutExt = filename.substring(0, lastDotIndex)
      const extension = filename.substring(lastDotIndex)
      const thumbnailFilename = `${nameWithoutExt}-thumb${extension}`
      const thumbnailUrl = `/static/images/items/thumbs/${thumbnailFilename}`
      return getFullUrl(thumbnailUrl)
    }
  } else if (imageUrl.includes('/static/images/items/thumbs/')) {
    // 已经是缩略图路径
    return getFullUrl(imageUrl)
  } else if (imageUrl.includes('/static/images/items/')) {
    // 处理非标准路径，如 /static/images/items/updated_image.jpg
    const filename = imageUrl.split('/').pop()
    const lastDotIndex = filename.lastIndexOf('.')
    if (lastDotIndex > 0) {
      const nameWithoutExt = filename.substring(0, lastDotIndex)
      const extension = filename.substring(lastDotIndex)
      const thumbnailFilename = `${nameWithoutExt}-thumb${extension}`
      const thumbnailUrl = `/static/images/items/thumbs/${thumbnailFilename}`
      return getFullUrl(thumbnailUrl)
    }
  } else if (imageUrl.includes('/static/images/')) {
    // 兼容旧格式：检查是否已经是缩略图
    if (imageUrl.includes('-thumb.')) {
      return getFullUrl(imageUrl)
    }

    // 生成缩略图URL：在文件扩展名前添加-thumb（兼容旧格式）
    const lastDotIndex = imageUrl.lastIndexOf('.')
    if (lastDotIndex > 0) {
      const thumbnailUrl =
        imageUrl.substring(0, lastDotIndex) + '-thumb' + imageUrl.substring(lastDotIndex)
      return getFullUrl(thumbnailUrl)
    }
  }

  // 对于其他URL或无法生成缩略图的情况，返回原图
  return getFullUrl(imageUrl)
}

// 类目下拉菜单交互方法
const toggleCategoryDropdown = () => {
  categoryDropdownOpen.value = !categoryDropdownOpen.value
  // 关闭子类目下拉框
  if (categoryDropdownOpen.value) {
    subcategoryDropdownOpen.value = false
  }
}

const closeCategoryDropdown = () => {
  categoryDropdownOpen.value = false
}

const selectCategory = (category) => {
  form.categoryId = category.id
  form.subcategoryId = '' // 清空子类目选择
  closeCategoryDropdown()
}

// 子类目下拉菜单交互方法
const toggleSubcategoryDropdown = () => {
  if (!form.categoryId) return // 如果没有选择主类目，不允许打开子类目下拉框

  subcategoryDropdownOpen.value = !subcategoryDropdownOpen.value
  // 关闭主类目下拉框
  if (subcategoryDropdownOpen.value) {
    categoryDropdownOpen.value = false
  }
}

const closeSubcategoryDropdown = () => {
  subcategoryDropdownOpen.value = false
}

const selectSubcategory = (subcategory) => {
  if (subcategory) {
    form.subcategoryId = subcategory.id
  } else {
    form.subcategoryId = '' // 选择"无子类目"
  }
  closeSubcategoryDropdown()
}

// 重置表单
const resetForm = () => {
  form.name = ''
  form.itemCode = ''
  form.categoryId = ''
  form.subcategoryId = ''
  form.price = 0
  form.stock = -1
  form.description = ''
  form.image = ''
  form.pendingImageFile = null

  // 重置图片上传相关数据
  selectedImageFile.value = null
  imagePreviewUrl.value = ''
  uploadMessage.value = ''
  uploadSuccess.value = false
}

// 打开模态框
const openItemModal = (item = null) => {
  resetForm()

  if (item) {
    isEditing.value = true
    editingItemId.value = item.id
    form.name = item.name

    // 处理物品代码显示：如果是JSON格式，转换为原始命令格式
    const itemCode = item.item_code || ''
    form.itemCode = convertJsonToCommands(itemCode)

    form.categoryId = item.categoryId || item.category_id
    form.subcategoryId = item.subcategoryId || item.subcategory_id || ''
    form.price = item.price || 0
    form.stock = item.stock !== undefined ? item.stock : -1
    form.description = item.description || ''
    form.image = item.image || item.image_url || ''

    // 如果有现有图片，不显示预览URL（因为form.image已经有值）
    // 预览URL主要用于新上传的图片
    imagePreviewUrl.value = ''
  } else {
    isEditing.value = false
    editingItemId.value = null
  }

  showModal.value = true
  modalAnimationClass.value = 'scale-100 opacity-100'
}

// 关闭模态框
const closeItemModal = () => {
  modalAnimationClass.value = 'scale-95 opacity-0'
  setTimeout(() => {
    showModal.value = false
    resetForm()
  }, 300)
}

// 处理物品代码格式转换
const processItemCode = (itemCode) => {
  try {
    // 解析命令格式（支持单行和多行）
    const lines = itemCode.split('\n').filter((line) => line.trim())
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
        }
      }
    }

    // 如果成功解析到命令，返回JSON格式
    if (commands.length > 0) {
      return JSON.stringify(commands)
    }
  } catch (error) {
    console.warn('[ItemsView] Failed to parse item code:', error)
  }

  // 如果解析失败，抛出错误
  throw new Error('Invalid item code format')
}

// 保存物品
const saveItem = async () => {
  if (!form.name.trim()) {
    alert('物品名称不能为空')
    return
  }

  if (!form.itemCode.trim()) {
    alert('物品代码不能为空')
    return
  }

  if (!form.categoryId) {
    alert('请选择类目')
    return
  }

  isSubmitting.value = true
  try {
    // 处理物品代码格式转换
    const processedItemCode = processItemCode(form.itemCode.trim())

    let itemData

    if (isEditing.value && editingItemId.value) {
      // 更新物品：发送完整的可更新字段
      itemData = {
        name: form.name.trim(),
        item_code: processedItemCode,
        category_id: parseInt(form.categoryId),
        description: form.description.trim(),
        price: parseFloat(form.price) || 0,
        stock: parseInt(form.stock),
        image_url: form.image.trim() || 'https://placehold.co/100x100/cccccc/000000?text=New',
        is_active: true, // 默认为激活状态
      }

      // 只有当subcategoryId有值且大于0时才添加subcategory_id字段
      if (form.subcategoryId && parseInt(form.subcategoryId) > 0) {
        itemData['subcategory_id'] = parseInt(form.subcategoryId)
      }

      await gameStore.updateItem(editingItemId.value, itemData)

      // 如果有待上传的图片文件，现在上传它
      if (form.pendingImageFile) {
        try {
          console.log('[Items] Uploading pending image file for update...')
          const compressedFile = await compressImage(form.pendingImageFile, 800, 600, 0.8)
          const uploadResponse = await gameStore.uploadItemImage(processedItemCode, compressedFile)

          if (uploadResponse.success) {
            console.log('[Items] Pending image uploaded successfully for update')
            successMessage.value = '物品更新成功，图片上传成功'
          } else {
            console.warn(
              '[Items] Failed to upload pending image for update:',
              uploadResponse.message,
            )
            successMessage.value = '物品更新成功，但图片上传失败'
          }
        } catch (imageError) {
          console.error('[Items] Failed to upload pending image for update:', imageError)
          successMessage.value = '物品更新成功，但图片上传失败'
        }
      } else {
        successMessage.value = '物品更新成功'
      }
    } else {
      // 创建物品：发送完整的创建数据
      itemData = {
        name: form.name.trim(),
        item_code: processedItemCode, // 使用处理后的物品代码，保持与更新逻辑一致
        category_id: parseInt(form.categoryId),
        price: parseFloat(form.price) || 0,
        stock: parseInt(form.stock),
        description: form.description.trim(),
        image_url: form.image.trim() || 'https://placehold.co/100x100/cccccc/000000?text=New',
      }

      // 只有当subcategoryId有值且大于0时才添加subcategory_id字段
      if (form.subcategoryId && parseInt(form.subcategoryId) > 0) {
        itemData['subcategory_id'] = parseInt(form.subcategoryId)
      }

      const createResponse = await gameStore.addItem(itemData)

      // 如果有待上传的图片文件，现在上传它
      if (form.pendingImageFile && createResponse.success) {
        try {
          console.log('[Items] Uploading pending image file...')
          const compressedFile = await compressImage(form.pendingImageFile, 800, 600, 0.8)
          const uploadResponse = await gameStore.uploadItemImage(processedItemCode, compressedFile)

          if (uploadResponse.success) {
            console.log('[Items] Pending image uploaded successfully')

            // 图片上传成功后，更新物品的图片URL
            if (createResponse.data && createResponse.data.id) {
              try {
                await gameStore.updateItem(createResponse.data.id, {
                  image_url: uploadResponse.data.image_url,
                })
                console.log('[Items] Item image URL updated after upload')
              } catch (updateError) {
                console.warn('[Items] Failed to update item image URL:', updateError)
              }
            }

            successMessage.value = '物品添加成功，图片上传成功'
          } else {
            console.warn('[Items] Failed to upload pending image:', uploadResponse.message)
            successMessage.value = '物品添加成功，但图片上传失败'
          }
        } catch (imageError) {
          console.error('[Items] Failed to upload pending image:', imageError)
          successMessage.value = '物品添加成功，但图片上传失败'
        }
      } else {
        successMessage.value = '物品添加成功'
      }
    }

    closeItemModal()

    setTimeout(() => {
      successMessage.value = ''
    }, 3000)
  } catch (error) {
    console.error('[Items] Failed to save item:', error)
    alert('保存物品失败: ' + error.message)
  } finally {
    isSubmitting.value = false
  }
}

// 切换物品状态
const toggleItemStatus = async (item) => {
  const newStatus = item.is_active === false
  const action = newStatus ? '上架' : '下架'

  // 构建简化的确认消息
  let confirmMessage = `确定要${action}物品"${item.name}"吗？\n\n确定要继续吗？`

  if (!confirm(confirmMessage)) return

  // 立即禁用当前条目的所有按钮（除了上架/下架按钮）
  item.updating = true
  try {
    const response = await itemsApi.updateItemActiveStatus(item.id, newStatus)

    if (response.data?.success) {
      // 更新本地数据
      item.is_active = newStatus

      successMessage.value = `物品${action}成功`
      setTimeout(() => {
        successMessage.value = ''
      }, 3000)

      // 刷新数据以确保同步
      await gameStore.loadItems()
    }
  } catch (error) {
    console.error('[Items] Failed to toggle item status:', error)
    alert(`${action}物品失败: ` + error.message)
  } finally {
    item.updating = false
  }
}

// 删除物品
const deleteItem = async (id) => {
  const item = displayedItems.value.find((i) => i.id === id)
  if (!item) return

  if (!confirm('确定要删除这个物品吗？此操作不可撤销。')) return

  item.updating = true
  try {
    await gameStore.deleteItem(id)

    successMessage.value = '物品删除成功'
    setTimeout(() => {
      successMessage.value = ''
    }, 3000)
  } catch (error) {
    console.error('[Items] Failed to delete item:', error)
    alert('删除物品失败: ' + error.message)
  } finally {
    if (item) {
      item.updating = false
    }
  }
}

// 切换排序模式
const toggleSortMode = () => {
  sortMode.value = !sortMode.value

  // 退出排序模式时清理拖拽状态
  if (!sortMode.value) {
    draggedItemIndex.value = null
    draggedItem.value = null
    dragOverIndex.value = null
  }

  // 退出排序模式时也退出多选模式
  if (!sortMode.value && multiSelectMode.value) {
    multiSelectMode.value = false
    selectedItems.value.clear()
  }
}

// 切换多选模式
const toggleMultiSelectMode = () => {
  multiSelectMode.value = !multiSelectMode.value

  // 退出多选模式时清空选中项和隐藏下拉菜单
  if (!multiSelectMode.value) {
    selectedItems.value.clear()
    showMultiSelectDropdown.value = false
  }

  // 退出多选模式时也退出排序模式
  if (!multiSelectMode.value && sortMode.value) {
    sortMode.value = false
    draggedItemIndex.value = null
    draggedItem.value = null
    dragOverIndex.value = null
  }
}

// 切换单个物品的选中状态
const toggleItemSelection = (itemId) => {
  if (selectedItems.value.has(itemId)) {
    selectedItems.value.delete(itemId)
  } else {
    selectedItems.value.add(itemId)
  }
}

// 全选/取消全选
const toggleSelectAll = () => {
  if (selectedItems.value.size === displayedItems.value.length) {
    // 当前全选，取消全选
    selectedItems.value.clear()
  } else {
    // 全选当前页面的所有物品
    selectedItems.value.clear()
    displayedItems.value.forEach((item) => {
      selectedItems.value.add(item.id)
    })
  }
}

// 检查是否全选
const isAllSelected = computed(() => {
  return displayedItems.value.length > 0 && selectedItems.value.size === displayedItems.value.length
})

// 检查是否部分选中
const isIndeterminate = computed(() => {
  return selectedItems.value.size > 0 && selectedItems.value.size < displayedItems.value.length
})

// 批量切换状态（上架/下架）
const batchToggleStatus = async (newStatus) => {
  if (selectedItems.value.size === 0) return

  const selectedItemIds = Array.from(selectedItems.value)
  const action = newStatus ? '上架' : '下架'

  if (!confirm(`确定要${action}选中的 ${selectedItemIds.length} 个物品吗？`)) return

  showMultiSelectDropdown.value = false

  try {
    // 批量更新状态
    const promises = selectedItemIds.map(async (itemId) => {
      const item = displayedItems.value.find((i) => i.id === itemId)
      if (item) {
        item.updating = true
        try {
          const response = await itemsApi.updateItemActiveStatus(itemId, newStatus)
          if (response.data?.success) {
            item.is_active = newStatus
          }
        } catch (error) {
          console.error(`[Items] Failed to ${action} item ${itemId}:`, error)
        } finally {
          item.updating = false
        }
      }
    })

    await Promise.all(promises)

    // 刷新数据以确保同步
    await gameStore.loadItems()

    successMessage.value = `批量${action}成功`
    setTimeout(() => {
      successMessage.value = ''
    }, 3000)

    // 清空选中项
    selectedItems.value.clear()
  } catch (error) {
    console.error(`[Items] Failed to batch ${action}:`, error)
    alert(`批量${action}失败: ` + error.message)
  }
}

// 批量删除
const batchDelete = async () => {
  if (selectedItems.value.size === 0) return

  const selectedItemIds = Array.from(selectedItems.value)

  if (!confirm(`确定要删除选中的 ${selectedItemIds.length} 个物品吗？此操作不可撤销。`)) return

  showMultiSelectDropdown.value = false

  try {
    // 批量删除
    const promises = selectedItemIds.map(async (itemId) => {
      const item = displayedItems.value.find((i) => i.id === itemId)
      if (item) {
        item.updating = true
        try {
          await gameStore.deleteItem(itemId)
        } catch (error) {
          console.error(`[Items] Failed to delete item ${itemId}:`, error)
        }
      }
    })

    await Promise.all(promises)

    successMessage.value = `批量删除成功`
    setTimeout(() => {
      successMessage.value = ''
    }, 3000)

    // 清空选中项
    selectedItems.value.clear()
  } catch (error) {
    console.error('[Items] Failed to batch delete:', error)
    alert('批量删除失败: ' + error.message)
  }
}

// 拖拽处理函数
const handleDragStart = (index, itemId) => {
  if (!sortMode.value || multiSelectMode.value) return
  draggedItemIndex.value = index
  draggedItem.value = itemId
}

const handleDragOver = (index) => {
  if (!sortMode.value || multiSelectMode.value) return
  if (draggedItemIndex.value !== null && draggedItemIndex.value !== index) {
    dragOverIndex.value = index
  }
}

const handleDragEnter = (index) => {
  if (!sortMode.value || multiSelectMode.value) return
  if (draggedItemIndex.value !== null && draggedItemIndex.value !== index) {
    dragOverIndex.value = index
  }
}

const handleDragLeave = () => {
  if (!sortMode.value || multiSelectMode.value) return
  dragOverIndex.value = null
}

const handleDrop = async (toIndex) => {
  if (!sortMode.value || multiSelectMode.value) return
  if (draggedItemIndex.value !== null && draggedItemIndex.value !== toIndex) {
    try {
      // 获取当前显示的物品列表的副本
      const itemsCopy = [...displayedItems.value]

      // 从原位置移除物品
      const [movedItem] = itemsCopy.splice(draggedItemIndex.value, 1)

      // 插入到新位置
      itemsCopy.splice(toIndex, 0, movedItem)

      // 更新sortOrder以反映新的顺序
      itemsCopy.forEach((item, index) => {
        item.sortOrder = (index + 1) * 100 // 使用100的间隔，便于后续插入
      })

      // 准备API调用数据
      const sortUpdates = itemsCopy.map((item, index) => ({
        id: parseInt(item.id),
        sort_order: (index + 1) * 100,
      }))

      // 准备请求数据
      const requestData = {
        items: sortUpdates,
      }

      // 只有在有分类ID时才添加
      if (selectedCategoryId.value) {
        requestData.category_id = parseInt(selectedCategoryId.value)
      }

      // 调用API保存新的排序到服务器
      await itemsApi.updateItemsSort(requestData)

      // 更新store中的items数组
      const allItems = [...gameStore.items]
      itemsCopy.forEach((updatedItem) => {
        const originalIndex = allItems.findIndex((item) => item.id === updatedItem.id)
        if (originalIndex !== -1) {
          allItems[originalIndex] = updatedItem
        }
      })

      console.log('[Items] Items reordered successfully')

      // 显示成功消息
      successMessage.value = '物品排序已保存'
      setTimeout(() => {
        successMessage.value = ''
      }, 3000)
    } catch (error) {
      console.error('[Items] Failed to reorder items:', error)

      // 显示错误消息
      successMessage.value = `排序保存失败: ${error.message || '未知错误'}`
      setTimeout(() => {
        successMessage.value = ''
      }, 5000)

      // 重新加载数据以恢复原始状态
      await gameStore.loadItems()
    }
  }
  dragOverIndex.value = null
}

const handleDragEnd = () => {
  if (!sortMode.value || multiSelectMode.value) return
  draggedItemIndex.value = null
  draggedItem.value = null
  dragOverIndex.value = null
}

// 图片上传相关方法
const handleImageUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  // 检查是否有物品代码
  if (!form.itemCode || !form.itemCode.trim()) {
    uploadMessage.value = '请先输入物品代码再上传图片'
    uploadSuccess.value = false
    return
  }

  selectedImageFile.value = file
  uploadMessage.value = ''
  uploadSuccess.value = false

  try {
    // 生成预览URL
    imagePreviewUrl.value = await fileToBase64(file)

    // 检查物品代码是否为复杂的多行JSON格式
    const itemCode = form.itemCode.trim()
    const isComplexCode = itemCode.includes('\n') || itemCode.includes('#spawnitem')

    if (isComplexCode) {
      // 对于复杂的物品代码，暂时只显示预览，不立即上传
      uploadMessage.value = '图片已选择，将在保存物品时一起上传'
      uploadSuccess.value = true
      // 将图片文件保存到表单中，稍后上传
      form.pendingImageFile = file
      return
    }

    // 对于简单的物品代码，立即上传
    isUploading.value = true
    uploadMessage.value = '正在上传图片...'

    // 可选：压缩图片
    const compressedFile = await compressImage(file, 800, 600, 0.8)

    // 使用专门的物品图片上传API
    const response = await gameStore.uploadItemImage(itemCode, compressedFile)

    if (response.success) {
      // 使用后端API返回的正确字段名
      form.image = response.data.image_url
      uploadMessage.value = response.message || '图片上传成功'
      uploadSuccess.value = true
    } else {
      uploadMessage.value = response.message || '图片上传失败'
      uploadSuccess.value = false
    }
  } catch (error) {
    console.error('图片上传失败:', error)
    uploadMessage.value = error.message || '图片上传失败，请重试'
    uploadSuccess.value = false
  } finally {
    isUploading.value = false
  }
}

// 清除选中的文件
const clearSelectedFile = () => {
  selectedImageFile.value = null
  imagePreviewUrl.value = ''
  uploadMessage.value = ''
  uploadSuccess.value = false

  // 清空文件输入框
  const imageInput = document.getElementById('item-image')
  if (imageInput) {
    imageInput.value = ''
  }
}

// 清除现有图片
const clearExistingImage = () => {
  form.image = ''
  selectedImageFile.value = null
  imagePreviewUrl.value = ''
  uploadMessage.value = ''
  uploadSuccess.value = false

  // 清空文件输入框
  const imageInput = document.getElementById('item-image')
  if (imageInput) {
    imageInput.value = ''
  }
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 组件挂载时加载数据
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
  if (items.value.length === 0) {
    await gameStore.loadItems()
  }
})

// 格式化物品代码显示
const formatItemCodeForDisplay = (itemCode) => {
  if (!itemCode || itemCode === '未设置') return '未设置'

  // 尝试解析JSON数组格式
  try {
    const parsed = JSON.parse(itemCode)

    // 如果是数组格式，转换为完整的命令格式
    if (Array.isArray(parsed)) {
      const itemCodeLines = parsed
        .map((item) => {
          if (item.command && item.item) {
            const amount = item.amount || 1
            return `${item.command} ${item.item} ${amount}`
          }
          return ''
        })
        .filter((line) => line)

      return itemCodeLines.join('\n')
    }

    // 如果是对象格式，转换为命令格式
    if (typeof parsed === 'object' && parsed !== null) {
      // 如果有item字段，转换为命令格式
      if (parsed.item) {
        const amount = parsed.amount || 1
        const command = parsed.command || '#spawnitem'
        return `${command} ${parsed.item} ${amount}`
      }

      // 如果是字典格式 {"item_name": quantity}
      const entries = Object.entries(parsed)
      if (entries.length > 0) {
        const itemCodeLines = entries.map(([itemName, quantity]) => {
          return `#spawnitem ${itemName} ${quantity || 1}`
        })
        return itemCodeLines.join('\n')
      }
    }
  } catch {
    // JSON解析失败，返回原始字符串
  }

  // 普通字符串或解析失败，直接返回
  return itemCode
}
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

.opacity-0 {
  opacity: 0;
}

.opacity-100 {
  opacity: 1;
}

/* 拖拽相关样式 */
tr[draggable='true'] {
  transition: background-color 0.2s ease;
}

tr[draggable='true']:hover {
  cursor: move;
}

.cursor-move {
  cursor: move;
}

/* 拖拽时的视觉反馈 */
.scale-98 {
  transform: scale(0.98);
}

.opacity-80 {
  opacity: 0.8;
}

/* 拖拽悬停效果 */
.bg-blue-900\/20 {
  background-color: rgba(30, 58, 138, 0.2);
  border-left: 3px solid #3b82f6;
}

/* 拖拽手柄样式 */
.fa-grip-vertical {
  transition: color 0.2s ease;
}

.fa-grip-vertical:hover {
  color: #9ca3af;
}

/* 拖拽提示效果 */
tbody tr:hover .fa-grip-vertical {
  color: #6b7280;
}

/* 下拉箭头旋转动画 */
.rotate-180 {
  transform: rotate(180deg);
  transition: transform 0.2s ease;
}

.fa-chevron-down {
  transition: transform 0.2s ease;
}
</style>
