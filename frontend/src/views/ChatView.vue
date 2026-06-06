<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import { getConversation, markRead } from '@/api/chat'
import ChatBox from '@/components/chat/ChatBox.vue'
import { ElAvatar } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const chatStore = useChatStore()

const conversation = ref(null)
const messages = ref([])
let pollTimer = null
let ws = null
let reconnectTimer = null

onMounted(async () => {
  await loadConversation()
  connectWebSocket()

  // Poll as fallback
  pollTimer = setInterval(loadConversation, 8000)

  // Mark as read via REST (fallback for offline messages)
  try { await markRead(route.params.id) } catch {}
  // Also mark as read via WebSocket (real-time sync)
  sendReadConversation()
  // Update store unread count
  chatStore.markConversationRead(route.params.id)
})

onUnmounted(() => {
  if (ws) ws.close()
  if (pollTimer) clearInterval(pollTimer)
  if (reconnectTimer) clearTimeout(reconnectTimer)
})

function connectWebSocket() {
  const token = auth.token
  if (!token) return

  // 关闭旧连接
  if (ws) {
    ws.onclose = null  // 阻止旧 onclose 触发重连
    ws.close()
  }

  const wsUrl = `ws://${window.location.host}/ws/chat/${route.params.id}/?token=${token}`
  ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    // 连接成功后发送 read_conversation 标记已读
    sendReadConversation()
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)

      if (data.type === 'new_message') {
        const msg = data.message
        messages.value.push(msg)
        // 收到新消息时，如果当前页面可见，立即标记已读
        if (document.visibilityState === 'visible') {
          sendReadConversation()
        }
      } else if (data.type === 'messages_read') {
        // 对方已读了我的消息，更新消息状态
        if (data.message_ids) {
          const idSet = new Set(data.message_ids)
          messages.value.forEach(msg => {
            if (idSet.has(msg.id)) {
              msg.is_read = true
            }
          })
        }
      }
    } catch { /* ignore malformed messages */ }
  }

  ws.onclose = () => {
    // reconnect after 3 seconds if page is still active
    reconnectTimer = setTimeout(() => {
      if (document.visibilityState === 'visible') {
        connectWebSocket()
      }
    }, 3000)
  }
}

function sendReadConversation() {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'read_conversation' }))
  }
}

async function loadConversation() {
  try {
    const res = await getConversation(route.params.id)
    conversation.value = res.data.data || res.data
    if (conversation.value?.messages) {
      messages.value = conversation.value.messages
    }
  } catch {}
}

function handleMessageSent() {
  loadConversation()
}

function getTitle() {
  return conversation.value?.title || '聊天'
}

function goBack() {
  router.push('/chat')
}
</script>

<template>
  <div class="chat-page">
    <div class="chat-header">
      <el-button :icon="ArrowLeft" text @click="goBack" />
      <el-avatar :size="36">
        {{ getTitle()[0] }}
      </el-avatar>
      <span class="chat-title">{{ getTitle() }}</span>
    </div>

    <div class="chat-body" v-if="conversation">
      <ChatBox
        :conversation-id="route.params.id"
        :messages="messages"
        :current-user-id="auth.user?.id || ''"
        @message-sent="handleMessageSent"
      />
    </div>

    <div v-else class="chat-loading" v-loading="true" style="min-height: 400px"></div>
  </div>
</template>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
  max-width: 800px;
  margin: 0 auto;
}

.chat-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.chat-title {
  font-weight: 600;
  font-size: 16px;
}

.chat-body {
  flex: 1;
  overflow: hidden;
  padding: 0;
}
</style>
