import client from './client'

export function getConversations() {
  return client.get('/chat/conversations/')
}

export function createConversation(data) {
  return client.post('/chat/conversations/', data)
}

export function getConversation(id) {
  return client.get(`/chat/conversations/${id}/`)
}

export function getMessages(id, params) {
  return client.get(`/chat/conversations/${id}/messages/`, { params })
}

export function sendMessage(id, data) {
  return client.post(`/chat/conversations/${id}/messages/`, data)
}

export function markRead(id) {
  return client.post(`/chat/conversations/${id}/read/`)
}
