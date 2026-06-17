export async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      ...(options.headers || {}),
    },
  })
  const payload = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(resolveErrorMessage(payload, response.status))
  }

  return payload
}

export async function postJson(url, body) {
  return fetchJson(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })
}

export async function putJson(url, body) {
  return fetchJson(url, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })
}

export async function deleteJson(url) {
  return fetchJson(url, {
    method: 'DELETE',
  })
}

export function toKoreanErrorMessage(message) {
  if (message.includes('GITHUB_OAUTH_CLIENT_ID')) {
    return '깃허브 OAuth Client ID가 설정되지 않았습니다.'
  }

  if (message.includes('GITHUB_OAUTH_CLIENT_SECRET')) {
    return '깃허브 OAuth Client Secret이 설정되지 않았습니다.'
  }

  if (message.includes('AUTH_JWT_SECRET_KEY')) {
    return 'JWT 비밀키가 설정되지 않았습니다.'
  }

  if (message.includes('authorization token is required')) {
    return '로그인이 필요합니다. 깃허브 로그인 버튼을 눌러주세요.'
  }

  if (message.includes('chat session not found')) {
    return '채팅 연결이 만료되었습니다. 새 대화로 다시 연결한 뒤 시도해 주세요.'
  }

  return message
}

function resolveErrorMessage(payload, status) {
  if (payload?.detail) {
    return typeof payload.detail === 'string'
      ? payload.detail
      : JSON.stringify(payload.detail)
  }

  return `요청 실패: ${status}`
}
