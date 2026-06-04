<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { createProduct, getCategories, getTags } from '@/api/products'
import { ElMessage } from 'element-plus'
import ImageUploader from '@/components/common/ImageUploader.vue'
import { productTitleRules, priceRules, conditionRules } from '@/utils/validators'
import { conditionLabels } from '@/utils/format'

const router = useRouter()

const formRef = ref(null)
const loading = ref(false)
const categories = ref([])
const tags = ref([])
const imageFiles = ref([])

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
  const [catRes, tagRes] = await Promise.all([
    getCategories(),
    getTags(),
  ])
  const catData = catRes.data.data || catRes.data
  categories.value = catData.results || catData
  const tagData = tagRes.data.data || tagRes.data
  tags.value = tagData.results || tagData
})

async function handlePublish() {
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

    await createProduct(formData)
    ElMessage.success('发布成功')
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
      <h2 class="page-header-text">发布商品</h2>
      <p class="page-subtitle">认真描述商品信息，更快卖出~</p>

      <el-form
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
        <el-form-item label="商品图片 (最多 9 张)" prop="images">
          <ImageUploader v-model="imageFiles" :max="9" />
        </el-form-item>

        <el-form-item label="商品标题" prop="title">
          <el-input
            v-model="form.title"
            placeholder="例如：九成新 MacBook Pro 14寸"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="售价" prop="price">
              <el-input
                v-model="form.price"
                placeholder="0.00"
              >
                <template #prefix>￥</template>
              </el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="原价 (选填)">
              <el-input
                v-model="form.original_price"
                placeholder="0.00"
              >
                <template #prefix>￥</template>
              </el-input>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="成色" prop="condition">
              <el-select v-model="form.condition" style="width: 100%">
                <el-option
                  v-for="(label, key) in conditionLabels"
                  :key="key"
                  :label="label"
                  :value="key"
                />
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
            <el-option
              v-for="cat in categories"
              :key="cat.id"
              :label="cat.name"
              :value="cat.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="标签">
          <el-select
            v-model="form.tag_ids"
            multiple
            placeholder="选择标签"
            style="width: 100%"
          >
            <el-option
              v-for="tag in tags"
              :key="tag.id"
              :label="tag.name"
              :value="tag.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="商品描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="6"
            placeholder="详细描述商品的状态、使用情况、购买渠道等..."
            maxlength="5000"
            show-word-limit
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="success"
            size="large"
            :loading="loading"
            @click="handlePublish"
            round
            style="width: 200px"
          >
            发布商品
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
  margin-bottom: 4px;
}

.page-subtitle {
  color: var(--text-secondary);
  font-size: 14px;
  margin-bottom: 32px;
}
</style>
