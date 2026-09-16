export const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

const ACCESS_KEY = 'conveyor_access_token'
const REFRESH_KEY = 'conveyor_refresh_token'

export function getAccessToken() { return localStorage.getItem(ACCESS_KEY) }
export function getRefreshToken() { return localStorage.getItem(REFRESH_KEY) }
export function hasSession() { return Boolean(getAccessToken() || getRefreshToken()) }

export function saveTokens(tokens) {
  localStorage.setItem(ACCESS_KEY, tokens.access)
  if (tokens.refresh) localStorage.setItem(REFRESH_KEY, tokens.refresh)
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

export async function login(username, password) {
  const response = await fetch(`${API}/auth/token/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!response.ok) {
    const error = new Error(response.status === 401 ? 'invalid_credentials' : 'login_unavailable')
    error.status = response.status
    throw error
  }
  const tokens = await response.json()
  saveTokens(tokens)
  return tokens
}

async function refreshAccessToken() {
  const refresh = getRefreshToken()
  if (!refresh) return null
  const response = await fetch(`${API}/auth/token/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  })
  if (!response.ok) {
    clearTokens()
    return null
  }
  const tokens = await response.json()
  saveTokens({ access: tokens.access, refresh: tokens.refresh || refresh })
  return tokens.access
}

export async function authFetch(url, options = {}) {
  const headers = new Headers(options.headers || {})
  const access = getAccessToken()
  if (access) headers.set('Authorization', `Bearer ${access}`)

  let response = await fetch(url, { ...options, headers })
  if (response.status !== 401) return response

  const newAccess = await refreshAccessToken()
  if (!newAccess) return response

  headers.set('Authorization', `Bearer ${newAccess}`)
  return fetch(url, { ...options, headers })
}
