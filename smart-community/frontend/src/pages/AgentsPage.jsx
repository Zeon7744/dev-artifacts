import { useEffect, useRef, useState } from 'react'
import { api } from '../hooks/useAuth'
import { Bot, Star, MessageCircle, X, Send } from 'lucide-react'

export default function AgentsPage() {
  const [agents, setAgents] = useState([])
  const [chatAgent, setChatAgent] = useState(null)
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState([]) // {role: 'user'|'agent', text}
  const [streaming, setStreaming] = useState(false)
  const bodyRef = useRef(null)

  useEffect(() => {
    api.get('/agents/').then(({ data }) => setAgents(data)).catch(() => setAgents([]))
  }, [])

  useEffect(() => {
    bodyRef.current?.scrollTo({ top: bodyRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  const openChat = (agent) => {
    setChatAgent(agent)
    setMessages([])
    setInput('')
  }

  // SSE 流式对话：用 fetch 读取 text/event-stream（EventSource 不支持 POST/Authorization 头）
  const handleSend = async () => {
    const text = input.trim()
    if (!text || !chatAgent || streaming) return
    setInput('')
    setStreaming(true)
    setMessages((m) => [...m, { role: 'user', text }])
    // 先放一条空的 agent 消息，token 到达时增量追加
    setMessages((m) => [...m, { role: 'agent', text: '' }])

    const appendAgent = (chunk) => {
      setMessages((m) => {
        const copy = [...m]
        const last = copy[copy.length - 1]
        if (last && last.role === 'agent') copy[copy.length - 1] = { ...last, text: last.text + chunk }
        return copy
      })
    }

    try {
      const token = localStorage.getItem('token')
      const resp = await fetch('/api/agents/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ agent_id: chatAgent.id, message: text }),
      })
      if (!resp.ok || !resp.body) throw new Error(`stream ${resp.status}`)

      const reader = resp.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const frames = buffer.split('\n\n')
        buffer = frames.pop() || ''
        for (const frame of frames) {
          const lines = frame.split('\n')
          const eventLine = lines.find((l) => l.startsWith('event:'))
          const dataLine = lines.find((l) => l.startsWith('data:'))
          if (!eventLine || !dataLine) continue
          const event = eventLine.slice(6).trim()
          try {
            const data = JSON.parse(dataLine.slice(5).trim())
            if (event === 'token' && data.text) appendAgent(data.text)
          } catch {
            // 忽略不完整帧
          }
        }
      }
    } catch {
      appendAgent('（流式连接失败，请稍后重试）')
    } finally {
      setStreaming(false)
    }
  }

  return (
    <div className="p-8 animate-fade-in">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Agent 市场</h1>
        <p className="text-gray-500 mt-1">发现和使用AI智能体 · 流式实时对话</p>
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
              <button onClick={() => openChat(agent)} className="px-3 py-1 rounded-lg bg-purple-500/10 text-purple-400 text-xs hover:bg-purple-500/20 transition-all">
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

      {/* 流式对话面板 */}
      {chatAgent && (
        <div className="bg-[#1a1a2e] rounded-xl border border-purple-500/20 animate-fade-in overflow-hidden">
          <div className="flex justify-between items-center px-6 py-4 border-b border-[#27272a]">
            <h3 className="text-white font-semibold flex items-center gap-2">
              <MessageCircle size={16} className="text-purple-400" /> 与 {chatAgent.name} 对话
              <span className="text-xs text-gray-500 font-normal">SSE 流式输出</span>
            </h3>
            <button onClick={() => { setChatAgent(null); setMessages([]) }} className="text-gray-500 hover:text-white">
              <X size={18} />
            </button>
          </div>

          <div ref={bodyRef} className="px-6 py-4 space-y-3 max-h-96 overflow-y-auto">
            {messages.length === 0 && (
              <p className="text-sm text-gray-600 text-center py-6">开始对话吧，回复会逐字实时显示～</p>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[75%] px-4 py-2.5 rounded-lg text-sm whitespace-pre-wrap ${
                  m.role === 'user'
                    ? 'bg-purple-600 text-white rounded-br-none'
                    : 'bg-[#0a0a0f] text-gray-300 border border-[#27272a] rounded-bl-none'
                }`}>
                  {m.text}
                  {m.role === 'agent' && streaming && i === messages.length - 1 && (
                    <span className="inline-block w-1.5 h-4 ml-1 bg-purple-400 animate-pulse align-middle" />
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="flex gap-3 px-6 py-4 border-t border-[#27272a]">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              disabled={streaming}
              className="flex-1 px-4 py-2 rounded-lg bg-[#0a0a0f] border border-[#27272a] text-white text-sm focus:border-purple-500 focus:outline-none disabled:opacity-50"
              placeholder={streaming ? 'AI 正在回复...' : '输入消息...'}
            />
            <button onClick={handleSend} disabled={streaming || !input.trim()}
              className="px-4 py-2 rounded-lg bg-purple-500 hover:bg-purple-600 text-white text-sm flex items-center gap-1.5 disabled:opacity-40">
              <Send size={14} /> 发送
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
