<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  getDashboard,
  getAdminProducts,
  productAction,
  getAdminReports,
  handleReport,
  getAdminUsers,
  manageUser,
  getVerifications,
  reviewVerification,
} from '@/api/admin'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ShoppingCart,
  Warning,
  User,
  TrendCharts,
} from '@element-plus/icons-vue'

const router = useRouter()
const auth = useAuthStore()

// 权限检查
if (!auth.user?.is_staff) {
  router.replace('/')
}

// ── 状态 ──
const activeTab = ref('dashboard')
const loading = ref(false)

// 仪表盘数据
const dashboard = ref({})

// 商品管理
const products = ref([])
const productPagination = ref({ page: 1, page_size: 20, total: 0 })
const productStatusFilter = ref('')
const productSearch = ref('')

// 举报管理
const reports = ref([])
const reportPagination = ref({ page: 1, page_size: 20, total: 0 })
const reportStatusFilter = ref('pending')

// 用户管理
const users = ref([])
const userPagination = ref({ page: 1, page_size: 20, total: 0 })
const userSearch = ref('')

// 学生证认证审核
const verifications = ref([])
const verificationPagination = ref({ page: 1, page_size: 20, total: 0 })
const verificationStatusFilter = ref('pending')

onMounted(() => {
  loadDashboard()
})

// ═══════════════════════════════════════════════════════════
// 仪表盘
// ═══════════════════════════════════════════════════════════
async function loadDashboard() {
  try {
    const res = await getDashboard()
    dashboard.value = (res.data && res.data.data) ? res.data.data : res.data
  } catch { /* handled */ }
}

// ═══════════════════════════════════════════════════════════
// 商品管理
// ═══════════════════════════════════════════════════════════
async function loadProducts(page = 1) {
  loading.value = true
  try {
    const params = { page, page_size: 20 }
    if (productStatusFilter.value) params.status = productStatusFilter.value
    if (productSearch.value) params.search = productSearch.value
    const res = await getAdminProducts(params)
    const d = res.data
    products.value = d.data || d.results || []
    productPagination.value = d.pagination || { page: 1, page_size: 20, total: 0 }
  } catch { /* handled */ } finally {
    loading.value = false
  }
}

async function doProductAction(productId, action) {
  try {
    await productAction(productId, action)
    ElMessage.success('操作成功')
    loadProducts(productPagination.value.page)
    loadDashboard()
  } catch (e) {
    ElMessage.error(e?.response?.data?.error?.message || '操作失败')
  }
}

// ═══════════════════════════════════════════════════════════
// 举报管理
// ═══════════════════════════════════════════════════════════
async function loadReports(page = 1) {
  loading.value = true
  try {
    const params = { page, page_size: 20 }
    if (reportStatusFilter.value) params.status = reportStatusFilter.value
    const res = await getAdminReports(params)
    const d = res.data
    reports.value = d.data || d.results || []
    reportPagination.value = d.pagination || { page: 1, page_size: 20, total: 0 }
  } catch { /* handled */ } finally {
    loading.value = false
  }
}

async function doHandleReport(reportId, action) {
  try {
    const { value: note } = await ElMessageBox.prompt('处理备注（可选）', '处理举报', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPlaceholder: '输入处理备注...',
    })
    await handleReport(reportId, { action, note: note || '' })
    ElMessage.success('处理完成')
    loadReports(reportPagination.value.page)
    loadDashboard()
  } catch {
    // 用户取消
  }
}

// ═══════════════════════════════════════════════════════════
// 用户管理
// ═══════════════════════════════════════════════════════════
async function loadUsers(page = 1) {
  loading.value = true
  try {
    const params = { page, page_size: 20 }
    if (userSearch.value) params.search = userSearch.value
    const res = await getAdminUsers(params)
    const d = res.data
    users.value = d.data || d.results || []
    userPagination.value = d.pagination || { page: 1, page_size: 20, total: 0 }
  } catch { /* handled */ } finally {
    loading.value = false
  }
}

async function doManageUser(userId, action) {
  const actionText = action === 'ban' ? '封禁' : '解封'
  try {
    await ElMessageBox.confirm(`确定要${actionText}该用户吗？`, '用户管理', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await manageUser(userId, { action })
    ElMessage.success(`${actionText}成功`)
    loadUsers(userPagination.value.page)
    loadDashboard()
  } catch {
    // 用户取消
  }
}

// ═══════════════════════════════════════════════════════════
// 学生证认证审核
// ═══════════════════════════════════════════════════════════
async function loadVerifications(page = 1) {
  loading.value = true
  try {
    const params = { page, page_size: 20 }
    if (verificationStatusFilter.value) params.status = verificationStatusFilter.value
    const res = await getVerifications(params)
    const d = res.data
    verifications.value = d.data || d.results || []
    verificationPagination.value = d.pagination || { page: 1, page_size: 20, total: 0 }
  } catch { /* handled */ } finally {
    loading.value = false
  }
}

async function doReviewVerification(userId, action) {
  const actionText = action === 'approve' ? '通过' : '拒绝'
  try {
    const { value: note } = await ElMessageBox.prompt(
      action === 'reject' ? '请输入拒绝原因（必填）' : '审核备注（可选）',
      `${actionText}认证`,
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputPlaceholder: action === 'reject' ? '如：学生证信息不清晰' : '',
        inputValidator: action === 'reject' ? (val) => val ? true : '拒绝时必须填写原因' : undefined,
      }
    )
    await reviewVerification(userId, { action, note: note || '' })
    ElMessage.success(`${actionText}成功`)
    loadVerifications(verificationPagination.value.page)
    loadDashboard()
  } catch {
    // 用户取消
  }
}

// ═══════════════════════════════════════════════════════════
// Tab 切换
// ═══════════════════════════════════════════════════════════
function onTabChange(tab) {
  if (tab === 'products') loadProducts()
  else if (tab === 'reports') loadReports()
  else if (tab === 'users') loadUsers()
  else if (tab === 'verifications') loadVerifications()
  else if (tab === 'dashboard') loadDashboard()
}

function onPageChange(page) {
  if (activeTab.value === 'products') loadProducts(page)
  else if (activeTab.value === 'reports') loadReports(page)
  else if (activeTab.value === 'users') loadUsers(page)
  else if (activeTab.value === 'verifications') loadVerifications(page)
}
</script>

<template>
  <div class="admin-page">
    <div class="admin-header">
      <h1>
        <span class="admin-header-icon">&#9881;</span>
        后台管理
      </h1>
    </div>

    <el-tabs v-model="activeTab" @tab-change="onTabChange" type="border-card">
      <!-- ═══════════════════════════ 仪表盘 ═══════════════════════════ -->
      <el-tab-pane label="数据看板" name="dashboard">
        <div class="dashboard-grid">
          <el-card class="stat-card">
            <div class="stat-icon" style="background: #e8f5e9"><el-icon :size="28" color="#43a047"><User /></el-icon></div>
            <div class="stat-info">
              <div class="stat-value">{{ dashboard.total_users || 0 }}</div>
              <div class="stat-label">活跃用户</div>
            </div>
          </el-card>
          <el-card class="stat-card">
            <div class="stat-icon" style="background: #e3f2fd"><el-icon :size="28" color="#1976d2"><ShoppingCart /></el-icon></div>
            <div class="stat-info">
              <div class="stat-value">{{ dashboard.active_products || 0 }}</div>
              <div class="stat-label">在售商品</div>
            </div>
          </el-card>
          <el-card class="stat-card">
            <div class="stat-icon" style="background: #fff3e0"><el-icon :size="28" color="#f57c00"><TrendCharts /></el-icon></div>
            <div class="stat-info">
              <div class="stat-value">{{ dashboard.pending_orders || 0 }}</div>
              <div class="stat-label">待处理订单</div>
            </div>
          </el-card>
          <el-card class="stat-card">
            <div class="stat-icon" style="background: #fce4ec"><el-icon :size="28" color="#d32f2f"><Warning /></el-icon></div>
            <div class="stat-info">
              <div class="stat-value">{{ dashboard.pending_reports || 0 }}</div>
              <div class="stat-label">待处理举报</div>
            </div>
          </el-card>
        </div>

        <h3 class="section-title">最近注册用户</h3>
        <el-table :data="dashboard.recent_registrations || []" stripe>
          <el-table-column prop="username" label="用户名" />
          <el-table-column prop="nickname" label="昵称" />
          <el-table-column label="注册时间">
            <template #default="{ row }">
              {{ new Date(row.date_joined).toLocaleDateString('zh-CN') }}
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- ═══════════════════════════ 商品管理 ═══════════════════════════ -->
      <el-tab-pane label="商品管理" name="products">
        <div class="toolbar">
          <el-input
            v-model="productSearch"
            placeholder="搜索商品..."
            clearable
            style="width: 240px"
            @keyup.enter="loadProducts()"
          />
          <el-select v-model="productStatusFilter" placeholder="状态筛选" clearable @change="loadProducts()" style="width: 140px">
            <el-option label="在售" value="active" />
            <el-option label="已预定" value="reserved" />
            <el-option label="已售出" value="sold" />
            <el-option label="已隐藏" value="hidden" />
          </el-select>
          <el-button type="success" @click="loadProducts()">查询</el-button>
        </div>

        <el-table :data="products" stripe v-loading="loading">
          <el-table-column prop="title" label="商品标题" min-width="180" />
          <el-table-column prop="price" label="价格" width="100" />
          <el-table-column prop="status_display" label="状态" width="100" />
          <el-table-column label="卖家" width="120">
            <template #default="{ row }">{{ row.seller?.nickname || row.seller?.username }}</template>
          </el-table-column>
          <el-table-column prop="category" label="分类" width="100" />
          <el-table-column label="操作" width="240" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="row.status !== 'active'"
                size="small"
                type="success"
                @click="doProductAction(row.id, 'approve')"
              >审核通过</el-button>
              <el-button
                v-if="row.status === 'active'"
                size="small"
                type="warning"
                @click="doProductAction(row.id, 'hide')"
              >隐藏</el-button>
              <el-button
                size="small"
                type="danger"
                @click="doProductAction(row.id, 'delete')"
              >删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination
          v-if="productPagination.total > 20"
          :current-page="productPagination.page"
          :page-size="20"
          :total="productPagination.total"
          layout="prev, pager, next"
          @current-change="page => onPageChange(page)"
          style="margin-top: 16px; justify-content: center"
        />
      </el-tab-pane>

      <!-- ═══════════════════════════ 举报处理 ═══════════════════════════ -->
      <el-tab-pane label="举报处理" name="reports">
        <div class="toolbar">
          <el-select v-model="reportStatusFilter" @change="loadReports()" style="width: 140px">
            <el-option label="待处理" value="pending" />
            <el-option label="已处理" value="resolved" />
            <el-option label="已驳回" value="dismissed" />
          </el-select>
        </div>

        <el-table :data="reports" stripe v-loading="loading">
          <el-table-column label="举报人" width="120">
            <template #default="{ row }">{{ row.reporter?.nickname || row.reporter?.username }}</template>
          </el-table-column>
          <el-table-column label="被举报商品" min-width="160">
            <template #default="{ row }">{{ row.product?.title }}</template>
          </el-table-column>
          <el-table-column prop="reason_display" label="举报原因" width="120" />
          <el-table-column prop="description" label="详细说明" min-width="160" show-overflow-tooltip />
          <el-table-column prop="status_display" label="状态" width="100" />
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <template v-if="row.status === 'pending'">
                <el-button size="small" type="success" @click="doHandleReport(row.id, 'resolve')">处理</el-button>
                <el-button size="small" type="info" @click="doHandleReport(row.id, 'dismiss')">驳回</el-button>
              </template>
              <span v-else class="text-secondary">已处理</span>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination
          v-if="reportPagination.total > 20"
          :current-page="reportPagination.page"
          :page-size="20"
          :total="reportPagination.total"
          layout="prev, pager, next"
          @current-change="page => onPageChange(page)"
          style="margin-top: 16px; justify-content: center"
        />
      </el-tab-pane>

      <!-- ═══════════════════════════ 用户管理 ═══════════════════════════ -->
      <el-tab-pane label="用户管理" name="users">
        <div class="toolbar">
          <el-input
            v-model="userSearch"
            placeholder="搜索用户（用户名/昵称）..."
            clearable
            style="width: 280px"
            @keyup.enter="loadUsers()"
          />
          <el-button type="success" @click="loadUsers()">查询</el-button>
        </div>

        <el-table :data="users" stripe v-loading="loading">
          <el-table-column prop="username" label="用户名" width="120" />
          <el-table-column prop="nickname" label="昵称" width="120" />
          <el-table-column label="信用分" width="90">
            <template #default="{ row }">
              <el-tag
                :type="row.credit_score >= 100 ? 'success' : row.credit_score >= 60 ? 'warning' : 'danger'"
                size="small"
              >{{ row.credit_score }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="campus" label="校区" width="100" />
          <el-table-column label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
                {{ row.is_active ? '正常' : '已封禁' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="注册时间" width="120">
            <template #default="{ row }">
              {{ new Date(row.date_joined).toLocaleDateString('zh-CN') }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="row.is_active"
                size="small"
                type="danger"
                @click="doManageUser(row.id, 'ban')"
              >封禁</el-button>
              <el-button
                v-else
                size="small"
                type="success"
                @click="doManageUser(row.id, 'unban')"
              >解封</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination
          v-if="userPagination.total > 20"
          :current-page="userPagination.page"
          :page-size="20"
          :total="userPagination.total"
          layout="prev, pager, next"
          @current-change="page => onPageChange(page)"
          style="margin-top: 16px; justify-content: center"
        />
      </el-tab-pane>

      <!-- ═══════════════════════════ 学生证审核 ═══════════════════════════ -->
      <el-tab-pane label="学生证审核" name="verifications">
        <div class="toolbar">
          <el-select v-model="verificationStatusFilter" @change="loadVerifications()" style="width: 140px">
            <el-option label="待审核" value="pending" />
            <el-option label="已通过" value="approved" />
            <el-option label="已拒绝" value="rejected" />
          </el-select>
        </div>

        <el-table :data="verifications" stripe v-loading="loading">
          <el-table-column label="用户" width="150">
            <template #default="{ row }">{{ row.nickname || row.username }}</template>
          </el-table-column>
          <el-table-column prop="username" label="用户名" width="120" />
          <el-table-column label="学生证" width="120">
            <template #default="{ row }">
              <el-image
                v-if="row.student_id_card"
                :src="row.student_id_card"
                :preview-src-list="[row.student_id_card]"
                fit="cover"
                style="width: 60px; height: 40px; border-radius: 4px; cursor: pointer"
              />
              <span v-else class="text-secondary">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="verification_status_display" label="状态" width="100">
            <template #default="{ row }">
              <el-tag
                :type="row.verification_status === 'approved' ? 'success' : row.verification_status === 'rejected' ? 'danger' : 'warning'"
                size="small"
              >{{ row.verification_status_display }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="verification_note" label="审核备注" min-width="160" show-overflow-tooltip>
            <template #default="{ row }">
              <span v-if="row.verification_note">{{ row.verification_note }}</span>
              <span v-else class="text-secondary">-</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <template v-if="row.verification_status === 'pending'">
                <el-button size="small" type="success" @click="doReviewVerification(row.id, 'approve')">通过</el-button>
                <el-button size="small" type="danger" @click="doReviewVerification(row.id, 'reject')">拒绝</el-button>
              </template>
              <span v-else class="text-secondary">已处理</span>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination
          v-if="verificationPagination.total > 20"
          :current-page="verificationPagination.page"
          :page-size="20"
          :total="verificationPagination.total"
          layout="prev, pager, next"
          @current-change="page => onPageChange(page)"
          style="margin-top: 16px; justify-content: center"
        />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style scoped>
.admin-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.admin-header {
  margin-bottom: 20px;
}

.admin-header h1 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 24px;
  color: var(--text-primary);
  margin: 0;
}

.admin-header-icon {
  font-size: 22px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

@media (max-width: 768px) {
  .dashboard-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.stat-card {
  display: flex;
  align-items: center;
}

.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 12px 0;
}

.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.text-secondary {
  color: var(--text-secondary);
  font-size: 13px;
}
</style>
