import { useEffect, useState } from 'react'
import { api } from '../hooks/useAuth'
import { Bot, Star, MessageCircle } from 'lucide-react'

export default function AgentsPage() {
  const [agents, setAgents] = useState([])
  const [chatAgent, setChatAgent] = useState(null)
  const [message, setMessage] = useState('')
  const [response, setResponse] = useState('')

  useEffect(() => {
    api.get('/agents/').then(({ data }) => setAgents(data)).catch(() => setAgents([]))
  }, [])

  const handleChat = async () => {
    if (!message.trim() || !chatAgent) return
    try {
      const { data } = await api.post('/agents/chat', { agent_id: chatAgent.id, message })
      setResponse(data.response)
    } catch { setResponse('Agent 暂时不可用') }
    setMessage('')
  }

  return (
    <div className="p-8 animate-fade-in">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Agent 市场</h1>
        <p className="text-gray-500 mt-1">发现和使用AI智能体</p>
      </div>

      <div className="grid grid-cols-3 gap-6 mb-8">
        {agents.map((agent) => (
          <div key={agent.id} className="bg-[#1a1a2e] rounded-xl p-6 border border-[#27272a] hover:border-purple-500/30 transition-all">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                <Bot size={20} className="text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-white">{agent.name}</h3>
                <p className="text-xs text-gray-500">{agent.agent_type}</p>
              </div>
            </div>
            <p className="text-sm text-gray-400 mb-4">{agent.description || '智能助手'}</p>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1 text-xs text-yellow-400">
                <Star size={12} /> {agent.rating || '0.0'}
              </div>
              <button onClick={() => setChatAgent(agent)} className="px-3 py-1 rounded-lg bg-purple-500/10 text-purple-400 text-xs hover:bg-purple-500/20 transition-all">
                对话
              </button>
            </div>
          </div>
        ))}
        {agents.length === 0 && (
          <div className="col-span-3 text-center py-16 text-gray-500">
            <Bot size={48} className="mx-auto mb-4 opacity-30" />
            <p>暂无已发布的Agent</p>
          </div>
        )}
      </div>

      {/* 对话面板 */}
      {chatAgent && (
        <div className="bg-[#1a1a2e] rounded-xl p-6 border border-purple-500/20 animate-fade-in">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-white font-semibold">与 {chatAgent.name} 对话</h3>
            <button onClick={() => { setChatAgent(null); setResponse('') }} className="text-gray-500 hover:text-white">×</button>
          </div>
          {response && <div className="mb-4 p-4 rounded-lg bg-[#0a0a0f] text-gray-300 text-sm whitespace-pre-wrap">{response}</div>}
          <div className="flex gap-3">
            <input value={message} onChange={(e) => setMessage(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleChat()} className="flex-1 px-4 py-2 rounded-lg bg-[#0a0a0f] border border-[#27272a] text-white text-sm focus:border-purple-500 focus:outline-none" placeholder="输入消息..." />
            <button onClick={handleChat} className="px-4 py-2 rounded-lg bg-purple-500 hover:bg-purple-600 text-white text-sm">发送</button>
          </div>
        </div>
      )}
    </div>
  )
}
