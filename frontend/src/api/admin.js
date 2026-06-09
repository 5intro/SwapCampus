import client from './client'

// ── 仪表盘 ──
export function getDashboard() {
  return client.get('/admin/dashboard/')
}

// ── 商品管理 ──
export function getAdminProducts(params) {
  return client.get('/admin/products/', { params })
}

export function productAction(productId, action) {
  return client.post(`/admin/products/${productId}/${action}/`)
}

// ── 举报处理 ──
export function getAdminReports(params) {
  return client.get('/admin/reports/', { params })
}

export function handleReport(reportId, data) {
  return client.post(`/admin/reports/${reportId}/handle/`, data)
}

// ── 用户管理 ──
export function getAdminUsers(params) {
  return client.get('/admin/users/', { params })
}

export function manageUser(userId, data) {
  return client.post(`/admin/users/${userId}/manage/`, data)
}

// ── 学生证认证审核 ──
export function getVerifications(params) {
  return client.get('/admin/verifications/', { params })
}

export function reviewVerification(userId, data) {
  return client.post(`/admin/verifications/${userId}/review/`, data)
}
