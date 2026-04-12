export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL||'https://super-duper-couscous-v4x77545rpq2wgp6-8000.app.github.dev' || 'http://localhost:8000').replace(/\/$/, '')

export function apiUrl(path = '') {
  if (!path) return API_BASE_URL
  const normalized = path.startsWith('/') ? path : `/${path}`
  return `${API_BASE_URL}${normalized}`
}
