import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
})

// ─── Collections ────────────────────────────────────────
export const getCollections = (params = {}) =>
  api.get('/collections', { params }).then(r => r.data)

export const getCollection = (name) =>
  api.get(`/collections/${name}`).then(r => r.data)

export const createCollection = (data) =>
  api.post('/collections', data).then(r => r.data)

export const updateCollection = (name, data) =>
  api.patch(`/collections/${name}`, data).then(r => r.data)

export const deleteCollection = (name) =>
  api.delete(`/collections/${name}?confirm=true`).then(r => r.data)

// ─── Documents ──────────────────────────────────────────
export const getDocuments = (collection, params = {}) =>
  api.get(`/collections/${collection}/documents`, { params }).then(r => r.data)

export const getDocument = (collection, docId) =>
  api.get(`/collections/${collection}/documents/${docId}`).then(r => r.data)

export const ingestDocuments = (collection, data) =>
  api.post(`/collections/${collection}/documents`, data).then(r => r.data)

export const uploadFile = (collection, formData) =>
  api.post(`/collections/${collection}/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  }).then(r => r.data)

export const deleteDocument = (collection, docId) =>
  api.delete(`/collections/${collection}/documents/${docId}`).then(r => r.data)

export const bulkDeleteDocuments = (collection, ids) =>
  api.post(`/collections/${collection}/documents/delete`, { ids }).then(r => r.data)

// ─── Search ─────────────────────────────────────────────
export const searchCollection = (collection, data) =>
  api.post(`/collections/${collection}/search`, data).then(r => r.data)

export const compareSearch = (collection, data) =>
  api.post(`/collections/${collection}/search/compare`, data).then(r => r.data)

export const multiSearch = (collection, data) =>
  api.post(`/collections/${collection}/search/multi`, data).then(r => r.data)

// ─── Storage ────────────────────────────────────────────
export const getStorageHealth = () =>
  api.get('/storage/health').then(r => r.data)

export const persistAll = () =>
  api.post('/storage/persist').then(r => r.data)

// ─── Health ─────────────────────────────────────────────
export const getHealth = () =>
  api.get('/health').then(r => r.data)

export default api
