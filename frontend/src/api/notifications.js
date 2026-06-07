import client from './client'

export function getNotifications(params) {
  return client.get('/notifications/', { params })
}

export function markRead(id) {
  return client.post(`/notifications/${id}/read/`)
}

export function markAllRead() {
  return client.post('/notifications/read-all/')
}
