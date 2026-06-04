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
      unreadTotal.value = (data.results || data).reduce(
        (sum, c) => sum + (c.unread_count || 0),
        0,
      )
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

  return {
    conversations,
    currentConversation,
    unreadTotal,
    fetchConversations,
    fetchConversation,
    clearCurrent,
  }
})
