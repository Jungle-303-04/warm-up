import { API_BASE_URL } from './config'

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

async function requestJson(path) {
  const response = await fetch(`${API_BASE_URL}${path}`)

  if (!response.ok) {
    throw new Error(`${path} failed: ${response.status}`)
  }

  return response.json()
}

export async function getNotionDocs(params = {}) {
  const queryString = buildQueryString({
    page_size: params.page_size ?? 20,
    start_cursor: params.start_cursor ?? '',
  })

  return requestJson(`/integrations/notion/docs${queryString}`)
}

export async function getNotionDoc(pageId) {
  return requestJson(`/integrations/notion/docs/${pageId}`)
}
