<script setup>
import { computed } from 'vue'
import { formatTime } from '@/utils/format'

const props = defineProps({
  message: { type: Object, required: true },
  isMine: { type: Boolean, default: false },
})

const emit = defineEmits(['recall'])

// 是否在 3 分钟撤回窗口内
const canRecall = computed(() => {
  if (!props.isMine || props.message.is_recalled) return false
  const msgTime = new Date(props.message.created_at)
  const now = new Date()
  return (now - msgTime) < 3 * 60 * 1000
})

function handleRecall() {
  emit('recall', props.message.id)
}
</script>

<template>
  <!-- 对方消息：[头像] [消息] -->
  <div v-if="!isMine" class="message-bubble">
    <el-avatar :size="32" class="msg-avatar">
      {{ message.sender_name?.[0] || '?' }}
    </el-avatar>
    <div class="msg-body">
      <div class="msg-header">
        <span class="msg-sender">{{ message.sender_name }}</span>
      </div>
      <div
        class="msg-content"
        :class="{ 'msg-recalled': message.is_recalled }"
      >
        {{ message.content }}
      </div>
      <div class="msg-time">{{ formatTime(message.created_at) }}</div>
    </div>
  </div>

  <!-- 自己消息：[消息] [头像] -->
  <div v-else class="message-bubble message-mine">
    <div class="msg-body">
      <div
        class="msg-content"
        :class="{ 'msg-recalled': message.is_recalled }"
      >
        {{ message.content }}
      </div>
      <div class="msg-meta">
        <span v-if="canRecall" class="msg-recall-btn" @click="handleRecall">撤回</span>
        <span class="msg-time">{{ formatTime(message.created_at) }}</span>
        <span v-if="!message.is_recalled" class="msg-read-status" :class="{ 'is-read': message.is_read }">
          {{ message.is_read ? '已读' : '未读' }}
        </span>
        <span v-else class="msg-recalled-label">已撤回</span>
      </div>
    </div>
    <el-avatar :size="32" class="msg-avatar">
      {{ message.sender_name?.[0] || '我' }}
    </el-avatar>
  </div>
</template>

<style scoped>
.message-bubble {
  display: flex;
  gap: 10px;
  margin-bottom: 18px;
  align-items: flex-start;
}

.message-mine {
  justify-content: flex-end;
}

.msg-avatar {
  flex-shrink: 0;
}

.msg-body {
  max-width: 65%;
}

.msg-header {
  margin-bottom: 4px;
}

.msg-sender {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.msg-content {
  display: inline-block;
  padding: 10px 16px;
  border-radius: 18px;
  font-size: 14px;
  line-height: 1.5;
  background: #f0f2f5;
  color: var(--text-primary);
  word-break: break-word;
}

.message-mine .msg-content {
  background: linear-gradient(135deg, #43a047, #66bb6a);
  color: #fff;
}

.msg-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
}

.message-mine .msg-meta {
  justify-content: flex-end;
}

.msg-time {
  font-size: 11px;
  color: var(--text-secondary);
}

.msg-read-status {
  font-size: 11px;
  color: #b0b0b0;
  transition: color 0.3s;
}

.msg-read-status.is-read {
  color: var(--text-secondary);
}

.msg-recall-btn {
  font-size: 11px;
  color: #909399;
  cursor: pointer;
  transition: color 0.2s;
}

.msg-recall-btn:hover {
  color: #e65100;
}

.msg-recalled {
  background: #f5f5f5 !important;
  color: #909399 !important;
  font-style: italic;
  border: 1px dashed #d0d0d0;
}

.message-mine .msg-recalled {
  background: #f5f5f5 !important;
  color: #909399 !important;
  border: 1px dashed #d0d0d0;
  background-image: none !important;
}

.msg-recalled-label {
  font-size: 11px;
  color: #909399;
  font-style: italic;
}
</style>
