/**
 * Centralized API client for SentinelSOC frontend.
 *
 * Injects the auth token from localStorage and provides
 * consistent error handling.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL !== undefined 
  ? process.env.NEXT_PUBLIC_API_URL 
  : (typeof window !== 'undefined' ? '' : 'http://localhost:8000')

function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem('sentinel_token')
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

export interface ApiError {
  detail: string
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(body.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  get: async <T>(path: string): Promise<T> => {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: getAuthHeaders(),
    })
    return handleResponse<T>(res)
  },

  post: async <T>(path: string, body?: unknown): Promise<T> => {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: body ? JSON.stringify(body) : undefined,
    })
    return handleResponse<T>(res)
  },

  put: async <T>(path: string, body?: unknown): Promise<T> => {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: body ? JSON.stringify(body) : undefined,
    })
    return handleResponse<T>(res)
  },

  patch: async <T>(path: string, body?: unknown): Promise<T> => {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: body ? JSON.stringify(body) : undefined,
    })
    return handleResponse<T>(res)
  },

  delete: async <T>(path: string): Promise<T> => {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    })
    return handleResponse<T>(res)
  },
}
