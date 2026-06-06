<script setup>
import { ref } from 'vue'
import { formatTime } from '@/utils/format'

defineProps({
  message: { type: Object, required: true },
  isMine: { type: Boolean, default: false },
})
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
      <div class="msg-content">{{ message.content }}</div>
      <div class="msg-time">{{ formatTime(message.created_at) }}</div>
    </div>
  </div>

  <!-- 自己消息：[消息] [头像] -->
  <div v-else class="message-bubble message-mine">
    <div class="msg-body">
      <div class="msg-content">{{ message.content }}</div>
      <div class="msg-meta">
        <span class="msg-time">{{ formatTime(message.created_at) }}</span>
        <span class="msg-read-status" :class="{ 'is-read': message.is_read }">
          {{ message.is_read ? '已读' : '未读' }}
        </span>
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
</style>
