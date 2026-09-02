import { useEffect, useState } from 'react'
import { api } from '../hooks/useAuth'
import { GitBranch, Bot, MessageSquare, Users, TrendingUp, Activity } from 'lucide-react'

export default function DashboardPage() {
  const [stats, setStats] = useState({ users: 0, workflows: 0, agents: 0, posts: 0 })

  useEffect(() => {
    api.get('/system/stats').then(({ data }) => setStats(data)).catch(() => {})
  }, [])

  const cards = [
    { icon: GitBranch, label: '工作流', value: stats.workflows, color: 'from-indigo-500 to-blue-500' },
    { icon: Bot, label: 'Agent', value: stats.agents, color: 'from-purple-500 to-pink-500' },
    { icon: Users, label: '用户', value: stats.users, color: 'from-green-500 to-teal-500' },
    { icon: MessageSquare, label: '社区帖子', value: stats.posts, color: 'from-orange-500 to-red-500' },
  ]

  return (
    <div className="p-8 animate-fade-in">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">控制台</h1>
        <p className="text-gray-500 mt-1">系统概览与快速操作</p>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-4 gap-6 mb-8">
        {cards.map((card) => (
          <div key={card.label} className="bg-[#1a1a2e] rounded-xl p-6 border border-[#27272a] hover:border-indigo-500/30 transition-all group">
            <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${card.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
              <card.icon size={22} className="text-white" />
            </div>
            <p className="text-3xl font-bold text-white">{card.value}</p>
            <p className="text-sm text-gray-500 mt-1">{card.label}</p>
          </div>
        ))}
      </div>

      {/* 快速操作 */}
      <div className="grid grid-cols-2 gap-6 mb-8">
        <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#27272a]">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Activity size={18} className="text-indigo-400" /> 最近活动
          </h3>
          <div className="space-y-3">
            {['工作流「每日简报」执行成功', '新Agent「市场分析助手」已发布', '社区帖子获得12个赞', '系统健康检查通过'].map((item, i) => (
              <div key={i} className="flex items-center gap-3 text-sm text-gray-400">
                <div className="w-2 h-2 rounded-full bg-green-400" />
                {item}
              </div>
            ))}
          </div>
        </div>

        <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#27272a]">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp size={18} className="text-green-400" /> 系统状态
          </h3>
          <div className="space-y-4">
            {[
              { label: 'CPU', value: 23, color: 'bg-green-500' },
              { label: '内存', value: 45, color: 'bg-blue-500' },
              { label: 'API 响应', value: 12, color: 'bg-purple-500' },
            ].map((m) => (
              <div key={m.label}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-400">{m.label}</span>
                  <span className="text-white">{m.value}%</span>
                </div>
                <div className="h-2 bg-[#0a0a0f] rounded-full overflow-hidden">
                  <div className={`h-full ${m.color} rounded-full transition-all`} style={{ width: `${m.value}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
