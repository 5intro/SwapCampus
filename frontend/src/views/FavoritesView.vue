<script setup>
import { ref, onMounted } from 'vue'
import { getFavorites, removeFavorite } from '@/api/favorites'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import ProductCard from '@/components/product/ProductCard.vue'

const router = useRouter()
const favorites = ref([])
const loading = ref(false)

onMounted(() => { loadFavorites() })

async function loadFavorites() {
  loading.value = true
  try {
    const res = await getFavorites({ page_size: 50 })
    const data = res.data.data || res.data
    favorites.value = data.results || data
  } catch {
    favorites.value = []
  } finally {
    loading.value = false
  }
}

async function handleRemove(fav) {
  try {
    await ElMessageBox.confirm('确定取消收藏吗？', '提示', { type: 'warning' })
    await removeFavorite(fav.id)
    ElMessage.success('已取消收藏')
    loadFavorites()
  } catch {}
}
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>我的收藏</h2>
    </div>

    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="4" animated v-for="i in 3" :key="i" style="margin-bottom: 20px" />
    </div>

    <div v-else-if="favorites.length > 0" class="card-grid">
      <div v-for="fav in favorites" :key="fav.id" class="fav-item">
        <ProductCard :product="fav.product" />
        <el-button
          size="small"
          type="danger"
          plain
          class="remove-btn"
          @click="handleRemove(fav)"
        >
          取消收藏
        </el-button>
      </div>
    </div>

    <div v-else class="empty-state">
      <el-icon :size="56"><component :is="'StarFilled'" /></el-icon>
      <p>还没有收藏任何商品</p>
      <el-button type="success" round @click="router.push('/')">去逛逛</el-button>
    </div>
  </div>
</template>

<style scoped>
.fav-item {
  position: relative;
}
.remove-btn {
  margin-top: 8px;
  width: 100%;
}
</style>
