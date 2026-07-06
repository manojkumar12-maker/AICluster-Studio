import { useState, useEffect, useCallback, useRef } from 'react'
import { getBaseUrl, getToken } from '../api/client'
import { login as apiLogin } from '../api/endpoints'
import { useAuthStore } from '../stores/authStore'

export function useBackend<T>(
  fetcher: () => Promise<T>,
  deps: any[] = [],
  intervalMs = 0,
) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const refresh = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const result = await fetcher()
      setData(result)
    } catch (err: any) {
      setError(err.message || 'An error occurred')
    } finally {
      setLoading(false)
    }
  }, deps)

  useEffect(() => {
    refresh()
    if (intervalMs > 0) {
      intervalRef.current = setInterval(refresh, intervalMs)
      return () => { if (intervalRef.current) clearInterval(intervalRef.current) }
    }
  }, [refresh, intervalMs])

  return { data, loading, error, refresh }
}

export function useHealthCheck() {
  const [healthy, setHealthy] = useState(false)
  const [checking, setChecking] = useState(true)

  const check = useCallback(async () => {
    try {
      setChecking(true)
      const res = await fetch(`${getBaseUrl()}/api/v1/health`, { signal: AbortSignal.timeout(3000) })
      setHealthy(res.ok)
    } catch { setHealthy(false) }
    finally { setChecking(false) }
  }, [])

  useEffect(() => { check(); const i = setInterval(check, 10000); return () => clearInterval(i) }, [check])

  return { healthy, checking, refresh: check }
}

export function useWebSocket(host: string, port: number, onEvent?: (event: any) => void) {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const connect = useCallback(() => {
    if (wsRef.current) { wsRef.current.close(); wsRef.current = null }
    const token = getToken()
    const url = `ws://${host}:${port}/ws${token ? `?token=${token}` : ''}`
    try {
      const ws = new WebSocket(url)
      ws.onopen = () => {}
      ws.onmessage = (msg) => { try { const d = JSON.parse(msg.data); if (onEvent) onEvent(d) } catch {} }
      ws.onclose = () => { wsRef.current = null; reconnectRef.current = setTimeout(connect, 5000) }
      ws.onerror = () => { ws.close() }
      wsRef.current = ws
    } catch { setTimeout(connect, 5000) }
  }, [host, port, onEvent])

  const disconnect = useCallback(() => {
    if (reconnectRef.current) clearTimeout(reconnectRef.current)
    if (wsRef.current) { wsRef.current.close(); wsRef.current = null }
  }, [])

  return { connect, disconnect }
}

export function useLoginForm() {
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('admin')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const { login: storeLogin } = useAuthStore()

  const submit = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await apiLogin({ username, password })
      storeLogin(result.access_token, username)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [username, password, storeLogin])

  return { username, setUsername, password, setPassword, error, loading, submit }
}
