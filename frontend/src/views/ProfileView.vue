<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getUser, getUserProfile, updateUserProfile, getCreditRecords } from '@/api/users'
import { getOrders } from '@/api/transactions'
import { getMyProducts } from '@/api/products'
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

// Edit mode
const editing = ref(false)
const editForm = ref({
  nickname: '',
  bio: '',
  campus: '',
})

onMounted(async () => {
  const userId = route.params.id

  if (!userId) {
    // /profile
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
    // View another user's public profile
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
  }
})

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
    <div class="profile-header">
      <div class="profile-cover"></div>
      <div class="profile-info">
        <el-avatar :size="80" :src="profileUser.avatar" class="profile-avatar">
          {{ profileUser.nickname?.[0] || profileUser.username?.[0] || '?' }}
        </el-avatar>
        <div class="profile-text">
          <h2>{{ profileUser.nickname || profileUser.username }}</h2>
          <p class="profile-username">学号: {{ profileUser.username }}</p>
          <CreditBadge
            v-if="profileUser.credit_score != null"
            :score="profileUser.credit_score"
            :level="profileUser.credit_level"
          />
        </div>
        <el-button
          v-if="isOwn && !editing"
          @click="startEdit"
          type="default"
          round
        >
          编辑资料
        </el-button>
      </div>
    </div>

    <!-- Edit Form -->
    <div v-if="editing" class="edit-section">
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
    </div>

    <!-- Tabs (own profile only) -->
    <div v-if="isOwn" class="profile-tabs">
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
          <div v-if="myOrdersList.length > 0">
            <el-card
              v-for="order in myOrdersList"
              :key="order.id"
              class="order-card"
              shadow="hover"
              @click="router.push(`/chat`)"
            >
              <div class="order-row">
                <el-image
                  v-if="order.product?.cover_image"
                  :src="order.product.cover_image"
                  fit="cover"
                  class="order-image"
                />
                <div class="order-info">
                  <h4>{{ order.product?.title || '商品已删除' }}</h4>
                  <p>
                    {{ formatPrice(order.product?.price) }}
                    &middot;
                    {{ order.buyer?.nickname || '买家' }} → {{ order.seller?.nickname || '卖家' }}
                  </p>
                </div>
                <div class="order-right">
                  <el-tag
                    :type="orderStatusColors[order.status] || 'info'"
                    size="small"
                  >
                    {{ orderStatusLabels[order.status] || order.status_display }}
                  </el-tag>
                  <span class="order-date">{{ formatTime(order.created_at) }}</span>
                </div>
              </div>
            </el-card>
          </div>
          <div v-else class="empty-state">
            <el-icon :size="48"><component :is="'Document'" /></el-icon>
            <p>还没有订单</p>
          </div>
        </el-tab-pane>

        <el-tab-pane label="信用记录" name="credit">
          <div v-if="creditRecords.length > 0">
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
                <span class="credit-after">余额: {{ record.score_after }}</span>
                <span class="credit-desc">{{ record.description }}</span>
                <span class="credit-time">{{ formatTime(record.created_at) }}</span>
              </div>
            </div>
          </div>
          <div v-else class="empty-state">
            <el-icon :size="48"><component :is="'Clock'" /></el-icon>
            <p>还没有信用记录</p>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- Public profile: just bio -->
    <div v-else class="public-bio">
      <el-card>
        <h3>个人简介</h3>
        <p>{{ profileUser.bio || '这个人很懒，什么都没写...' }}</p>
        <p class="bio-meta">
          加入于 {{ formatDateTime(profileUser.date_joined) }}
          &middot; {{ profileUser.campus || '未知校区' }}
        </p>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.profile-header {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  overflow: hidden;
  margin-bottom: 24px;
  box-shadow: var(--shadow-card);
}

.profile-cover {
  height: 140px;
  background: linear-gradient(135deg, #43a047 0%, #66bb6a 40%, #a5d6a7 100%);
}

.profile-info {
  display: flex;
  align-items: flex-end;
  gap: 20px;
  padding: 0 24px 24px;
  margin-top: -40px;
}

.profile-avatar {
  border: 4px solid #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.profile-text {
  flex: 1;
}

.profile-text h2 {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 4px;
}

.profile-username {
  color: var(--text-secondary);
  font-size: 13px;
  margin-bottom: 8px;
}

.edit-section {
  background: var(--bg-card);
  padding: 24px;
  border-radius: var(--radius-lg);
  margin-bottom: 24px;
}

.edit-actions {
  display: flex;
  gap: 12px;
}

.profile-tabs {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 8px 20px 20px;
}

.order-card {
  margin-bottom: 12px;
  border-radius: var(--radius-base);
  cursor: pointer;
}

.order-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.order-image {
  width: 64px;
  height: 64px;
  border-radius: 8px;
  flex-shrink: 0;
}

.order-info {
  flex: 1;
}

.order-info h4 {
  font-size: 15px;
  margin-bottom: 4px;
}

.order-info p {
  font-size: 13px;
  color: var(--text-secondary);
}

.order-right {
  text-align: right;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.order-date {
  font-size: 12px;
  color: var(--text-secondary);
}

.credit-item {
  display: flex;
  justify-content: space-between;
  padding: 14px 0;
  border-bottom: 1px solid var(--border-color);
}

.credit-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.credit-change {
  font-weight: 700;
  font-size: 16px;
  min-width: 50px;
}

.credit-change.positive { color: var(--color-success); }
.credit-change.negative { color: var(--color-danger); }

.credit-reason {
  font-size: 14px;
}

.credit-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  font-size: 12px;
  color: var(--text-secondary);
}

.credit-after {
  font-weight: 500;
}

.public-bio {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 4px;
}

.public-bio h3 { margin-bottom: 12px; }
.public-bio p { color: var(--text-regular); font-size: 14px; }

.bio-meta {
  margin-top: 16px;
  color: var(--text-secondary) !important;
  font-size: 13px !important;
}
</style>
