<template>
  <div class="mb-6">
    <div class="flex items-center overflow-x-auto custom-scrollbar pb-2 -mb-2">
      <div class="flex items-center gap-2">
        <button
          v-for="category in categories"
          :key="category"
          @click="selectCategory(category)"
          :class="['category-btn', { active: activeCategory === category }]"
        >
          {{ category }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CategoryButtons',
  props: {
    categories: {
      type: Array,
      required: true,
    },
    activeCategory: {
      type: String,
      required: true,
    },
  },
  emits: ['category-selected'],
  methods: {
    selectCategory(category) {
      this.$emit('category-selected', category)
    },
  },
}
</script>

<style scoped>
.category-btn {
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: rgb(209 213 219);
  background-color: rgba(55, 65, 81, 0.5);
  border-radius: 0.375rem;
  white-space: nowrap;
  transition: background-color 0.2s;
}

.category-btn:hover {
  background-color: rgb(75 85 99);
}

.category-btn.active {
  background-color: rgb(37 99 235);
  color: white;
}

/* Custom scrollbar for better aesthetics */
.custom-scrollbar::-webkit-scrollbar {
  height: 8px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(31, 41, 55, 0.5);
  border-radius: 10px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(75, 85, 99, 0.7);
  border-radius: 10px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(107, 114, 128, 0.8);
}
</style>
