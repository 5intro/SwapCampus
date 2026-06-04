import client from './client'

export function getUserProfile() {
  return client.get('/users/me/')
}

export function updateUserProfile(data) {
  return client.patch('/users/me/', data, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function getUser(id) {
  return client.get(`/users/${id}/`)
}

export function getCreditRecords(id) {
  return client.get(`/users/${id}/credit-records/`)
}
