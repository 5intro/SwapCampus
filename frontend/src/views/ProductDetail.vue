<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getProduct, getRelatedProducts } from '@/api/products'
import { addFavorite, getFavorites, removeFavorite } from '@/api/favorites'
import { createReport } from '@/api/reports'
import { createOrder } from '@/api/transactions'
import { createConversation } from '@/api/chat'
import { ElMessage, ElMessageBox } from 'element-plus'
import CreditBadge from '@/components/user/CreditBadge.vue'
import ProductCard from '@/components/product/ProductCard.vue'
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
const relatedProducts = ref([])
const isFavorited = ref(false)
const favoriteId = ref(null)
const reportDialog = ref(false)
const reportReason = ref('')
const reportDesc = ref('')

const reportReasons = [
  { value: 'inappropriate', label: '内容不当' },
  { value: 'counterfeit', label: '假冒伪劣' },
  { value: 'fraud', label: '虚假交易' },
  { value: 'prohibited', label: '违禁物品' },
  { value: 'other', label: '其他' },
]

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
  fetchRelated()
  checkFav()
})

async function fetchRelated() {
  try {
    const res = await getRelatedProducts(route.params.id)
    relatedProducts.value = (res.data.data || res.data)?.results || res.data.data || []
  } catch {}
}

async function checkFav() {
  if (!auth.isLoggedIn) return
  try {
    const res = await getFavorites({ page_size: 50 })
    const data = res.data.data || res.data
    const favs = data.results || data
    const fav = favs.find(f => f.product.id === product.value?.id)
    if (fav) {
      isFavorited.value = true
      favoriteId.value = fav.id
    }
  } catch {}
}

async function toggleFavorite() {
  if (!auth.isLoggedIn) {
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  try {
    if (isFavorited.value) {
      await removeFavorite(favoriteId.value)
      isFavorited.value = false
      ElMessage.success('已取消收藏')
    } else {
      const res = await addFavorite(route.params.id)
      isFavorited.value = true
      favoriteId.value = res.data.data.id
      ElMessage.success('已加入收藏')
    }
  } catch {
    // handled by interceptor
  }
}

function handleEdit() {
  router.push(`/product/${route.params.id}/edit`)
}

async function handleDelete() {
  try {
    await ElMessageBox.confirm('确定要删除该商品吗？此操作不可撤销。', '确认删除', {
      type: 'error',
      confirmButtonText: '删除',
    })
    await import('@/api/products').then(m => m.deleteProduct(route.params.id))
    ElMessage.success('已删除')
    router.push('/my-products')
  } catch {}
}

function handleReport() {
  if (!auth.isLoggedIn) {
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  reportReason.value = ''
  reportDesc.value = ''
  reportDialog.value = true
}

async function submitReport() {
  if (!reportReason.value) {
    ElMessage.warning('请选择举报原因')
    return
  }
  try {
    await createReport({
      product_id: route.params.id,
      reason: reportReason.value,
      description: reportDesc.value,
    })
    ElMessage.success('举报已提交，我们会尽快处理')
    reportDialog.value = false
  } catch {}
}

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
            <el-button
              :type="isFavorited ? 'warning' : 'default'"
              size="large"
              @click="toggleFavorite"
              round
              :icon="isFavorited ? 'StarFilled' : 'Star'"
            >
              {{ isFavorited ? '已收藏' : '收藏' }}
            </el-button>
            <template v-if="isSeller()">
              <el-button size="default" type="primary" plain round @click="handleEdit">
                编辑
              </el-button>
              <el-button size="default" type="danger" plain round @click="handleDelete">
                删除
              </el-button>
            </template>
            <el-button
              v-if="!isSeller()"
              size="default"
              type="danger"
              plain
              round
              @click="handleReport"
            >
              举报
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

      <!-- Related Products -->
      <section v-if="relatedProducts.length" class="related-section">
        <h3>相关推荐</h3>
        <div class="card-grid">
          <ProductCard
            v-for="rp in relatedProducts"
            :key="rp.id"
            :product="rp"
          />
        </div>
      </section>

      <!-- Report Dialog -->
      <el-dialog v-model="reportDialog" title="举报商品" width="420px">
        <el-form label-position="top">
          <el-form-item label="举报原因" required>
            <el-select v-model="reportReason" placeholder="请选择举报原因" style="width: 100%">
              <el-option
                v-for="r in reportReasons"
                :key="r.value"
                :label="r.label"
                :value="r.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="详细说明（选填）">
            <el-input
              v-model="reportDesc"
              type="textarea"
              :rows="3"
              maxlength="500"
              show-word-limit
            />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="reportDialog = false">取消</el-button>
          <el-button type="danger" @click="submitReport">提交举报</el-button>
        </template>
      </el-dialog>
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

.related-section {
  margin-top: 40px;
}

.related-section h3 {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 20px;
}
</style>
