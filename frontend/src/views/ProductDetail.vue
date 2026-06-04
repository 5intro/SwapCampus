<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getProduct } from '@/api/products'
import { createOrder } from '@/api/transactions'
import { createConversation } from '@/api/chat'
import { ElMessage, ElMessageBox } from 'element-plus'
import CreditBadge from '@/components/user/CreditBadge.vue'
import {
  formatPrice, formatTime, formatDateTime,
  conditionLabels, conditionColors,
} from '@/utils/format'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const product = ref(null)
const loading = ref(true)
const activeImageIndex = ref(0)

onMounted(async () => {
  try {
    const res = await getProduct(route.params.id)
    product.value = res.data.data || res.data
  } catch {
    ElMessage.error('商品不存在')
    router.push('/')
  } finally {
    loading.value = false
  }
})

async function handleBuy() {
  if (!auth.isLoggedIn) {
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }

  try {
    await ElMessageBox.prompt('请输入面交地点（可选）', '确认下单', {
      inputPlaceholder: '如：图书馆门口',
      confirmButtonText: '确认下单',
      cancelButtonText: '取消',
    })

    await createOrder({
      product_id: product.value.id,
      meet_location: undefined,
    })
    ElMessage.success('下单成功，等待卖家确认')
    router.push('/my-orders')
  } catch {
    if (arguments.length === 0) return // cancel
    ElMessage.error('下单失败')
  }
}

async function handleContact() {
  if (!auth.isLoggedIn) {
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }

  try {
    const res = await createConversation({
      participant_id: product.value.seller.id,
      product: product.value.id,
    })
    const conv = res.data.data || res.data
    router.push(`/chat/${conv.id}`)
  } catch {
    ElMessage.error('无法发起会话')
  }
}

function isSeller() {
  return auth.user && product.value && auth.user.id === product.value.seller?.id
}
</script>

<template>
  <div class="page-container" v-loading="loading">
    <div v-if="product" class="detail-layout">
      <!-- Images -->
      <div class="detail-images">
        <div class="main-image">
          <el-image
            v-if="product.images?.[activeImageIndex]?.image"
            :src="product.images[activeImageIndex].image"
            fit="contain"
            class="main-img"
          />
          <div v-else class="no-image">
            <el-icon :size="80"><component :is="'Picture'" /></el-icon>
          </div>
        </div>
        <div v-if="product.images?.length > 1" class="thumb-list">
          <div
            v-for="(img, i) in product.images"
            :key="img.id"
            class="thumb"
            :class="{ active: i === activeImageIndex }"
            @click="activeImageIndex = i"
          >
            <el-image :src="img.image" fit="cover" />
          </div>
        </div>
      </div>

      <!-- Info -->
      <div class="detail-info">
        <el-tag
          v-if="product.condition"
          :type="conditionColors[product.condition] || 'info'"
          size="small"
        >
          {{ conditionLabels[product.condition] || product.condition_display }}
        </el-tag>

        <h1 class="detail-title">{{ product.title }}</h1>

        <div class="detail-price-row">
          <span class="detail-price">{{ formatPrice(product.price) }}</span>
          <span v-if="product.original_price" class="detail-original-price">
            原价 {{ formatPrice(product.original_price) }}
          </span>
        </div>

        <div class="detail-seller" @click="router.push(`/profile/${product.seller?.id}`)">
          <el-avatar :size="40" :src="product.seller?.avatar">
            {{ product.seller?.nickname?.[0] || '?' }}
          </el-avatar>
          <div class="seller-info">
            <span class="seller-name">{{ product.seller?.nickname }}</span>
            <CreditBadge
              v-if="product.seller?.credit_level"
              :score="product.seller?.credit_score"
              :level="product.seller?.credit_level"
              size="small"
            />
          </div>
          <el-icon><component :is="'ArrowRight'" /></el-icon>
        </div>

        <div class="detail-meta">
          <span v-if="product.campus">📌 {{ product.campus }}</span>
          <span>👁 {{ product.view_count }} 次浏览</span>
          <span>🕒 {{ formatDateTime(product.created_at) }}</span>
          <span v-if="product.category">📂 {{ product.category.name }}</span>
        </div>

        <div class="detail-actions">
          <el-button
            v-if="!isSeller() && product.status === 'active'"
            type="warning"
            size="large"
            @click="handleBuy"
            round
          >
            立即购买
          </el-button>

          <el-button
            v-if="!isSeller()"
            type="success"
            size="large"
            @click="handleContact"
            round
          >
            <el-icon><component :is="'ChatDotRound'" /></el-icon>
            联系卖家
          </el-button>

          <el-tag v-if="product.status !== 'active'" type="info" size="large">
            该商品已{{ product.status === 'sold' ? '售出' : '下架' }}
          </el-tag>
        </div>

        <div class="detail-tags" v-if="product.tags?.length">
          <el-tag
            v-for="tag in product.tags"
            :key="tag.id"
            size="small"
            type="info"
            effect="plain"
          >
            {{ tag.name }}
          </el-tag>
        </div>
      </div>
    </div>

    <!-- Description -->
    <div v-if="product" class="detail-description">
      <h3>商品详情</h3>
      <div class="description-content">{{ product.description || '卖家没有提供详细描述' }}</div>
    </div>
  </div>
</template>

<style scoped>
.detail-layout {
  display: flex;
  gap: 32px;
  margin-bottom: 32px;
}

.detail-images {
  width: 480px;
  flex-shrink: 0;
}

.main-image {
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: #f5f5f5;
  aspect-ratio: 4/3;
  display: flex;
  align-items: center;
  justify-content: center;
}

.main-img {
  width: 100%;
  height: 100%;
}

.no-image {
  color: #ccc;
}

.thumb-list {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.thumb {
  width: 64px;
  height: 64px;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  border: 2px solid transparent;
  transition: border-color 0.2s;
}

.thumb.active {
  border-color: #43a047;
}

.detail-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.detail-title {
  font-size: 22px;
  font-weight: 700;
  line-height: 1.4;
}

.detail-price-row {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.detail-price {
  font-size: 28px;
  font-weight: 800;
  color: #e65100;
}

.detail-original-price {
  font-size: 14px;
  color: var(--text-secondary);
  text-decoration: line-through;
}

.detail-seller {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: var(--bg-page);
  border-radius: var(--radius-base);
  cursor: pointer;
  transition: background 0.2s;
}

.detail-seller:hover {
  background: #e8f5e9;
}

.seller-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.seller-name {
  font-weight: 600;
  font-size: 15px;
}

.detail-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 13px;
  color: var(--text-secondary);
}

.detail-actions {
  display: flex;
  gap: 12px;
  padding-top: 8px;
}

.detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.detail-description {
  background: var(--bg-card);
  padding: 28px 32px;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.detail-description h3 {
  font-size: 17px;
  font-weight: 600;
  margin-bottom: 16px;
}

.description-content {
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-regular);
  white-space: pre-wrap;
}

@media (max-width: 768px) {
  .detail-layout {
    flex-direction: column;
  }

  .detail-images {
    width: 100%;
  }
}
</style>
