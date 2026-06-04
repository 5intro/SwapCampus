<script setup>
defineProps({
  modelValue: { type: Number, default: 0 },
  size: { type: String, default: 'default' },
  readonly: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])
</script>

<template>
  <div class="star-rating" :class="{ readonly: readonly }">
    <span
      v-for="star in 5"
      :key="star"
      class="star"
      :class="{
        active: star <= modelValue,
      }"
      :style="{ fontSize: size === 'large' ? '24px' : '18px' }"
      @click="!readonly && emit('update:modelValue', star)"
    >
      {{ star <= modelValue ? '★' : '☆' }}
    </span>
  </div>
</template>

<style scoped>
.star-rating {
  display: inline-flex;
  gap: 2px;
}

.star {
  color: #ddd;
  cursor: pointer;
  transition: color 0.15s ease;
  user-select: none;
}

.star.active {
  color: #f7ba2a;
}

.star-rating.readonly .star {
  cursor: default;
}
</style>
