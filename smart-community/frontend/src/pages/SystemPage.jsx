import { useEffect, useState } from 'react'
import { api } from '../hooks/useAuth'
import { Activity, AlertTriangle, CheckCircle, Server } from 'lucide-react'

export default function SystemPage() {
  const [health, setHealth] = useState(null)
  const [alerts, setAlerts] = useState([])

  useEffect(() => {
    api.get('/system/health').then(({ data }) => setHealth(data)).catch(() => {})
    api.get('/system/alerts').then(({ data }) => setAlerts(data)).catch(() => setAlerts([]))
  }, [])

  return (
    <div className="p-8 animate-fade-in">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">智能运维</h1>
        <p className="text-gray-500 mt-1">系统监控、告警与自动化运维</p>
      </div>

      {/* 健康状态 */}
      <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#27272a] mb-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Server size={18} className="text-green-400" /> 系统健康
        </h3>
        <div className="grid grid-cols-3 gap-4">
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${health?.status === 'healthy' ? 'bg-green-400' : 'bg-red-400'}`} />
            <span className="text-gray-300">API服务: {health?.status || '检查中...'}</span>
          </div>
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${health?.llm_providers?.ollama ? 'bg-green-400' : 'bg-gray-500'}`} />
            <span className="text-gray-300">Ollama: {health?.llm_providers?.ollama ? '在线' : '离线'}</span>
          </div>
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${health?.llm_providers?.openai ? 'bg-green-400' : 'bg-gray-500'}`} />
            <span className="text-gray-300">OpenAI: {health?.llm_providers?.openai ? '可用' : '未配置'}</span>
          </div>
        </div>
      </div>

      {/* 告警 */}
      <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#27272a]">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <AlertTriangle size={18} className="text-yellow-400" /> 告警列表
        </h3>
        {alerts.length === 0 ? (
          <div className="flex items-center gap-3 text-green-400 py-8 justify-center">
            <CheckCircle size={24} />
            <span>暂无告警，系统运行正常</span>
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.map((alert) => (
              <div key={alert.id} className={`flex items-center gap-3 p-3 rounded-lg ${alert.severity === 'critical' ? 'bg-red-500/10 border border-red-500/20' : 'bg-yellow-500/10 border border-yellow-500/20'}`}>
                <AlertTriangle size={16} className={alert.severity === 'critical' ? 'text-red-400' : 'text-yellow-400'} />
                <div>
                  <p className="text-sm text-white">{alert.title}</p>
                  <p className="text-xs text-gray-500">{alert.message}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
