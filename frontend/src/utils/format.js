export function formatPrice(price) {
  if (price == null) return ''
  const num = typeof price === 'string' ? parseFloat(price) : price
  return `¥${num.toFixed(2)}`
}

export function formatTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)} 天前`

  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
}

export function formatDateTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export const conditionLabels = {
  new: '全新',
  like_new: '几乎全新',
  used: '使用过',
  old: '老旧',
}

export const conditionColors = {
  new: 'success',
  like_new: 'primary',
  used: 'warning',
  old: 'info',
}

export const statusLabels = {
  active: '在售',
  reserved: '已预定',
  sold: '已售出',
  hidden: '已隐藏',
}

export const orderStatusLabels = {
  pending: '等待卖家确认',
  accepted: '已接受，待面交',
  rejected: '已拒绝',
  cancelled: '已取消',
  face_confirm: '面交确认中',
  completed: '已完成',
}

export const orderStatusColors = {
  pending: 'warning',
  accepted: 'primary',
  rejected: 'info',
  cancelled: 'info',
  face_confirm: 'success',
  completed: 'success',
}

export const creditLevelLabels = {
  excellent: '信用极好',
  good: '信用良好',
  fair: '信用一般',
  poor: '信用较差',
}

export const creditLevelColors = {
  excellent: '#67c23a',
  good: '#409eff',
  fair: '#e6a23c',
  poor: '#f56c6c',
}
