import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getProducts, getCategories } from '@/api/products'

export const useProductsStore = defineStore('products', () => {
  const products = ref([])
  const categories = ref([])
  const loading = ref(false)
  const total = ref(0)

  async function fetchProducts(params = {}) {
    loading.value = true
    try {
      const res = await getProducts(params)
      const data = res.data.data || res.data
      products.value = data.results || data
      total.value = data.pagination?.total || data.count || 0
    } catch {
      products.value = []
    } finally {
      loading.value = false
    }
  }

  async function fetchCategories() {
    try {
      const res = await getCategories()
      const data = res.data.data || res.data
      categories.value = data.results || data
    } catch {
      categories.value = []
    }
  }

  return {
    products,
    categories,
    loading,
    total,
    fetchProducts,
    fetchCategories,
  }
})
