const DEFAULT_HOST = '127.0.0.1'
const DEFAULT_PORT = 8000

let _baseUrl = `http://${DEFAULT_HOST}:${DEFAULT_PORT}`
let _token: string | null = null
let _onAuthFailure: (() => void) | null = null

export function setBaseUrl(host: string, port: number) {
  _baseUrl = `http://${host}:${port}`
}

export function setToken(token: string | null) {
  _token = token
}

export function getToken(): string | null {
  return _token
}

export function setOnAuthFailure(cb: () => void) {
  _onAuthFailure = cb
}

export function getBaseUrl(): string {
  return _baseUrl
}

export class ApiError extends Error {
  status: number
  detail?: string
  diagnosticId?: string
  constructor(
    status: number,
    message: string,
    detail?: string,
    diagnosticId?: string,
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
    this.diagnosticId = diagnosticId
  }
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  opts?: { skipAuth?: boolean; timeout?: number },
): Promise<T> {
  const controller = new AbortController()
  const timeout = opts?.timeout ?? 30000
  const timer = setTimeout(() => controller.abort(), timeout)

  try {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    if (_token && !opts?.skipAuth) {
      headers['Authorization'] = `Bearer ${_token}`
    }

    const res = await fetch(`${_baseUrl}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    })

    if (res.status === 401 && _onAuthFailure) {
      _onAuthFailure()
    }

    if (!res.ok) {
      let detail = ''
      try { const d = await res.json(); detail = d.detail || d.message || JSON.stringify(d) } catch { detail = res.statusText }
      throw new ApiError(res.status, `HTTP ${res.status}`, detail, `diag-${Date.now()}`)
    }

    if (res.status === 204) return undefined as T
    return (await res.json()) as T
  } catch (err: any) {
    if (err instanceof ApiError) throw err
    if (err.name === 'AbortError') throw new ApiError(0, 'Request timed out', `Timeout after ${timeout}ms`)
    throw new ApiError(0, 'Network error', err.message || 'Could not reach the server')
  } finally {
    clearTimeout(timer)
  }
}

export const api = {
  get: <T>(path: string, opts?: { skipAuth?: boolean; timeout?: number }) =>
    request<T>('GET', path, undefined, opts),
  post: <T>(path: string, body?: unknown, opts?: { skipAuth?: boolean }) =>
    request<T>('POST', path, body, opts),
  put: <T>(path: string, body?: unknown) =>
    request<T>('PUT', path, body),
  delete: <T>(path: string) =>
    request<T>('DELETE', path),
}
