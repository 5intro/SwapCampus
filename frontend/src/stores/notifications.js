import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getNotifications } from '@/api/notifications'

export const useNotificationsStore = defineStore('notifications', () => {
  const unreadCount = ref(0)

  async function fetchUnreadCount() {
    try {
      const res = await getNotifications({ page_size: 1, is_read: false })
      unreadCount.value = res.data.pagination?.total || 0
    } catch {}
  }

  function clearUnread() {
    unreadCount.value = 0
  }

  function decrementUnread() {
    if (unreadCount.value > 0) unreadCount.value--
  }

  return { unreadCount, fetchUnreadCount, clearUnread, decrementUnread }
})
