<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getProduct, updateProduct, getCategories, getTags } from '@/api/products'
import { ElMessage } from 'element-plus'
import ImageUploader from '@/components/common/ImageUploader.vue'
import { productTitleRules, priceRules, conditionRules } from '@/utils/validators'
import { conditionLabels } from '@/utils/format'

const route = useRoute()
const router = useRouter()

const formRef = ref(null)
const loading = ref(false)
const fetching = ref(true)
const categories = ref([])
const tags = ref([])
const imageFiles = ref([])
const productId = route.params.id

const form = reactive({
  title: '',
  description: '',
  price: '',
  original_price: '',
  condition: 'used',
  campus: '',
  category_id: '',
  tag_ids: [],
})

onMounted(async () => {
  try {
    const [prodRes, catRes, tagRes] = await Promise.all([
      getProduct(productId),
      getCategories(),
      getTags(),
    ])
    const product = prodRes.data.data || prodRes.data
    form.title = product.title || ''
    form.description = product.description || ''
    form.price = String(product.price || '')
    form.original_price = product.original_price ? String(product.original_price) : ''
    form.condition = product.condition || 'used'
    form.campus = product.campus || ''
    form.category_id = product.category?.id || ''
    form.tag_ids = product.tags?.map(t => t.id) || []

    const catData = catRes.data.data || catRes.data
    categories.value = catData.results || catData
    const tagData = tagRes.data.data || tagRes.data
    tags.value = tagData.results || tagData
  } catch {
    ElMessage.error('商品不存在')
    router.push('/my-products')
  } finally {
    fetching.value = false
  }
})

async function handleSave() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const formData = new FormData()
    Object.entries(form).forEach(([key, val]) => {
      if (key === 'tag_ids' && val) {
        val.forEach(t => formData.append('tag_ids', t))
      } else if (val !== '' && val !== null && val !== undefined) {
        formData.append(key, val)
      }
    })
    imageFiles.value.forEach((f) => {
      formData.append('images', f)
    })

    await updateProduct(productId, formData)
    ElMessage.success('保存成功')
    router.push('/my-products')
  } catch {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page-container">
    <div class="publish-card">
      <h2 class="page-header-text">编辑商品</h2>

      <div v-if="fetching" class="loading-state" v-loading="true" style="min-height: 300px"></div>

      <el-form
        v-else
        ref="formRef"
        :model="form"
        :rules="{
          title: productTitleRules,
          price: priceRules,
          condition: conditionRules,
        }"
        label-position="top"
        size="large"
      >
        <el-form-item label="追加图片 (最多 9 张)">
          <ImageUploader v-model="imageFiles" :max="9" />
        </el-form-item>

        <el-form-item label="商品标题" prop="title">
          <el-input v-model="form.title" maxlength="200" show-word-limit />
        </el-form-item>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="售价" prop="price">
              <el-input v-model="form.price" placeholder="0.00">
                <template #prefix>￥</template>
              </el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="原价 (选填)">
              <el-input v-model="form.original_price" placeholder="0.00">
                <template #prefix>￥</template>
              </el-input>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="成色" prop="condition">
              <el-select v-model="form.condition" style="width: 100%">
                <el-option v-for="(label, key) in conditionLabels" :key="key" :label="label" :value="key" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="校区 (选填)">
              <el-select v-model="form.campus" style="width: 100%" clearable>
                <el-option label="校本部" value="校本部" />
                <el-option label="鹫峰校区" value="鹫峰校区" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="分类">
          <el-select v-model="form.category_id" placeholder="选择分类" clearable style="width: 100%">
            <el-option v-for="cat in categories" :key="cat.id" :label="cat.name" :value="cat.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="标签">
          <el-select v-model="form.tag_ids" multiple placeholder="选择标签" style="width: 100%">
            <el-option v-for="tag in tags" :key="tag.id" :label="tag.name" :value="tag.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="商品描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="6"
            maxlength="5000"
            show-word-limit
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="success"
            size="large"
            :loading="loading"
            @click="handleSave"
            round
            style="width: 200px"
          >
            保存修改
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.publish-card {
  max-width: 720px;
  margin: 0 auto;
  background: var(--bg-card);
  padding: 36px 40px;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.page-header-text {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 24px;
}
</style>
