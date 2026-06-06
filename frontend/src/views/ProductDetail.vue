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
    const { value: meetLocation } = await ElMessageBox.prompt(
      '请输入面交地点（可选）',
      '确认下单',
      {
        inputPlaceholder: '如：图书馆门口',
        confirmButtonText: '确认下单',
        cancelButtonText: '取消',
      },
    )

    await createOrder({
      product_id: product.value.id,
      meet_location: meetLocation || undefined,
    })
    ElMessage.success('下单成功，等待卖家确认')
    router.push('/my-orders')
  } catch {
    // cancel or error
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
    <template v-if="product">
      <!-- Breadcrumb -->
      <div class="breadcrumb">
        <el-button text size="small" @click="router.push('/')">
          <el-icon><component :is="'ArrowLeft'" /></el-icon>
          返回首页
        </el-button>
        <span class="breadcrumb-sep">/</span>
        <span v-if="product.category" class="breadcrumb-cat">
          {{ product.category.name }}
        </span>
        <span class="breadcrumb-sep" v-if="product.category">/</span>
        <span class="breadcrumb-current">{{ product.title }}</span>
      </div>

      <!-- Main Layout -->
      <div class="detail-layout">
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
              <el-icon :size="72"><component :is="'Picture'" /></el-icon>
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
          <div class="info-top">
            <div class="info-badges">
              <el-tag
                v-if="product.condition"
                :type="conditionColors[product.condition] || 'info'"
                size="small"
                effect="plain"
              >
                {{ conditionLabels[product.condition] || product.condition_display }}
              </el-tag>
              <el-tag
                v-if="product.status !== 'active'"
                type="info"
                size="small"
              >
                已{{ product.status === 'sold' ? '售出' : '下架' }}
              </el-tag>
            </div>

            <h1 class="detail-title">{{ product.title }}</h1>

            <div class="detail-price-row">
              <span class="detail-price">{{ formatPrice(product.price) }}</span>
              <span v-if="product.original_price" class="detail-original-price">
                原价 {{ formatPrice(product.original_price) }}
              </span>
            </div>

            <div class="detail-meta">
              <span class="meta-item">
                <el-icon :size="15"><component :is="'Location'" /></el-icon>
                {{ product.campus || '未设置' }}
              </span>
              <span class="meta-item">
                <el-icon :size="15"><component :is="'View'" /></el-icon>
                {{ product.view_count }} 次浏览
              </span>
              <span class="meta-item">
                <el-icon :size="15"><component :is="'Clock'" /></el-icon>
                {{ formatTime(product.created_at) }}
              </span>
              <span v-if="product.category" class="meta-item">
                <el-icon :size="15"><component :is="'Folder'" /></el-icon>
                {{ product.category.name }}
              </span>
            </div>
          </div>

          <!-- Seller Card -->
          <div
            class="seller-card"
            @click="router.push(`/profile/${product.seller?.id}`)"
          >
            <el-avatar :size="44" :src="product.seller?.avatar">
              {{ product.seller?.nickname?.[0] || '?' }}
            </el-avatar>
            <div class="seller-detail">
              <span class="seller-name">{{ product.seller?.nickname }}</span>
              <CreditBadge
                v-if="product.seller?.credit_level"
                :score="product.seller?.credit_score"
                :level="product.seller?.credit_level"
                size="small"
              />
            </div>
            <el-icon class="seller-arrow"><component :is="'ArrowRight'" /></el-icon>
          </div>

          <!-- Actions -->
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
          </div>

          <!-- Tags -->
          <div class="detail-tags" v-if="product.tags?.length">
            <el-tag
              v-for="tag in product.tags"
              :key="tag.id"
              size="small"
              effect="plain"
            >
              #{{ tag.name }}
            </el-tag>
          </div>
        </div>
      </div>

      <!-- Description -->
      <section class="detail-description">
        <h3>商品详情</h3>
        <div class="description-content">
          {{ product.description || '卖家没有提供详细描述' }}
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
/* Breadcrumb */
.breadcrumb {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 20px;
  font-size: 13px;
  color: var(--text-secondary);
}

.breadcrumb-sep {
  color: var(--border-color);
}

.breadcrumb-current {
  color: var(--text-primary);
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Main Layout */
.detail-layout {
  display: flex;
  gap: 36px;
  margin-bottom: 32px;
}

/* Images */
.detail-images {
  width: 480px;
  flex-shrink: 0;
}

.main-image {
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--bg-card);
  aspect-ratio: 4/3;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border-color);
}

.main-img {
  width: 100%;
  height: 100%;
}

.no-image {
  color: var(--border-color);
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
  transition: border-color 0.25s ease;
}

.thumb:hover {
  border-color: var(--color-brand);
}

.thumb.active {
  border-color: var(--color-brand);
}

/* Info */
.detail-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.info-top {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-badges {
  display: flex;
  gap: 6px;
}

.detail-title {
  font-size: 24px;
  font-weight: 700;
  line-height: 1.35;
  color: var(--text-primary);
}

.detail-price-row {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.detail-price {
  font-size: 30px;
  font-weight: 800;
  color: var(--color-price);
}

.detail-original-price {
  font-size: 14px;
  color: var(--text-secondary);
  text-decoration: line-through;
}

.detail-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--text-secondary);
}

/* Seller Card */
.seller-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: var(--bg-page);
  border-radius: var(--radius-base);
  cursor: pointer;
  transition: background 0.2s, transform 0.2s;
}

.seller-card:hover {
  background: var(--color-brand-light);
  transform: translateY(-1px);
}

.seller-detail {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.seller-name {
  font-weight: 600;
  font-size: 15px;
}

.seller-arrow {
  color: var(--text-secondary);
}

/* Actions */
.detail-actions {
  display: flex;
  gap: 12px;
  padding-top: 4px;
}

.detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

/* Description */
.detail-description {
  background: var(--bg-card);
  padding: 28px 32px;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.detail-description h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--text-primary);
}

.description-content {
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-regular);
  white-space: pre-wrap;
  max-width: 720px;
}

@media (max-width: 768px) {
  .detail-layout {
    flex-direction: column;
    gap: 20px;
  }

  .detail-images {
    width: 100%;
  }

  .detail-title {
    font-size: 20px;
  }

  .detail-price {
    font-size: 24px;
  }
}
</style>
