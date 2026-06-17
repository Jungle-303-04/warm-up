import { getAccessToken } from './authApi'
import { API_BASE_URL } from './config'

function getAuthHeaders() {
  const token = getAccessToken()

  if (!token) {
    throw new Error('로그인이 필요합니다.')
  }

  return {
    Authorization: `Bearer ${token}`,
  }
}

export async function syncDocuments(syncData) {
  const response = await fetch(`${API_BASE_URL}/ai/sync-documents`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
    body: JSON.stringify(syncData),
  })

  if (!response.ok) {
    throw new Error(`POST /ai/sync-documents failed: ${response.status}`)
  }

  return response.json()
}

export async function askDocs(questionData) {
  const response = await fetch(`${API_BASE_URL}/ai/ask-docs`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
    body: JSON.stringify(questionData),
  })

  if (!response.ok) {
    throw new Error(`POST /ai/ask-docs failed: ${response.status}`)
  }

  return response.json()
}
