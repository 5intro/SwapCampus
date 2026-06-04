<script setup>
import { formatPrice, formatTime, conditionLabels, conditionColors } from '@/utils/format'
import { useRouter } from 'vue-router'

const props = defineProps({
  product: {
    type: Object,
    required: true,
  },
})

const router = useRouter()

function goDetail() {
  router.push(`/product/${props.product.id}`)
}
</script>

<template>
  <el-card
    shadow="hover"
    class="product-card"
    :body-style="{ padding: '0' }"
    @click="goDetail"
  >
    <div class="card-image-wrap">
      <el-image
        v-if="product.cover_image"
        :src="product.cover_image"
        fit="cover"
        class="card-image"
        lazy
      >
        <template #error>
          <div class="image-placeholder">
            <el-icon :size="40"><component :is="'Picture'" /></el-icon>
          </div>
        </template>
      </el-image>
      <div v-else class="image-placeholder">
        <el-icon :size="40"><component :is="'Picture'" /></el-icon>
      </div>

      <el-tag
        v-if="product.condition"
        :type="conditionColors[product.condition] || 'info'"
        size="small"
        class="condition-tag"
      >
        {{ conditionLabels[product.condition] || product.condition_display }}
      </el-tag>

      <div v-if="product.status !== 'active'" class="status-overlay">
        <el-tag type="info" size="large">已售出</el-tag>
      </div>
    </div>

    <div class="card-body">
      <h3 class="card-title">{{ product.title }}</h3>

      <div class="card-price-row">
        <span class="card-price">{{ formatPrice(product.price) }}</span>
        <span v-if="product.original_price" class="card-original-price">
          {{ formatPrice(product.original_price) }}
        </span>
      </div>

      <div class="card-meta">
        <div class="card-seller">
          <el-avatar :size="20" class="seller-avatar">
            {{ product.seller?.nickname?.[0] || '?' }}
          </el-avatar>
          <span>{{ product.seller?.nickname }}</span>
        </div>
        <span class="card-time">{{ formatTime(product.created_at) }}</span>
      </div>
    </div>
  </el-card>
</template>

<style scoped>
.product-card {
  cursor: pointer;
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.2s ease;
}

.product-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-hover);
}

.card-image-wrap {
  position: relative;
  width: 100%;
  padding-top: 75%;
  overflow: hidden;
  background: #f0f0f0;
}

.card-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.image-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #e8f5e9, #f1f8e9);
  color: #a5d6a7;
}

.condition-tag {
  position: absolute;
  top: 8px;
  left: 8px;
}

.status-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-body {
  padding: 14px 16px 16px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 10px;
  color: var(--text-primary);
}

.card-price-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 10px;
}

.card-price {
  font-size: 18px;
  font-weight: 700;
  color: #e65100;
}

.card-original-price {
  font-size: 13px;
  color: var(--text-secondary);
  text-decoration: line-through;
}

.card-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: var(--text-secondary);
}

.card-seller {
  display: flex;
  align-items: center;
  gap: 6px;
}

.seller-avatar {
  font-size: 12px;
}
</style>
