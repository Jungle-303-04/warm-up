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

export async function getCommentsByPost(postId) {
  const response = await fetch(`${API_BASE_URL}/comments/post/${postId}`)

  if (!response.ok) {
    throw new Error(`GET /comments/post/${postId} failed: ${response.status}`)
  }

  return response.json()
}

export async function createComment(postId, commentData) {
  const response = await fetch(`${API_BASE_URL}/comments/post/${postId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
    body: JSON.stringify(commentData),
  })

  if (!response.ok) {
    throw new Error(`POST /comments/post/${postId} failed: ${response.status}`)
  }

  return response.json()
}

export async function updateComment(commentId, commentData) {
  const response = await fetch(`${API_BASE_URL}/comments/${commentId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
    body: JSON.stringify(commentData),
  })

  if (!response.ok) {
    throw new Error(`PATCH /comments/${commentId} failed: ${response.status}`)
  }

  return response.json()
}

export async function deleteComment(commentId) {
  const response = await fetch(`${API_BASE_URL}/comments/${commentId}`, {
    method: 'DELETE',
    headers: {
      ...getAuthHeaders(),
    },
  })

  if (!response.ok) {
    throw new Error(`DELETE /comments/${commentId} failed: ${response.status}`)
  }

  return null
}
