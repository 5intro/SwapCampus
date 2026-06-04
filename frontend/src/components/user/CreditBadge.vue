<script setup>
import { computed } from 'vue'
import { creditLevelLabels, creditLevelColors } from '@/utils/format'

const props = defineProps({
  score: { type: Number, default: 100 },
  level: { type: String, default: 'good' },
  size: { type: String, default: 'default' },
})

const color = computed(() => creditLevelColors[props.level] || '#409eff')
const label = computed(() => creditLevelLabels[props.level] || '信用良好')
</script>

<template>
  <el-tooltip :content="`信用分: ${score}`" placement="top">
    <span
      class="credit-badge"
      :class="`credit-badge--${size}`"
      :style="{ color: color, borderColor: color }"
    >
      {{ label }}
      <span class="credit-score">{{ score }}</span>
    </span>
  </el-tooltip>
</template>

<style scoped>
.credit-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 10px;
  border: 1px solid;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
}

.credit-badge--small {
  font-size: 11px;
  padding: 1px 8px;
}

.credit-score {
  font-weight: 600;
}
</style>
