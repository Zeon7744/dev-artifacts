import { useEffect, useRef, useState, useCallback } from 'react'

/**
 * WebSocket 实时连接 hook
 * 自动连接 /api/ws（自动加入用户专属房间），断线指数退避重连。
 * 通知双通道：WS 实时推送 + 服务端持久化（连接后拉取未读历史）。
 * 返回：{ connected, notifications, unread, activities, sendMessage, subscribe,
 *        clearNotifications, refreshHistory }
 */
const API = (path) => {
  const token = localStorage.getItem('token')
  return fetch(`/api${path}`, {
    headers: { Authorization: token ? `Bearer ${token}` : '' },
  }).then((r) => (r.ok ? r.json() : null))
}

export function useRealtime() {
  const [connected, setConnected] = useState(false)
  const [notifications, setNotifications] = useState([])
  const [activities, setActivities] = useState([])
  const [unread, setUnread] = useState(0)
  const wsRef = useRef(null)
  const retryRef = useRef(0)
  const timerRef = useRef(null)

  const pushNotification = useCallback((n) => {
    const item = { id: Date.now() + Math.random(), ...n, time: new Date().toLocaleTimeString() }
    setNotifications((prev) => [item, ...prev].slice(0, 30))
    setActivities((prev) => [item, ...prev].slice(0, 50))
    // 服务端持久化的通知会贡献未读数；WS 实时通知到达时角标 +1
    if (n.type === 'notification') {
      setUnread((u) => u + 1)
    }
  }, [])

  const refreshHistory = useCallback(async () => {
    // 连接建立后拉取服务端未读通知与未读数（离线期间产生的通知）
    try {
      const [listRes, countRes] = await Promise.all([
        API('/notifications?limit=20'),
        API('/notifications/unread-count'),
      ])
      if (countRes && typeof countRes.unread === 'number') setUnread(countRes.unread)
      if (listRes && Array.isArray(listRes.items)) {
        const items = listRes.items.map((it) => ({
          id: `srv-${it.id}`,
          type: 'notification',
          category: it.category,
          message: it.title || it.content,
          level: it.level || 'info',
          data: it.data,
          time: it.created_at ? new Date(it.created_at).toLocaleTimeString() : '',
        }))
        setNotifications((prev) => {
          // 合并：服务端历史在前（按时间倒序），实时收到的保留
          const live = prev.filter((n) => !String(n.id).startsWith('srv-'))
          return [...live, ...items].slice(0, 30)
        })
      }
    } catch (e) {
      // 拉取历史失败不影响实时通道
    }
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
      refreshHistory()
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === 'pong') return
        if (msg.type === 'system') return
        // 通知 / 工作流 / 系统 / 插件等事件推送
        pushNotification({
          type: msg.type || 'event',
          message: msg.title || msg.message || msg.data?.message || JSON.stringify(msg.data || msg),
          level: msg.level || (msg.type === 'alert' ? 'warning' : 'info'),
          category: msg.category,
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
  }, [pushNotification, refreshHistory])

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

  const clearNotifications = useCallback(async () => {
    setNotifications([])
    setUnread(0)
    try {
      await fetch('/api/notifications/read-all', {
        method: 'POST',
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      })
    } catch (e) {
      // 标记失败不影响本地清空
    }
  }, [])

  useEffect(() => {
    connect()
    return () => {
      if (timerRef.current) clearTimeout(timerRef)
      if (wsRef.current) {
        wsRef.current.onclose = null
        wsRef.current.close()
      }
    }
  }, [connect])

  return {
    connected,
    notifications,
    unread,
    activities,
    sendMessage,
    subscribe,
    clearNotifications,
    refreshHistory,
  }
}
