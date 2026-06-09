<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getProducts, getCategories, getTags } from '@/api/products'
import ProductCard from '@/components/product/ProductCard.vue'
import { conditionLabels } from '@/utils/format'

const route = useRoute()
const router = useRouter()

const products = ref([])
const categories = ref([])
const tags = ref([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20

// Filters
const keyword = ref('')
const categoryId = ref('')
const condition = ref('')
const minPrice = ref('')
const maxPrice = ref('')
const tagId = ref('')
const sortBy = ref('newest')

// sortBy value mapping: frontend key → backend sort_by parameter
const sortMap = {
  'newest': 'newest',
  'price_asc': 'price_asc',
  'price_desc': 'price_desc',
  'popular': 'popular',
}

onMounted(async () => {
  keyword.value = route.query.q || ''
  categoryId.value = route.query.category || ''

  const [catRes, tagRes] = await Promise.all([
    getCategories(),
    getTags(),
  ])
  const catData = catRes.data.data || catRes.data
  categories.value = catData.results || catData
  const tagData = tagRes.data.data || tagRes.data
  tags.value = tagData.results || tagData

  await search()
})

async function search() {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize,
      status: 'active',
      sort_by: sortMap[sortBy.value],
    }
    if (keyword.value.trim()) params.search = keyword.value.trim()
    if (categoryId.value) params.category = categoryId.value
    if (condition.value) params.condition = condition.value
    if (tagId.value) params.tag = tagId.value
    if (minPrice.value) params.price_min = minPrice.value
    if (maxPrice.value) params.price_max = maxPrice.value

    const res = await getProducts(params)
    const data = res.data.data || res.data
    products.value = data.results || data
    total.value = res.data.pagination?.total || data.length || 0
  } catch {
    products.value = []
  } finally {
    loading.value = false
  }
}

function handleFilterChange() {
  currentPage.value = 1
  search()
}

function handlePageChange(page) {
  currentPage.value = page
  search()
}

function clearFilters() {
  keyword.value = ''
  categoryId.value = ''
  condition.value = ''
  tagId.value = ''
  minPrice.value = ''
  maxPrice.value = ''
  currentPage.value = 1
  search()
}
</script>

<template>
  <div class="page-container">
    <div class="search-layout">
      <!-- Filters sidebar -->
      <aside class="filter-sidebar">
        <el-card class="filter-card">
          <template #header>
            <div class="filter-header">
              <span>筛选</span>
              <el-button text size="small" type="info" @click="clearFilters">清空</el-button>
            </div>
          </template>

          <div class="filter-group">
            <label>分类</label>
            <el-select v-model="categoryId" placeholder="全部分类" clearable style="width: 100%" @change="handleFilterChange">
              <el-option
                v-for="cat in categories"
                :key="cat.id"
                :label="cat.name"
                :value="cat.id"
              />
            </el-select>
          </div>

          <div class="filter-group">
            <label>成色</label>
            <el-select v-model="condition" placeholder="全部成色" clearable style="width: 100%" @change="handleFilterChange">
              <el-option
                v-for="(label, key) in conditionLabels"
                :key="key"
                :label="label"
                :value="key"
              />
            </el-select>
          </div>

          <div class="filter-group">
            <label>标签</label>
            <el-select v-model="tagId" placeholder="全部标签" clearable style="width: 100%" @change="handleFilterChange">
              <el-option
                v-for="tag in tags"
                :key="tag.id"
                :label="tag.name"
                :value="tag.id"
              />
            </el-select>
          </div>

          <div class="filter-group">
            <label>价格范围</label>
            <el-row :gutter="8">
              <el-col :span="12">
                <el-input v-model="minPrice" placeholder="最低价" @change="handleFilterChange" />
              </el-col>
              <el-col :span="12">
                <el-input v-model="maxPrice" placeholder="最高价" @change="handleFilterChange" />
              </el-col>
            </el-row>
          </div>

          <div class="filter-group">
            <label>排序</label>
            <el-select v-model="sortBy" style="width: 100%" @change="handleFilterChange">
              <el-option label="最新发布" value="newest" />
              <el-option label="价格低→高" value="price_asc" />
              <el-option label="价格高→低" value="price_desc" />
              <el-option label="最多浏览" value="popular" />
            </el-select>
          </div>
        </el-card>
      </aside>

      <!-- Results -->
      <main class="search-results">
        <div v-if="keyword" class="search-keyword">
          搜索 "{{ keyword }}" 的结果 ({{ total }} 件)
        </div>

        <div v-if="loading" class="loading-state">
          <el-skeleton :rows="4" animated v-for="i in 3" :key="i" style="margin-bottom: 20px" />
        </div>

        <div v-else-if="products.length > 0">
          <div class="card-grid">
            <ProductCard
              v-for="product in products"
              :key="product.id"
              :product="product"
            />
          </div>

          <div class="pagination-wrap" v-if="total > pageSize">
            <el-pagination
              v-model:current-page="currentPage"
              :page-size="pageSize"
              :total="total"
              layout="prev, pager, next"
              background
              @current-change="handlePageChange"
            />
          </div>
        </div>

        <div v-else class="empty-state">
          <el-icon :size="56"><component :is="'Search'" /></el-icon>
          <p>没有找到匹配的商品</p>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.search-layout {
  display: flex;
  gap: 24px;
}

.filter-sidebar {
  width: 240px;
  flex-shrink: 0;
}

.filter-card {
  border-radius: var(--radius-lg);
  position: sticky;
  top: 80px;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-group {
  margin-bottom: 16px;
}

.filter-group label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-regular);
  margin-bottom: 6px;
}

.search-results {
  flex: 1;
  min-width: 0;
}

.search-keyword {
  font-size: 16px;
  color: var(--text-primary);
  margin-bottom: 20px;
  padding: 12px 16px;
  background: var(--bg-card);
  border-radius: var(--radius-base);
}

.search-keyword strong {
  color: #43a047;
}

.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 32px;
}

@media (max-width: 768px) {
  .search-layout {
    flex-direction: column;
  }

  .filter-sidebar {
    width: 100%;
  }
}
</style>
