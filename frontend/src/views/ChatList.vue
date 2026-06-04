<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getConversations } from '@/api/chat'
import { formatTime } from '@/utils/format'
import { ElAvatar } from 'element-plus'

const router = useRouter()
const auth = useAuthStore()

const conversations = ref([])
const loading = ref(false)
let pollTimer = null

onMounted(async () => {
  await fetchList()
  pollTimer = setInterval(fetchList, 10000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

async function fetchList() {
  loading.value = true
  try {
    const res = await getConversations()
    const data = res.data.data || res.data
    conversations.value = data.results || data
  } catch {
    conversations.value = []
  } finally {
    loading.value = false
  }
}

function getOtherParticipant(conv) {
  if (!auth.user) return { name: '用户', id: '' }
  const names = conv.participant_names || []
  return names.find(p => p.id !== auth.user.id) || { name: '用户', id: '' }
}

function getTitle(conv) {
  return conv.title || getOtherParticipant(conv).name
}
</script>

<template>
  <div class="page-container">
    <div class="chat-list-card">
      <div class="page-header">
        <h2>消息</h2>
      </div>

      <div v-if="loading && conversations.length === 0" v-loading="loading" style="min-height: 200px"></div>

      <div v-else-if="conversations.length > 0">
        <div
          v-for="conv in conversations"
          :key="conv.id"
          class="chat-item"
          @click="router.push(`/chat/${conv.id}`)"
        >
          <el-avatar :size="48" class="chat-item-avatar">
            {{ getTitle(conv)[0] }}
          </el-avatar>

          <div class="chat-item-body">
            <div class="chat-item-header">
              <span class="chat-item-name">{{ getTitle(conv) }}</span>
              <span class="chat-item-time">{{ formatTime(conv.last_message?.created_at || conv.updated_at) }}</span>
            </div>
            <div class="chat-item-preview">
              <span v-if="conv.last_message">
                {{ conv.last_message.sender_name }}: {{ conv.last_message.content }}
              </span>
              <span v-else class="no-preview">暂无消息</span>
            </div>
          </div>

          <el-badge
            v-if="conv.unread_count > 0"
            :value="conv.unread_count"
            class="unread-dot"
          />
        </div>
      </div>

      <div v-else class="empty-state">
        <el-icon :size="56"><component :is="'ChatDotRound'" /></el-icon>
        <p>还没有消息</p>
        <p class="empty-tip">去商品页面联系卖家开始聊天吧~</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-list-card {
  max-width: 680px;
  margin: 0 auto;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 20px 8px;
  box-shadow: var(--shadow-card);
}

.page-header {
  padding: 0 16px;
  margin-bottom: 8px;
}

.chat-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  cursor: pointer;
  border-radius: var(--radius-base);
  transition: background 0.15s;
}

.chat-item:hover {
  background: var(--bg-page);
}

.chat-item-avatar {
  flex-shrink: 0;
}

.chat-item-body {
  flex: 1;
  min-width: 0;
}

.chat-item-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.chat-item-name {
  font-weight: 600;
  font-size: 15px;
}

.chat-item-time {
  font-size: 12px;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.chat-item-preview {
  font-size: 13px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.no-preview {
  font-style: italic;
}

.unread-dot {
  flex-shrink: 0;
}

.empty-tip {
  font-size: 13px;
  margin-top: 4px;
}
</style>
