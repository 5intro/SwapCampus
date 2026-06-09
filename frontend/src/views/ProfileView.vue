<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getUser, getUserProfile, updateUserProfile, getCreditRecords } from '@/api/users'
import { getOrders } from '@/api/transactions'
import { getMyProducts, getUserProducts } from '@/api/products'
import CreditBadge from '@/components/user/CreditBadge.vue'
import ProductCard from '@/components/product/ProductCard.vue'
import { ElMessage } from 'element-plus'
import {
  formatPrice, formatDateTime, formatTime,
  creditLevelLabels, orderStatusLabels, orderStatusColors,
} from '@/utils/format'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const isOwn = ref(false)
const profileUser = ref(null)
const creditRecords = ref([])
const myProductsList = ref([])
const myOrdersList = ref([])
const activeTab = ref('products')

const editing = ref(false)
const editForm = ref({
  nickname: '',
  bio: '',
  campus: '',
})

onMounted(async () => {
  const userId = route.params.id

  if (!userId) {
    if (!auth.isLoggedIn) {
      router.push('/login')
      return
    }
    isOwn.value = true
    profileUser.value = auth.user
  } else if (auth.user && auth.user.id === userId) {
    isOwn.value = true
    profileUser.value = auth.user
  } else {
    try {
      const res = await getUser(userId)
      profileUser.value = res.data.data || res.data
    } catch {
      ElMessage.error('用户不存在')
      router.push('/')
      return
    }
  }

  if (isOwn.value) {
    loadMyData()
  } else {
    loadPublicProducts(profileUser.value.id)
  }
})

async function loadPublicProducts(userId) {
  try {
    const res = await getUserProducts(userId)
    myProductsList.value = (res.data.data?.results || res.data.data || [])
  } catch {
    myProductsList.value = []
  }
}

async function loadMyData() {
  try {
    const [creditRes, productsRes, ordersRes] = await Promise.all([
      getCreditRecords(auth.user.id),
      getMyProducts(),
      getOrders({ role: 'all' }),
    ])
    creditRecords.value = (creditRes.data.data?.results || creditRes.data.data || [])?.slice(0, 10)
    myProductsList.value = (productsRes.data.data?.results || productsRes.data.data || [])
    myOrdersList.value = (ordersRes.data.data?.results || ordersRes.data.data || [])
  } catch {
    // silently fail
  }
}

function startEdit() {
  editForm.value = {
    nickname: profileUser.value?.nickname || '',
    bio: profileUser.value?.bio || '',
    campus: profileUser.value?.campus || '',
  }
  editing.value = true
}

async function saveProfile() {
  try {
    const res = await updateUserProfile(editForm.value)
    auth.user = { ...auth.user, ...(res.data.data || res.data) }
    profileUser.value = auth.user
    ElMessage.success('保存成功')
    editing.value = false
  } catch {
    // handled by interceptor
  }
}

function cancelEdit() {
  editing.value = false
}
</script>

<template>
  <div class="page-container" v-if="profileUser">
    <!-- Profile Header -->
    <section class="profile-header">
      <div class="profile-cover"></div>
      <div class="profile-body">
        <el-avatar :size="88" :src="profileUser.avatar" class="profile-avatar">
          {{ profileUser.nickname?.[0] || profileUser.username?.[0] || '?' }}
        </el-avatar>
        <div class="profile-main">
          <div class="profile-name-row">
            <h2>{{ profileUser.nickname || profileUser.username }}</h2>
            <CreditBadge
              v-if="profileUser.credit_score != null"
              :score="profileUser.credit_score"
              :level="profileUser.credit_level"
            />
            <el-tag
              v-if="profileUser.verification_status === 'approved'"
              type="success"
              size="small"
              effect="plain"
            >已认证</el-tag>
            <el-tag
              v-else-if="profileUser.verification_status === 'pending'"
              type="warning"
              size="small"
              effect="plain"
            >认证审核中</el-tag>
            <el-tag
              v-else-if="profileUser.verification_status === 'rejected'"
              type="danger"
              size="small"
              effect="plain"
            >认证未通过</el-tag>
            <el-tag
              v-else-if="isOwn"
              type="info"
              size="small"
              effect="plain"
            >未认证</el-tag>
          </div>
          <p class="profile-meta">
            用户名 {{ profileUser.username }}
            <span v-if="profileUser.campus"> - {{ profileUser.campus }}</span>
            <span> - 加入于 {{ formatDateTime(profileUser.date_joined) }}</span>
          </p>
          <p v-if="profileUser.bio" class="profile-bio">{{ profileUser.bio }}</p>
        </div>
        <el-button
          v-if="isOwn && !editing"
          @click="startEdit"
          round
          class="edit-btn"
        >
          <el-icon><component :is="'Edit'" /></el-icon>
          编辑资料
        </el-button>
      </div>
    </section>

    <!-- Edit Form -->
    <section v-if="editing" class="edit-section">
      <el-form :model="editForm" label-position="top">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="昵称">
              <el-input v-model="editForm.nickname" maxlength="50" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="校区">
              <el-select v-model="editForm.campus" style="width: 100%">
                <el-option label="校本部" value="校本部" />
                <el-option label="鹫峰校区" value="鹫峰校区" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="个人简介">
          <el-input
            v-model="editForm.bio"
            type="textarea"
            :rows="3"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <div class="edit-actions">
          <el-button type="success" @click="saveProfile">保存</el-button>
          <el-button @click="cancelEdit">取消</el-button>
        </div>
      </el-form>
    </section>

    <!-- Tabs (own profile) -->
    <section v-if="isOwn" class="profile-tabs">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="我的商品" name="products">
          <div v-if="myProductsList.length > 0" class="card-grid">
            <ProductCard
              v-for="p in myProductsList"
              :key="p.id"
              :product="p"
            />
          </div>
          <div v-else class="empty-state">
            <el-icon :size="48"><component :is="'Box'" /></el-icon>
            <p>还没有发布商品</p>
            <el-button type="success" round @click="router.push('/publish')">
              发布第一个商品
            </el-button>
          </div>
        </el-tab-pane>

        <el-tab-pane label="我的订单" name="orders">
          <template v-if="myOrdersList.length > 0">
            <div
              v-for="order in myOrdersList"
              :key="order.id"
              class="order-item"
              @click="router.push('/chat')"
            >
              <el-image
                v-if="order.product?.cover_image"
                :src="order.product.cover_image"
                fit="cover"
                class="order-pic"
              />
              <div v-else class="order-pic-placeholder">
                <el-icon :size="24"><component :is="'Picture'" /></el-icon>
              </div>
              <div class="order-body">
                <h4>{{ order.product?.title || '商品已删除' }}</h4>
                <p class="order-people">
                  {{ order.buyer?.nickname || '买家' }} → {{ order.seller?.nickname || '卖家' }}
                </p>
                <p class="order-price">{{ formatPrice(order.product?.price) }}</p>
              </div>
              <div class="order-tail">
                <el-tag
                  :type="orderStatusColors[order.status] || 'info'"
                  size="small"
                  effect="plain"
                >
                  {{ orderStatusLabels[order.status] || order.status_display }}
                </el-tag>
                <span class="order-time">{{ formatTime(order.created_at) }}</span>
              </div>
            </div>
          </template>
          <div v-else class="empty-state">
            <el-icon :size="48"><component :is="'Document'" /></el-icon>
            <p>还没有订单</p>
          </div>
        </el-tab-pane>

        <el-tab-pane label="信用记录" name="credit">
          <template v-if="creditRecords.length > 0">
            <div v-for="record in creditRecords" :key="record.id" class="credit-item">
              <div class="credit-left">
                <span
                  class="credit-change"
                  :class="record.change >= 0 ? 'positive' : 'negative'"
                >
                  {{ record.change >= 0 ? '+' : '' }}{{ record.change }}
                </span>
                <span class="credit-reason">{{ record.reason_display || record.reason }}</span>
              </div>
              <div class="credit-right">
                <span class="credit-balance">余额 {{ record.score_after }}</span>
                <span class="credit-desc">{{ record.description }}</span>
                <span class="credit-time">{{ formatTime(record.created_at) }}</span>
              </div>
            </div>
          </template>
          <div v-else class="empty-state">
            <el-icon :size="48"><component :is="'Clock'" /></el-icon>
            <p>还没有信用记录</p>
          </div>
        </el-tab-pane>
      </el-tabs>
    </section>

    <!-- Public profile -->
    <section v-else class="public-section">
      <div class="public-bio-card">
        <h3>个人简介</h3>
        <p>{{ profileUser.bio || '这个人很懒，什么都没写...' }}</p>
      </div>

      <div v-if="myProductsList.length > 0" class="public-products">
        <h3>TA 在售的商品 ({{ myProductsList.length }})</h3>
        <div class="card-grid">
          <ProductCard
            v-for="p in myProductsList"
            :key="p.id"
            :product="p"
          />
        </div>
      </div>
      <div v-else class="public-products">
        <h3>TA 在售的商品</h3>
        <div class="empty-state">
          <el-icon :size="36"><component :is="'Box'" /></el-icon>
          <p>暂无在售商品</p>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
/* Profile Header */
.profile-header {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  overflow: hidden;
  margin-bottom: 24px;
  box-shadow: var(--shadow-card);
}

.profile-cover {
  height: 140px;
  background: linear-gradient(135deg, var(--color-brand) 0%, #66bb6a 40%, var(--color-brand-light) 100%);
}

.profile-body {
  display: flex;
  align-items: flex-end;
  gap: 20px;
  padding: 0 28px 24px;
  margin-top: -44px;
}

.profile-avatar {
  border: 4px solid #fff;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
  flex-shrink: 0;
}

.profile-main {
  flex: 1;
  min-width: 0;
}

.profile-name-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
}

.profile-name-row h2 {
  font-size: 24px;
  font-weight: 700;
}

.profile-meta {
  color: var(--text-secondary);
  font-size: 13px;
  margin-bottom: 6px;
}

.profile-bio {
  color: var(--text-regular);
  font-size: 14px;
  line-height: 1.5;
  max-width: 480px;
}

.edit-btn {
  flex-shrink: 0;
  margin-bottom: 4px;
}

/* Edit Section */
.edit-section {
  background: var(--bg-card);
  padding: 24px 28px;
  border-radius: var(--radius-lg);
  margin-bottom: 24px;
  box-shadow: var(--shadow-card);
}

.edit-actions {
  display: flex;
  gap: 12px;
}

/* Tabs */
.profile-tabs {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 8px 24px 24px;
  box-shadow: var(--shadow-card);
}

/* Order Items */
.order-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 16px;
  border-radius: var(--radius-base);
  cursor: pointer;
  transition: background 0.2s;
  border-bottom: 1px solid var(--border-color);
}

.order-item:last-child {
  border-bottom: none;
}

.order-item:hover {
  background: var(--bg-page);
}

.order-pic {
  width: 56px;
  height: 56px;
  border-radius: 8px;
  flex-shrink: 0;
}

.order-pic-placeholder {
  width: 56px;
  height: 56px;
  border-radius: 8px;
  flex-shrink: 0;
  background: var(--bg-page);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--border-color);
}

.order-body {
  flex: 1;
  min-width: 0;
}

.order-body h4 {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.order-people {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 2px;
}

.order-price {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-price);
}

.order-tail {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  flex-shrink: 0;
}

.order-time {
  font-size: 12px;
  color: var(--text-secondary);
}

/* Credit Items */
.credit-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid var(--border-color);
}

.credit-item:last-child {
  border-bottom: none;
}

.credit-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.credit-change {
  font-weight: 700;
  font-size: 18px;
  min-width: 48px;
}

.credit-change.positive { color: var(--color-success); }
.credit-change.negative { color: var(--color-danger); }

.credit-reason {
  font-size: 14px;
  color: var(--text-primary);
}

.credit-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  font-size: 12px;
  color: var(--text-secondary);
}

.credit-balance {
  font-weight: 500;
  color: var(--text-regular);
}

/* Public profile */
.public-section {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 28px;
  box-shadow: var(--shadow-card);
}

.public-bio-card {
  margin-bottom: 28px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--border-color);
}

.public-bio-card h3,
.public-products h3 {
  font-size: 17px;
  font-weight: 600;
  margin-bottom: 12px;
}

.public-bio-card p {
  color: var(--text-regular);
  font-size: 14px;
  line-height: 1.6;
}

.public-products .empty-state {
  padding: 36px 0;
}

@media (max-width: 640px) {
  .profile-body {
    flex-direction: column;
    align-items: center;
    text-align: center;
    margin-top: -44px;
  }

  .profile-name-row {
    justify-content: center;
    flex-wrap: wrap;
  }

  .edit-btn {
    margin-bottom: 0;
  }

  .order-item {
    flex-wrap: wrap;
  }

  .credit-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }

  .credit-right {
    align-items: flex-start;
  }
}
</style>
