<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  getOrders, acceptOrder, rejectOrder, cancelOrder,
  generateConfirmCode, verifyConfirmCode, completeOrder,
  createReview,
} from '@/api/transactions'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import Rating from '@/components/common/Rating.vue'
import {
  formatPrice, formatTime, formatDateTime,
  orderStatusLabels, orderStatusColors,
} from '@/utils/format'

const router = useRouter()
const auth = useAuthStore()

const activeTab = ref('all')
const orders = ref([])
const loading = ref(false)

// Review dialog
const reviewDialog = ref(false)
const reviewOrder = ref(null)
const reviewRating = ref(5)
const reviewContent = ref('')

const statusTabs = [
  { name: 'all', label: '全部' },
  { name: 'pending', label: '待确认' },
  { name: 'active', label: '进行中' },
  { name: 'completed', label: '已完成' },
]

onMounted(async () => {
  await loadOrders()
})

async function loadOrders() {
  loading.value = true
  try {
    const params = {}
    if (activeTab.value === 'active') {
      params.status = 'accepted,face_confirm'
    } else if (activeTab.value !== 'all') {
      params.status = activeTab.value
    }
    const res = await getOrders(params)
    const data = res.data.data || res.data
    orders.value = data.results || data
  } catch {
    orders.value = []
  } finally {
    loading.value = false
  }
}

function switchTab(tab) {
  activeTab.value = tab
  loadOrders()
}

function isBuyer(order) {
  return auth.user?.id === order.buyer?.id
}

function isSeller(order) {
  return auth.user?.id === order.seller?.id
}

async function handleAccept(order) {
  try {
    await ElMessageBox.confirm('确定接受该订单吗？', '确认', { type: 'success' })
    await acceptOrder(order.id)
    ElMessage.success('订单已接受')
    loadOrders()
  } catch {}
}

async function handleReject(order) {
  try {
    const { value } = await ElMessageBox.prompt('请输入拒绝原因', '拒绝订单', {
      inputPlaceholder: '如：商品已售出、价格不合适等',
    })
    await rejectOrder(order.id, { reason: value })
    ElMessage.success('订单已拒绝')
    loadOrders()
  } catch {}
}

async function handleCancel(order) {
  try {
    const { value } = await ElMessageBox.prompt('请输入取消原因', '取消订单', {
      inputPlaceholder: '如：不想要了',
    })
    await cancelOrder(order.id, { reason: value })
    ElMessage.success('订单已取消')
    loadOrders()
  } catch {}
}

async function handleGenerateCode(order) {
  try {
    const res = await generateConfirmCode(order.id)
    const data = res.data.data || res.data
    await ElMessageBox.alert(`确认码: ${data.confirm_code}`, '面交确认码', {
      confirmButtonText: '知道了',
      type: 'success',
    })
    loadOrders()
  } catch {}
}

async function handleVerifyCode(order) {
  try {
    const { value } = await ElMessageBox.prompt('请输入卖家提供的 6 位确认码', '验证确认码', {
      inputPattern: /^\d{6}$/,
      inputErrorMessage: '请输入 6 位数字确认码',
    })
    await verifyConfirmCode(order.id, { code: value })
    ElMessage.success('验证成功')
    loadOrders()
  } catch {}
}

async function handleComplete(order) {
  try {
    await ElMessageBox.confirm('确认交易已完成？', '确认完成')
    await completeOrder(order.id)
    ElMessage.success('交易完成')
    loadOrders()
  } catch {}
}

function openReviewDialog(order) {
  reviewOrder.value = order
  reviewRating.value = 5
  reviewContent.value = ''
  reviewDialog.value = true
}

async function submitReview() {
  try {
    const revieweeId = isBuyer(reviewOrder.value)
      ? reviewOrder.value.seller.id
      : reviewOrder.value.buyer.id
    await createReview({
      order_id: reviewOrder.value.id,
      rating: reviewRating.value,
      content: reviewContent.value,
    })
    ElMessage.success('评价成功')
    reviewDialog.value = false
    loadOrders()
  } catch {}
}
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>我的订单</h2>
    </div>

    <div class="order-tabs">
      <el-radio-group v-model="activeTab" size="default" @change="switchTab">
        <el-radio-button
          v-for="tab in statusTabs"
          :key="tab.name"
          :value="tab.name"
        >
          {{ tab.label }}
        </el-radio-button>
      </el-radio-group>
    </div>

    <div v-if="loading" v-loading="loading" style="min-height: 200px"></div>

    <div v-else-if="orders.length > 0">
      <el-card
        v-for="order in orders"
        :key="order.id"
        class="order-card"
        shadow="hover"
      >
        <template #header>
          <div class="order-header">
            <el-tag :type="orderStatusColors[order.status] || 'info'" size="small">
              {{ orderStatusLabels[order.status] || order.status_display }}
            </el-tag>
            <span class="order-time">{{ formatDateTime(order.created_at) }}</span>
          </div>
        </template>

        <div class="order-body">
          <el-image
            v-if="order.product?.cover_image"
            :src="order.product.cover_image"
            fit="cover"
            class="order-image"
          />
          <div class="order-detail">
            <h4 @click="router.push(`/product/${order.product?.id}`)" class="order-title">
              {{ order.product?.title || '商品已删除' }}
            </h4>
            <div class="order-meta">
              <span class="order-price">{{ formatPrice(order.product?.price) }}</span>
              <span>{{ isBuyer(order) ? '卖家' : '买家' }}:
                {{ isBuyer(order) ? order.seller?.nickname : order.buyer?.nickname }}
              </span>
              <span v-if="order.meet_location">📍 {{ order.meet_location }}</span>
            </div>
          </div>

          <div class="order-actions">
            <!-- Seller: Pending -->
            <template v-if="isSeller(order) && order.status === 'pending'">
              <el-button size="small" type="success" @click="handleAccept(order)">接受</el-button>
              <el-button size="small" type="danger" plain @click="handleReject(order)">拒绝</el-button>
            </template>

            <!-- Buyer: Pending -->
            <el-button
              v-if="isBuyer(order) && order.status === 'pending'"
              size="small"
              type="danger"
              plain
              @click="handleCancel(order)"
            >
              取消
            </el-button>

            <!-- Seller: Accepted, generate code -->
            <el-button
              v-if="isSeller(order) && order.status === 'accepted'"
              size="small"
              type="primary"
              @click="handleGenerateCode(order)"
            >
              生成面交码
            </el-button>

            <!-- Buyer: face_confirm, verify code -->
            <el-button
              v-if="isBuyer(order) && order.status === 'face_confirm'"
              size="small"
              type="success"
              @click="handleVerifyCode(order)"
            >
              输入确认码
            </el-button>

            <!-- Either: complete after face_confirm -->
            <el-button
              v-if="order.status === 'completed' && !(isBuyer(order) ? order.buyer_rated : order.seller_rated)"
              size="small"
              type="warning"
              plain
              @click="openReviewDialog(order)"
            >
              去评价
            </el-button>
          </div>
        </div>
      </el-card>
    </div>

    <div v-else class="empty-state">
      <el-icon :size="56"><component :is="'Document'" /></el-icon>
      <p>还没有订单</p>
    </div>

    <!-- Review Dialog -->
    <el-dialog v-model="reviewDialog" title="交易评价" width="400px">
      <div class="review-form">
        <label>评分</label>
        <Rating v-model="reviewRating" size="large" />
        <label style="margin-top: 16px; display: block;">评价内容 (选填)</label>
        <el-input
          v-model="reviewContent"
          type="textarea"
          :rows="3"
          maxlength="500"
          show-word-limit
          style="margin-top: 8px;"
        />
      </div>
      <template #footer>
        <el-button @click="reviewDialog = false">取消</el-button>
        <el-button type="success" @click="submitReview">提交评价</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.order-tabs {
  margin-bottom: 20px;
}

.order-card {
  margin-bottom: 16px;
  border-radius: var(--radius-lg);
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.order-time {
  font-size: 12px;
  color: var(--text-secondary);
}

.order-body {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.order-image {
  width: 80px;
  height: 80px;
  border-radius: 8px;
  flex-shrink: 0;
}

.order-detail {
  flex: 1;
}

.order-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 8px;
  cursor: pointer;
}

.order-title:hover {
  color: #43a047;
}

.order-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 13px;
  color: var(--text-secondary);
}

.order-price {
  font-weight: 700;
  color: #e65100;
}

.order-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
  flex-wrap: wrap;
}

.review-form label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-regular);
}
</style>
