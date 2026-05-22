<template>
  <div class="grid gap-4 responsive-grid">
    <div
      v-for="item in items"
      :key="item.id"
      class="bg-gray-900 bg-opacity-50 rounded-lg p-3 flex flex-col text-center transition-transform transform hover:-translate-y-1"
    >
      <div class="relative mb-2">
        <img
          :src="item.image"
          :alt="item.name"
          class="w-full h-24 md:h-28 object-cover rounded-md mx-auto"
        />
      </div>
      <h3 class="text-sm font-semibold text-white mb-1 flex-grow">{{ item.name }}</h3>
      <p v-if="item.stock !== -1" class="text-xs text-gray-400 mb-1">库存: {{ item.stock }}</p>
      <p
        class="text-sm font-bold mb-2"
        :class="item.isPriceValid ? 'text-yellow-400' : 'text-red-400'"
      >
        <span v-if="item.isPriceValid">售价: {{ item.price.toFixed(2) }}</span>
        <span v-else>价格待定</span>
      </p>
      <div class="flex items-center justify-center gap-1">
        <input
          v-model="item.quantity"
          type="number"
          :min="1"
          :max="item.stock"
          :disabled="!item.isPriceValid"
          class="bg-gray-800 border border-gray-600 rounded-md p-1 text-center w-12 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        />
        <button
          @click="addToCart(item)"
          :disabled="!item.isPriceValid"
          :class="[
            'flex-grow rounded-md p-1.5 transition-colors',
            item.isPriceValid
              ? 'bg-green-600 hover:bg-green-700 text-white cursor-pointer'
              : 'bg-gray-600 text-gray-400 cursor-not-allowed',
          ]"
          :title="item.isPriceValid ? '加入购物车' : '商品价格待定，暂时无法购买'"
        >
          <i class="fas fa-cart-plus"></i>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ItemGrid',
  props: {
    items: {
      type: Array,
      required: true,
    },
  },
  emits: ['add-to-cart'],
  methods: {
    addToCart(item) {
      this.$emit('add-to-cart', item)
    },
  },
}
</script>

<style scoped>
.bg-opacity-50 {
  background-color: rgba(17, 24, 39, 0.5);
}

.responsive-grid {
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
}

/* 响应式网格调整 */
@media (max-width: 640px) {
  .responsive-grid {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 0.75rem;
  }
}

@media (min-width: 641px) and (max-width: 768px) {
  .responsive-grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  }
}

@media (min-width: 769px) and (max-width: 1024px) {
  .responsive-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  }
}

@media (min-width: 1025px) and (max-width: 1440px) {
  .responsive-grid {
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  }
}

@media (min-width: 1441px) {
  .responsive-grid {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  }
}

/* 高DPI屏幕优化 */
@media (-webkit-min-device-pixel-ratio: 1.5), (min-resolution: 144dpi) {
  .responsive-grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 0.75rem;
  }
}
</style>
