import client from './client'

export function getProducts(params) {
  return client.get('/products/', { params })
}

export function getProduct(id) {
  return client.get(`/products/${id}/`)
}

export function createProduct(data) {
  return client.post('/products/', data, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function updateProduct(id, data) {
  return client.patch(`/products/${id}/`, data, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function getCategories() {
  return client.get('/products/categories/')
}

export function getTags() {
  return client.get('/products/tags/')
}

export function getMyProducts() {
  return client.get('/products/', { params: { my: true } })
}
