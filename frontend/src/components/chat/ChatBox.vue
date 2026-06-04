<script setup>
import { ref, nextTick, onMounted, watch } from 'vue'
import { sendMessage } from '@/api/chat'
import MessageBubble from './MessageBubble.vue'

const props = defineProps({
  conversationId: { type: String, required: true },
  messages: { type: Array, default: () => [] },
  currentUserId: { type: String, default: '' },
})

const emit = defineEmits(['message-sent'])

const inputText = ref('')
const messagesContainer = ref(null)
const sending = ref(false)

watch(
  () => props.messages.length,
  () => scrollToBottom(),
)

onMounted(() => scrollToBottom())

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

async function handleSend() {
  const text = inputText.value.trim()
  if (!text || sending.value) return

  sending.value = true
  try {
    await sendMessage(props.conversationId, { content: text })
    inputText.value = ''
    emit('message-sent')
    scrollToBottom()
  } catch {
    // handled by interceptor
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <div class="chat-box">
    <div ref="messagesContainer" class="messages-area">
      <div v-if="messages.length === 0" class="chat-empty">
        <el-icon :size="48"><component :is="'ChatDotRound'" /></el-icon>
        <p>暂无消息，发送第一条消息吧</p>
      </div>

      <MessageBubble
        v-for="msg in messages"
        :key="msg.id"
        :message="msg"
        :is-mine="msg.sender === currentUserId"
      />
    </div>

    <div class="chat-input-area">
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="2"
        placeholder="输入消息..."
        resize="none"
        @keyup.enter.exact.prevent="handleSend"
      />
      <el-button
        type="success"
        :disabled="!inputText.trim() || sending"
        @click="handleSend"
        class="send-btn"
      >
        发送
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.chat-box {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.chat-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-secondary);
  gap: 12px;
}

.chat-input-area {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
  background: var(--bg-page);
  align-items: flex-end;
}

.chat-input-area :deep(.el-textarea__inner) {
  border-radius: 12px;
}

.send-btn {
  flex-shrink: 0;
  height: 40px;
}
</style>
