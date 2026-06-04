import client from './client'

export function getOrders(params) {
  return client.get('/transactions/orders/', { params })
}

export function getOrder(id) {
  return client.get(`/transactions/orders/${id}/`)
}

export function createOrder(data) {
  return client.post('/transactions/orders/', data)
}

export function acceptOrder(id) {
  return client.post(`/transactions/orders/${id}/accept/`)
}

export function rejectOrder(id, data) {
  return client.post(`/transactions/orders/${id}/reject/`, data)
}

export function cancelOrder(id, data) {
  return client.post(`/transactions/orders/${id}/cancel/`, data)
}

export function generateConfirmCode(id) {
  return client.post(`/transactions/orders/${id}/generate_confirm_code/`)
}

export function verifyConfirmCode(id, data) {
  return client.post(`/transactions/orders/${id}/verify_confirm_code/`, data)
}

export function completeOrder(id) {
  return client.post(`/transactions/orders/${id}/complete/`)
}

export function createReview(data) {
  return client.post('/transactions/reviews/', data)
}
