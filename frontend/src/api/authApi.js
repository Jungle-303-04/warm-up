import { API_BASE_URL } from './config'

const ACCESS_TOKEN_KEY = 'access_token'

export function saveAccessToken(token) {
  localStorage.setItem(ACCESS_TOKEN_KEY, token)
}

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

export function removeAccessToken() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
}

export function isLoggedIn() {
  return Boolean(getAccessToken())
}

export async function signup(signupData) {
  const response = await fetch(`${API_BASE_URL}/auth/signup`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(signupData),
  })

  if (!response.ok) {
    throw new Error(`POST /auth/signup failed: ${response.status}`)
  }

  return response.json()
}

export async function login(loginData) {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(loginData),
  })

  if (!response.ok) {
    throw new Error(`POST /auth/login failed: ${response.status}`)
  }

  return response.json()
}

export async function getMe() {
  const token = getAccessToken()

  if (!token) {
    throw new Error('로그인이 필요합니다.')
  }

  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error(`GET /auth/me failed: ${response.status}`)
  }

  return response.json()
}
