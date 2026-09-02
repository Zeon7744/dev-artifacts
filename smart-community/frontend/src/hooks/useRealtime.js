import { useEffect, useRef, useState, useCallback } from 'react'

/**
 * WebSocket 实时连接 hook
 * 自动连接 /api/ws，断线指数退避重连，订阅全局房间。
 * 返回：{ connected, notifications, activities, sendMessage, subscribe, clearNotifications }
 */
export function useRealtime() {
  const [connected, setConnected] = useState(false)
  const [notifications, setNotifications] = useState([])
  const [activities, setActivities] = useState([])
  const wsRef = useRef(null)
  const retryRef = useRef(0)
  const timerRef = useRef(null)

  const pushNotification = useCallback((n) => {
    const item = { id: Date.now() + Math.random(), ...n, time: new Date().toLocaleTimeString() }
    setNotifications((prev) => [item, ...prev].slice(0, 30))
    setActivities((prev) => [item, ...prev].slice(0, 50))
  }, [])

  const connect = useCallback(() => {
    const token = localStorage.getItem('token')
    if (!token) return
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const url = `${proto}://${window.location.host}/api/ws?token=${encodeURIComponent(token)}&room=global`
    let ws
    try {
      ws = new WebSocket(url)
    } catch (e) {
      scheduleReconnect()
      return
    }
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      retryRef.current = 0
      pushNotification({ type: 'system', message: '实时连接已建立', level: 'info' })
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === 'pong') return
        if (msg.type === 'system') return
        // 工作流/系统/插件等事件推送
        pushNotification({
          type: msg.type || 'event',
          message: msg.message || msg.data?.message || JSON.stringify(msg.data || msg),
          level: msg.level || (msg.type === 'alert' ? 'warning' : 'info'),
          data: msg.data,
        })
      } catch (e) {
        // 忽略非 JSON
      }
    }

    ws.onclose = (evt) => {
      setConnected(false)
      if (evt.code !== 4001) scheduleReconnect()
    }

    ws.onerror = () => {
      setConnected(false)
    }
  }, [pushNotification])

  const scheduleReconnect = useCallback(() => {
    if (timerRef.current) return
    const delay = Math.min(1000 * Math.pow(2, retryRef.current), 15000)
    retryRef.current += 1
    timerRef.current = setTimeout(() => {
      timerRef.current = null
      connect()
    }, delay)
  }, [connect])

  const sendMessage = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    }
  }, [])

  const subscribe = useCallback((room) => {
    sendMessage({ type: 'subscribe', room })
  }, [sendMessage])

  const clearNotifications = useCallback(() => setNotifications([]), [])

  useEffect(() => {
    connect()
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
      if (wsRef.current) {
        wsRef.current.onclose = null
        wsRef.current.close()
      }
    }
  }, [connect])

  return { connected, notifications, activities, sendMessage, subscribe, clearNotifications }
}
