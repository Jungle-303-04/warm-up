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

function buildQueryString(params) {
  const searchParams = new URLSearchParams()

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.set(key, value)
    }
  })

  const queryString = searchParams.toString()

  return queryString ? `?${queryString}` : ''
}

export async function getPosts(params = {}) {
  const queryString = buildQueryString(params)
  const response = await fetch(`${API_BASE_URL}/posts${queryString}`)

  if (!response.ok) {
    throw new Error(`GET /posts failed: ${response.status}`)
  }

  return response.json()
}

export async function getPost(postId) {
  const response = await fetch(`${API_BASE_URL}/posts/${postId}`)

  if (!response.ok) {
    throw new Error(`GET /posts/${postId} failed: ${response.status}`)
  }

  return response.json()
}

export async function createPost(postData) {
  const response = await fetch(`${API_BASE_URL}/posts`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
    body: JSON.stringify(postData),
  })

  if (!response.ok) {
    throw new Error(`POST /posts failed: ${response.status}`)
  }

  return response.json()
}

export async function updatePost(postId, postData) {
  const response = await fetch(`${API_BASE_URL}/posts/${postId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
    body: JSON.stringify(postData),
  })

  if (!response.ok) {
    throw new Error(`PATCH /posts/${postId} failed: ${response.status}`)
  }

  return response.json()
}

export async function deletePost(postId) {
  const response = await fetch(`${API_BASE_URL}/posts/${postId}`, {
    method: 'DELETE',
    headers: {
      ...getAuthHeaders(),
    },
  })

  if (!response.ok) {
    throw new Error(`DELETE /posts/${postId} failed: ${response.status}`)
  }

  return null
}
