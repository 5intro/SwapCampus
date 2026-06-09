import client from './client'

export function createReport(data) {
  return client.post('/products/reports/', data)
}
