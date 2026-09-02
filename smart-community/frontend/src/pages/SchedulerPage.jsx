import { useEffect, useState } from 'react'
import { api } from '../hooks/useAuth'
import { Clock, Calendar, Play, Trash2, RefreshCw } from 'lucide-react'

const CRON_PRESETS = [
  { label: '每天 9:00', cron: '0 9 * * *' },
  { label: '每天 18:00', cron: '0 18 * * *' },
  { label: '每小时', cron: '0 * * * *' },
  { label: '每周一 9:00', cron: '0 9 * * 1' },
  { label: '每月1号 9:00', cron: '0 9 1 * *' },
]

export default function SchedulerPage() {
  const [jobs, setJobs] = useState([])
  const [workflows, setWorkflows] = useState([])
  const [history, setHistory] = useState([])
  const [selectedWf, setSelectedWf] = useState('')
  const [cron, setCron] = useState('0 9 * * *')
  const [loading, setLoading] = useState(false)
  const [msg, setMsg] = useState('')

  const load = async () => {
    try {
      const [j, w, h] = await Promise.all([
        api.get('/scheduler/jobs').catch(() => ({ data: [] })),
        api.get('/workflows/').catch(() => ({ data: [] })),
        api.get('/scheduler/history').catch(() => ({ data: [] })),
      ])
      setJobs(j.data || [])
      setWorkflows(w.data || [])
      setHistory(h.data || [])
    } catch (e) { /* ignore */ }
  }

  useEffect(() => { load() }, [])

  const schedule = async () => {
    if (!selectedWf) { setMsg('请先选择工作流'); return }
    setLoading(true); setMsg('')
    try {
      await api.post(`/scheduler/workflows/${selectedWf}/schedule`, { cron })
      setMsg('✅ 调度已创建')
      load()
    } catch (e) {
      setMsg('❌ ' + (e.response?.data?.detail || '创建失败，检查 cron 表达式'))
    } finally { setLoading(false) }
  }

  const unschedule = async (wfId) => {
    try {
      await api.delete(`/scheduler/workflows/${wfId}/schedule`)
      load()
    } catch (e) { setMsg('❌ 取消失败') }
  }

  return (
    <div className="p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Clock className="text-indigo-400" /> 定时调度
          </h1>
          <p className="text-gray-500 mt-1">用 Cron 表达式定时自动执行工作流</p>
        </div>
        <button onClick={load} className="p-2 rounded-lg hover:bg-white/5 text-gray-400">
          <RefreshCw size={18} />
        </button>
      </div>

      {msg && <div className="mb-4 px-4 py-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-sm text-indigo-300">{msg}</div>}

      {/* 创建调度 */}
      <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#27272a] mb-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Calendar size={18} className="text-purple-400" /> 新建定时任务
        </h3>
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="text-sm text-gray-400 block mb-2">选择工作流</label>
            <select value={selectedWf} onChange={(e) => setSelectedWf(e.target.value)}
              className="w-full bg-[#0a0a0f] border border-[#27272a] rounded-lg px-3 py-2 text-white text-sm focus:border-indigo-500 outline-none">
              <option value="">-- 请选择 --</option>
              {workflows.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
            </select>
          </div>
          <div>
            <label className="text-sm text-gray-400 block mb-2">Cron 表达式</label>
            <input value={cron} onChange={(e) => setCron(e.target.value)}
              placeholder="0 9 * * *"
              className="w-full bg-[#0a0a0f] border border-[#27272a] rounded-lg px-3 py-2 text-white text-sm font-mono focus:border-indigo-500 outline-none" />
          </div>
        </div>
        <div className="flex flex-wrap gap-2 mb-4">
          {CRON_PRESETS.map((p) => (
            <button key={p.cron} onClick={() => setCron(p.cron)}
              className="px-3 py-1.5 text-xs rounded-full bg-white/5 text-gray-300 hover:bg-indigo-500/20 hover:text-indigo-300 transition-all">
              {p.label}
            </button>
          ))}
        </div>
        <button onClick={schedule} disabled={loading}
          className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-lg text-white text-sm font-medium flex items-center gap-2">
          <Play size={15} /> {loading ? '创建中...' : '创建调度'}
        </button>
      </div>

      {/* 活跃任务 */}
      <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#27272a] mb-6">
        <h3 className="text-lg font-semibold text-white mb-4">活跃调度任务 ({jobs.length})</h3>
        {jobs.length === 0 ? (
          <p className="text-gray-600 text-sm">暂无定时任务</p>
        ) : (
          <div className="space-y-2">
            {jobs.map((job) => (
              <div key={job.id} className="flex items-center justify-between bg-[#0a0a0f] rounded-lg px-4 py-3">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                  <div>
                    <p className="text-sm text-white font-mono">{job.id}</p>
                    <p className="text-xs text-gray-500">下次执行: {job.next_run_time || '—'}</p>
                  </div>
                </div>
                <button onClick={() => unschedule(job.id.toString().replace('workflow_', ''))}
                  className="p-2 text-gray-500 hover:text-red-400">
                  <Trash2 size={15} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 执行历史 */}
      <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#27272a]">
        <h3 className="text-lg font-semibold text-white mb-4">定时执行历史</h3>
        {history.length === 0 ? (
          <p className="text-gray-600 text-sm">暂无执行记录</p>
        ) : (
          <div className="space-y-2">
            {history.map((h) => (
              <div key={h.id} className="flex items-center justify-between bg-[#0a0a0f] rounded-lg px-4 py-2.5">
                <span className="text-sm text-gray-300">工作流 #{h.workflow_id}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  h.status === 'success' ? 'bg-green-500/15 text-green-400' : 'bg-red-500/15 text-red-400'
                }`}>{h.status}</span>
                <span className="text-xs text-gray-600">{h.completed_at || h.started_at}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
