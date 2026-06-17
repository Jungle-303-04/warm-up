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

async function postJson(path) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: {
      ...getAuthHeaders(),
    },
  })

  if (!response.ok) {
    throw new Error(`${path} failed: ${response.status}`)
  }

  return response.json()
}

export async function createTodayBriefing() {
  return postJson('/ai/today-briefing')
}

export async function createTeamSummary() {
  return postJson('/ai/team-summary')
}
