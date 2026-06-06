import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getConversations, getConversation } from '@/api/chat'

export const useChatStore = defineStore('chat', () => {
  const conversations = ref([])
  const currentConversation = ref(null)
  const unreadTotal = ref(0)

  async function fetchConversations() {
    try {
      const res = await getConversations()
      const data = res.data.data || res.data
      conversations.value = data.results || data
      updateUnreadTotal()
    } catch {
      // silently fail
    }
  }

  async function fetchConversation(id) {
    try {
      const res = await getConversation(id)
      currentConversation.value = res.data.data || res.data
      return currentConversation.value
    } catch {
      return null
    }
  }

  function clearCurrent() {
    currentConversation.value = null
  }

  // ── 实时未读管理 ──────────────────────────────────────

  function updateUnreadTotal() {
    unreadTotal.value = conversations.value.reduce(
      (sum, c) => sum + (c.unread_count || 0),
      0,
    )
  }

  function markConversationRead(conversationId) {
    const conv = conversations.value.find(c => c.id === conversationId)
    if (conv) {
      conv.unread_count = 0
      updateUnreadTotal()
    }
  }

  function incrementUnread(conversationId, message) {
    const conv = conversations.value.find(c => c.id === conversationId)
    if (conv) {
      conv.unread_count = (conv.unread_count || 0) + 1
      conv.last_message = {
        id: message.id,
        sender_name: message.sender_name,
        content: message.content,
        created_at: message.created_at,
      }
      updateUnreadTotal()
    } else {
      // 新会话不在列表中，需要重新拉取
      fetchConversations()
    }
  }

  function updateMessageReadStatus(messageIds) {
    // 更新当前会话消息的已读状态
    if (currentConversation.value?.messages) {
      const idSet = new Set(messageIds)
      currentConversation.value.messages.forEach(msg => {
        if (idSet.has(msg.id)) {
          msg.is_read = true
        }
      })
    }
  }

  return {
    conversations,
    currentConversation,
    unreadTotal,
    fetchConversations,
    fetchConversation,
    clearCurrent,
    updateUnreadTotal,
    markConversationRead,
    incrementUnread,
    updateMessageReadStatus,
  }
})
