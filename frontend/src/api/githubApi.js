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

export async function getGithubIssues(params = {}) {
  const queryString = buildQueryString({
    state: params.state ?? 'open',
    assignee: params.assignee ?? '',
    labels: params.labels ?? '',
    page: params.page ?? 1,
    per_page: params.per_page ?? 20,
  })

  return requestJson(`/integrations/github/issues${queryString}`)
}

export async function getGithubPullRequests(params = {}) {
  const queryString = buildQueryString({
    state: params.state ?? 'open',
    page: params.page ?? 1,
    per_page: params.per_page ?? 20,
  })

  return requestJson(`/integrations/github/pulls${queryString}`)
}

export async function getGithubCommits(params = {}) {
  const queryString = buildQueryString({
    sha: params.sha ?? '',
    since: params.since ?? '',
    page: params.page ?? 1,
    per_page: params.per_page ?? 20,
  })

  return requestJson(`/integrations/github/commits${queryString}`)
}
