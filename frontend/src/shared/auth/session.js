import {
  CALLBACK_PATH,
  LEGACY_ACCESS_TOKEN_STORAGE_KEY,
  OAUTH_STATE_STORAGE_KEY,
} from '../../app/config'

export function isGithubCallbackPage() {
  return window.location.pathname === CALLBACK_PATH
}

export function clearCallbackUrl() {
  window.history.replaceState({}, document.title, '/')
}

export function clearSession() {
  window.localStorage.removeItem(OAUTH_STATE_STORAGE_KEY)
  window.localStorage.removeItem(LEGACY_ACCESS_TOKEN_STORAGE_KEY)
}
