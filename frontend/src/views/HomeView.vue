<script setup>
import { ref, onMounted } from 'vue'
import { useProductsStore } from '@/stores/products'
import ProductCard from '@/components/product/ProductCard.vue'
import { TrendCharts, Goods, School } from '@element-plus/icons-vue'

const productsStore = useProductsStore()
const currentPage = ref(1)
const pageSize = 20

async function loadProducts() {
  await productsStore.fetchProducts({
    page: currentPage.value,
    page_size: pageSize,
    status: 'active',
  })
}

function handlePageChange(page) {
  currentPage.value = page
  loadProducts()
}

onMounted(async () => {
  await Promise.all([
    loadProducts(),
    productsStore.fetchCategories(),
  ])
})
</script>

<template>
  <div class="page-container">
    <!-- Hero Banner -->
    <div class="hero-banner">
      <div class="hero-content">
        <h1 class="hero-title">
          <span class="hero-icon">&#127795;</span>
          让闲置流转，让信任传递
        </h1>
        <p class="hero-subtitle">
          北京林业大学 · 安全便捷的校园 C2C 二手交易平台
        </p>
        <div class="hero-stats">
          <div class="hero-stat">
            <span class="stat-number">{{ productsStore.total }}</span>
            <span class="stat-label">在售商品</span>
          </div>
          <div class="hero-stat">
            <span class="stat-number">100%</span>
            <span class="stat-label">实名认证</span>
          </div>
          <div class="hero-stat">
            <span class="stat-number">面交</span>
            <span class="stat-label">安全担保</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Categories -->
    <div v-if="productsStore.categories.length > 0" class="category-section">
      <h3 class="section-title">浏览分类</h3>
      <div class="category-list">
        <div
          v-for="cat in productsStore.categories"
          :key="cat.id"
          class="category-item"
          @click="$router.push({ path: '/search', query: { category: cat.id } })"
        >
          <span class="cat-icon">{{ cat.icon || '📦' }}</span>
          <span class="cat-name">{{ cat.name }}</span>
        </div>
      </div>
    </div>

    <!-- Product List -->
    <div class="products-section">
      <div class="section-header">
        <h3 class="section-title">最新发布</h3>
      </div>

      <div v-if="productsStore.loading" class="loading-state">
        <el-skeleton :rows="3" animated />
        <el-skeleton :rows="3" animated style="margin-top: 20px" />
      </div>

      <div v-else-if="productsStore.products.length > 0">
        <div class="card-grid">
          <ProductCard
            v-for="product in productsStore.products"
            :key="product.id"
            :product="product"
          />
        </div>

        <div class="pagination-wrap" v-if="productsStore.total > pageSize">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="pageSize"
            :total="productsStore.total"
            layout="prev, pager, next"
            background
            @current-change="handlePageChange"
          />
        </div>
      </div>

      <div v-else class="empty-state">
        <el-icon :size="56"><component :is="'Box'" /></el-icon>
        <p>暂无在售商品，去发布第一个吧</p>
        <el-button type="success" round @click="$router.push('/publish')">
          发布商品
        </el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.hero-banner {
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 30%, #f1f8e9 70%, #e8f5e9 100%);
  border-radius: var(--radius-lg);
  padding: 56px 40px;
  margin-bottom: 36px;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.hero-banner::after {
  content: '';
  position: absolute;
  top: -50%;
  right: -10%;
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(67, 160, 71, 0.15) 0%, transparent 70%);
  border-radius: 50%;
}

.hero-content {
  position: relative;
  z-index: 1;
}

.hero-title {
  font-size: 32px;
  font-weight: 800;
  color: #2e7d32;
  margin-bottom: 12px;
}

.hero-icon {
  font-size: 36px;
}

.hero-subtitle {
  font-size: 16px;
  color: #558b2f;
  margin-bottom: 32px;
}

.hero-stats {
  display: flex;
  justify-content: center;
  gap: 48px;
}

.hero-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-number {
  font-size: 28px;
  font-weight: 700;
  color: #1b5e20;
}

.stat-label {
  font-size: 13px;
  color: #689f38;
  margin-top: 4px;
}

.category-section {
  margin-bottom: 36px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--text-primary);
}

.category-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.category-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: var(--bg-card);
  border-radius: 24px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid var(--border-color);
  font-size: 14px;
}

.category-item:hover {
  border-color: #43a047;
  color: #43a047;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(67, 160, 71, 0.1);
}

.cat-icon {
  font-size: 18px;
}

.products-section {
  margin-bottom: 40px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 32px;
}

.loading-state {
  padding: 20px 0;
}

@media (max-width: 640px) {
  .hero-banner {
    padding: 36px 20px;
  }

  .hero-title {
    font-size: 24px;
  }

  .hero-stats {
    gap: 24px;
  }
}
</style>
