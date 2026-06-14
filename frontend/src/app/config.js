export const API_BASE_URL = normalizeApiBaseUrl(
  import.meta.env.VITE_API_BASE_URL || '/api',
)

export const OAUTH_STATE_STORAGE_KEY = 'warm-up.auth.githubState'
export const LEGACY_ACCESS_TOKEN_STORAGE_KEY = 'warm-up.auth.accessToken'
export const CALLBACK_PATH = '/auth/callback'

export const INITIAL_STATUS = {
  type: 'muted',
  message: '로그인 전입니다.',
}

function normalizeApiBaseUrl(value) {
  return value.replace(/\/$/, '')
}
