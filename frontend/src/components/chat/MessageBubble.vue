<script setup>
import { ref } from 'vue'
import { formatTime } from '@/utils/format'

defineProps({
  message: { type: Object, required: true },
  isMine: { type: Boolean, default: false },
})
</script>

<template>
  <div class="message-bubble" :class="{ 'message-mine': isMine }">
    <el-avatar
      v-if="!isMine"
      :size="32"
      class="msg-avatar"
    >
      {{ message.sender_name?.[0] || '?' }}
    </el-avatar>

    <div class="msg-body">
      <div class="msg-header" v-if="!isMine">
        <span class="msg-sender">{{ message.sender_name }}</span>
      </div>
      <div class="msg-content">{{ message.content }}</div>
      <div class="msg-time">{{ formatTime(message.created_at) }}</div>
    </div>

    <el-avatar
      v-if="isMine"
      :size="32"
      class="msg-avatar"
    >
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
  flex-direction: row-reverse;
}

.msg-avatar {
  flex-shrink: 0;
}

.msg-body {
  max-width: 65%;
}

.message-mine .msg-body {
  text-align: right;
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

.msg-time {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 4px;
}
</style>
