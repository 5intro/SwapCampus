<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useProductsStore } from '@/stores/products'
import ProductCard from '@/components/product/ProductCard.vue'

const auth = useAuthStore()
const productsStore = useProductsStore()
const currentPage = ref(1)
const pageSize = 20
const productsRef = ref(null)

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

function scrollToProducts() {
  productsRef.value?.scrollIntoView({ behavior: 'smooth' })
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
    <!-- Hero -->
    <section class="hero">
      <div class="hero-text">
        <h1 class="hero-headline">校园闲置，安心流转</h1>
        <p class="hero-desc">
          北京林业大学师生专属的 C2C 二手交易平台。实名认证与面交担保，让每一笔交易都放心。
        </p>
        <div class="hero-actions">
          <template v-if="auth.isLoggedIn">
            <el-button type="success" size="large" round @click="$router.push('/publish')">
              发布商品
            </el-button>
            <el-button size="large" round class="btn-outline" @click="scrollToProducts">
              浏览商品
            </el-button>
          </template>
          <template v-else>
            <el-button type="success" size="large" round @click="$router.push('/register')">
              注册账号
            </el-button>
            <el-button size="large" round class="btn-outline" @click="scrollToProducts">
              浏览商品
            </el-button>
          </template>
        </div>
        <div class="hero-stats">
          <div class="hero-stat">
            <span class="stat-number">{{ productsStore.total || 0 }}</span>
            <span class="stat-label">在售好物</span>
          </div>
          <div class="hero-stat">
            <span class="stat-number">实名</span>
            <span class="stat-label">身份认证</span>
          </div>
          <div class="hero-stat">
            <span class="stat-number">面交</span>
            <span class="stat-label">安全担保</span>
          </div>
        </div>
      </div>
      <div class="hero-visual">
        <img
          src="/hero-campus.webp"
          alt="北京林业大学校园"
          class="hero-image"
        />
        <div class="hero-visual-glow"></div>
      </div>
    </section>

    <!-- Categories -->
    <section v-if="productsStore.categories.length > 0" class="category-section">
      <h2 class="section-title">浏览分类</h2>
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
    </section>

    <!-- Product List -->
    <section ref="productsRef" class="products-section">
      <div class="section-header">
        <h2 class="section-title">最新发布</h2>
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
    </section>
  </div>
</template>

<style scoped>
/* Hero */
.hero {
  display: flex;
  align-items: center;
  gap: 48px;
  padding: 48px 0 32px;
  margin-bottom: 24px;
  min-height: 360px;
}

.hero-text {
  flex: 1;
  max-width: 540px;
}

.hero-headline {
  font-size: 40px;
  font-weight: 800;
  color: var(--color-brand-dark);
  line-height: 1.25;
  margin-bottom: 16px;
  letter-spacing: -0.5px;
}

.hero-desc {
  font-size: 16px;
  color: var(--text-regular);
  line-height: 1.7;
  margin-bottom: 28px;
  max-width: 440px;
}

.hero-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 32px;
}

.btn-outline {
  color: var(--color-brand-dark);
  border-color: var(--color-brand);
  font-weight: 500;
}

.btn-outline:hover {
  color: #fff;
  background: var(--color-brand);
  border-color: var(--color-brand);
}

.hero-stats {
  display: flex;
  gap: 40px;
  padding-top: 8px;
}

.hero-stat {
  display: flex;
  flex-direction: column;
}

.stat-number {
  font-size: 26px;
  font-weight: 700;
  color: var(--color-brand-dark);
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 2px;
}

/* Hero visual */
.hero-visual {
  flex: 1;
  max-width: 520px;
  position: relative;
  display: none;
}

.hero-image {
  width: 100%;
  border-radius: var(--radius-xl);
  object-fit: cover;
  aspect-ratio: 3/2;
  box-shadow: var(--shadow-green);
}

.hero-visual-glow {
  position: absolute;
  top: -20px;
  right: -20px;
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, rgba(67, 160, 71, 0.12) 0%, transparent 70%);
  border-radius: 50%;
  z-index: -1;
  pointer-events: none;
}

/* Categories */
.category-section {
  margin-bottom: 32px;
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 14px;
  color: var(--text-primary);
}

.category-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.category-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 9px 18px;
  background: var(--bg-card);
  border-radius: 24px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  border: 1px solid var(--border-color);
  font-size: 14px;
  color: var(--text-regular);
}

.category-item:hover {
  border-color: var(--color-brand);
  color: var(--color-brand);
  transform: translateY(-2px);
  box-shadow: var(--shadow-green);
}

.cat-icon {
  font-size: 16px;
}

/* Products */
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

@media (min-width: 768px) {
  .hero-visual {
    display: block;
  }
}

@media (max-width: 767px) {
  .hero {
    flex-direction: column;
    padding: 32px 0 20px;
    text-align: center;
    min-height: auto;
  }

  .hero-headline {
    font-size: 28px;
  }

  .hero-desc {
    max-width: 100%;
    font-size: 15px;
  }

  .hero-actions {
    justify-content: center;
  }

  .hero-stats {
    justify-content: center;
    gap: 28px;
  }
}
</style>
