<script setup>
import { ref, onMounted } from 'vue'
import { getMyProducts, updateProduct } from '@/api/products'
import { ElMessage, ElMessageBox } from 'element-plus'
import ProductCard from '@/components/product/ProductCard.vue'
import { formatPrice, statusLabels } from '@/utils/format'

const products = ref([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const res = await getMyProducts()
    const data = res.data.data || res.data
    products.value = data.results || data
  } catch {
    products.value = []
  } finally {
    loading.value = false
  }
})

async function handleHide(product) {
  try {
    await ElMessageBox.confirm('确定要下架该商品吗？', '确认下架', {
      confirmButtonText: '下架',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await updateProduct(product.id, { status: 'hidden' })
    ElMessage.success('已下架')
    products.value = products.value.filter(p => p.id !== product.id)
  } catch {
    // cancel or error
  }
}
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>我的商品 ({{ products.length }})</h2>
      <el-button type="success" round @click="$router.push('/publish')">
        <el-icon><component :is="'Plus'" /></el-icon>
        发布商品
      </el-button>
    </div>

    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="5" animated />
    </div>

    <div v-else-if="products.length > 0">
      <el-card
        v-for="product in products"
        :key="product.id"
        class="product-item"
        shadow="hover"
      >
        <div class="product-row">
          <el-image
            v-if="product.cover_image"
            :src="product.cover_image"
            fit="cover"
            class="item-image"
          />
          <div class="item-info">
            <h4>{{ product.title }}</h4>
            <div class="item-meta">
              <span class="item-price">{{ formatPrice(product.price) }}</span>
              <el-tag size="small" :type="product.status === 'active' ? 'success' : 'info'">
                {{ statusLabels[product.status] || product.status }}
              </el-tag>
              <span>{{ product.view_count }} 次浏览</span>
            </div>
          </div>
          <div class="item-actions">
            <el-button
              size="small"
              @click="$router.push(`/product/${product.id}`)"
            >
              查看
            </el-button>
            <el-button
              v-if="product.status === 'active'"
              size="small"
              type="danger"
              plain
              @click="handleHide(product)"
            >
              下架
            </el-button>
          </div>
        </div>
      </el-card>
    </div>

    <div v-else class="empty-state">
      <el-icon :size="56"><component :is="'Box'" /></el-icon>
      <p>还没有发布过商品</p>
      <el-button type="success" round @click="$router.push('/publish')">
        发布第一个商品
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.product-item {
  margin-bottom: 12px;
  border-radius: var(--radius-base);
}

.product-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.item-image {
  width: 80px;
  height: 80px;
  border-radius: 8px;
  flex-shrink: 0;
}

.item-info {
  flex: 1;
}

.item-info h4 {
  font-size: 15px;
  margin-bottom: 8px;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  color: var(--text-secondary);
}

.item-price {
  font-weight: 700;
  font-size: 16px;
  color: #e65100;
}

.item-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}
</style>
