export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.PROD ? '/_/backend' : 'http://127.0.0.1:8000')
).replace(/\/$/, '')
