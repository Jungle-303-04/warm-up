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
