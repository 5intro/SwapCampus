import client from './client'

export function getFavorites(params) {
  return client.get('/products/favorites/', { params })
}

export function addFavorite(productId) {
  return client.post('/products/favorites/', { product_id: productId })
}

export function removeFavorite(id) {
  return client.delete(`/products/favorites/${id}/`)
}

export function checkFavorite(productId) {
  return client.get('/products/favorites/', { params: { product_id: productId } })
}
