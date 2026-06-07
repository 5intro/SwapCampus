<script setup>
import { ref, onMounted } from 'vue'
import { getNotifications, markRead, markAllRead } from '@/api/notifications'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { formatDateTime } from '@/utils/format'

const router = useRouter()
const notifications = ref([])
const loading = ref(false)

const typeLabels = {
  order_update: '订单更新',
  new_order: '新订单',
  new_message: '新消息',
  credit_change: '积分变动',
  new_review: '新评价',
  system: '系统通知',
}

const typeIcons = {
  order_update: 'Document',
  new_order: 'ShoppingCartFull',
  new_message: 'ChatDotRound',
  credit_change: 'Coin',
  new_review: 'StarFilled',
  system: 'InfoFilled',
}

onMounted(() => { loadNotifs() })

async function loadNotifs() {
  loading.value = true
  try {
    const res = await getNotifications({ page_size: 50 })
    const data = res.data.data || res.data
    notifications.value = data.results || data
  } catch {
    notifications.value = []
  } finally {
    loading.value = false
  }
}

async function handleClick(notif) {
  if (!notif.is_read) {
    try {
      await markRead(notif.id)
      notif.is_read = true
    } catch {}
  }
  if (notif.related_order) {
    router.push('/my-orders')
  } else if (notif.related_product) {
    router.push(`/product/${notif.related_product}`)
  }
}

async function handleMarkAll() {
  try {
    await markAllRead()
    notifications.value.forEach(n => n.is_read = true)
    ElMessage.success('全部标记为已读')
  } catch {}
}
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>通知</h2>
      <el-button text type="primary" @click="handleMarkAll">全部已读</el-button>
    </div>

    <div v-if="loading" v-loading="loading" style="min-height: 200px"></div>

    <div v-else-if="notifications.length > 0">
      <div
        v-for="notif in notifications"
        :key="notif.id"
        class="notif-item"
        :class="{ unread: !notif.is_read }"
        @click="handleClick(notif)"
      >
        <el-icon :size="24" class="notif-icon">
          <component :is="typeIcons[notif.type] || 'Bell'" />
        </el-icon>
        <div class="notif-body">
          <div class="notif-title">
            <span class="notif-tag">{{ typeLabels[notif.type] || notif.type_display }}</span>
            {{ notif.title }}
          </div>
          <div class="notif-content">{{ notif.content }}</div>
          <div class="notif-time">{{ formatDateTime(notif.created_at) }}</div>
        </div>
        <div v-if="!notif.is_read" class="unread-dot"></div>
      </div>
    </div>

    <div v-else class="empty-state">
      <el-icon :size="56"><component :is="'Bell'" /></el-icon>
      <p>暂无通知</p>
    </div>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.notif-item {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 16px;
  background: var(--bg-card);
  border-radius: var(--radius-base);
  margin-bottom: 10px;
  cursor: pointer;
  transition: background 0.2s;
  position: relative;
}

.notif-item:hover {
  background: var(--bg-page);
}

.notif-item.unread {
  background: #f1f8e9;
}

.notif-icon {
  margin-top: 2px;
  color: #43a047;
  flex-shrink: 0;
}

.notif-body {
  flex: 1;
  min-width: 0;
}

.notif-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 4px;
}

.notif-tag {
  display: inline-block;
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 4px;
  background: #e8f5e9;
  color: #2e7d32;
  margin-right: 6px;
}

.notif-content {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.notif-time {
  font-size: 11px;
  color: var(--text-placeholder);
}

.unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #43a047;
  flex-shrink: 0;
  margin-top: 6px;
}
</style>
