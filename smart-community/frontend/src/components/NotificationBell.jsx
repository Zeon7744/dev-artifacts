import { useState, useRef, useEffect } from 'react'
import { Bell, Wifi, WifiOff, Trash2, CheckCheck } from 'lucide-react'
import { useRealtime } from '../hooks/useRealtime'

/** 顶部实时通知铃铛 + WebSocket 连接状态 */
export default function NotificationBell() {
  const [open, setOpen] = useState(false)
  const { connected, notifications, unread, clearNotifications } = useRealtime()
  const ref = useRef(null)

  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const badge = Math.min(unread, 99)

  const levelDot = (n) => {
    const level = n.level
    if (level === 'error') return 'bg-red-400'
    if (level === 'warning') return 'bg-orange-400'
    if (level === 'success') return 'bg-emerald-400'
    return 'bg-indigo-400'
  }

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="relative p-2 rounded-lg hover:bg-white/5 text-gray-400 hover:text-white transition-all"
        title={connected ? '实时已连接' : '实时未连接（重连中）'}
      >
        {connected ? <Wifi size={18} className="text-green-400" /> : <WifiOff size={18} className="text-gray-600" />}
        {badge > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[16px] h-4 px-1 bg-red-500 rounded-full text-[10px] text-white flex items-center justify-center font-medium">
            {badge > 9 ? '9+' : badge}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-12 w-80 bg-[#1a1a2e] border border-[#27272a] rounded-xl shadow-2xl z-50 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-[#27272a]">
            <div className="flex items-center gap-2">
              <Bell size={15} className="text-indigo-400" />
              <span className="text-sm font-semibold text-white">实时通知</span>
              {unread > 0 && (
                <span className="text-[10px] bg-red-500/20 text-red-300 px-1.5 py-0.5 rounded">
                  {unread} 未读
                </span>
              )}
            </div>
            <button
              onClick={clearNotifications}
              className="flex items-center gap-1 text-gray-500 hover:text-indigo-300 text-xs"
              title="全部标记已读"
            >
              <CheckCheck size={14} />
              <Trash2 size={13} />
            </button>
          </div>
          <div className="max-h-80 overflow-auto">
            {notifications.length === 0 ? (
              <p className="text-center text-gray-600 text-sm py-8">暂无通知</p>
            ) : (
              notifications.map((n) => (
                <div key={n.id} className="px-4 py-3 border-b border-[#27272a]/50 hover:bg-white/5">
                  <div className="flex items-start gap-2">
                    <div className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${levelDot(n)}`} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-200 break-words">{n.message}</p>
                      <p className="text-xs text-gray-600 mt-1">
                        {n.category ? <span className="text-indigo-400/70 mr-2">{n.category}</span> : null}
                        {n.time}
                      </p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
