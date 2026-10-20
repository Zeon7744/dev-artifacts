import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../hooks/useAuth'
import { Plus, Play, Clock, GitBranch } from 'lucide-react'

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState([])
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/workflows/').then(({ data }) => setWorkflows(data)).catch(() => {})
  }, [])

  return (
    <div className="p-8 animate-fade-in">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">工作流</h1>
          <p className="text-gray-500 mt-1">自动化流程编排与执行</p>
        </div>
        <button onClick={() => navigate('/workflows/new')} className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-500 hover:bg-indigo-600 text-white transition-all">
          <Plus size={18} /> 新建工作流
        </button>
      </div>

      {workflows.length === 0 ? (
        <div className="bg-[#1a1a2e] rounded-xl p-16 border border-[#27272a] text-center">
          <GitBranch size={48} className="mx-auto text-gray-600 mb-4" />
          <h3 className="text-lg text-gray-400 mb-2">还没有工作流</h3>
          <p className="text-gray-600 mb-6">创建一个自动化工作流，让AI帮你完成任务</p>
          <button onClick={() => navigate('/workflows/new')} className="px-6 py-2 rounded-lg bg-indigo-500 hover:bg-indigo-600 text-white">
            开始创建
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-6">
          {workflows.map((wf) => (
            <div key={wf.id} className="bg-[#1a1a2e] rounded-xl p-6 border border-[#27272a] hover:border-indigo-500/30 transition-all cursor-pointer" onClick={() => navigate(`/workflows/${wf.id}`)}>
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-semibold text-white">{wf.name}</h3>
                <span className={`px-2 py-1 rounded text-xs ${wf.status === 'active' ? 'bg-green-500/10 text-green-400' : 'bg-gray-500/10 text-gray-400'}`}>
                  {wf.status}
                </span>
              </div>
              <p className="text-sm text-gray-500 mb-4">{wf.description || '暂无描述'}</p>
              <div className="flex items-center gap-4 text-xs text-gray-600">
                <span className="flex items-center gap-1"><Clock size={12} /> 运行 {wf.run_count} 次</span>
                {wf.tags?.map((t) => <span key={t} className="px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400">{t}</span>)}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
