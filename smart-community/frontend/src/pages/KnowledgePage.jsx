import { useEffect, useState } from 'react'
import { api } from '../hooks/useAuth'
import { BookOpen, Plus, Search, FileText, Database, Loader2 } from 'lucide-react'

export default function KnowledgePage() {
  const [kbs, setKbs] = useState([])
  const [selectedKb, setSelectedKb] = useState(null)
  const [docs, setDocs] = useState([])
  const [kbName, setKbName] = useState('')
  const [docTitle, setDocTitle] = useState('')
  const [docContent, setDocContent] = useState('')
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState(null)
  const [busy, setBusy] = useState('')

  const loadKbs = async () => {
    try { const { data } = await api.get('/rag/kb'); setKbs(data || []) } catch (e) {}
  }
  useEffect(() => { loadKbs() }, [])

  const createKb = async () => {
    if (!kbName.trim()) return
    setBusy('kb')
    try {
      const { data } = await api.post('/rag/kb', { name: kbName, description: '' })
      setKbName('')
      await loadKbs()
      selectKb(data.id)
    } finally { setBusy('') }
  }

  const selectKb = async (id) => {
    setSelectedKb(id); setAnswer(null)
    try { const { data } = await api.get(`/rag/kb/${id}/docs`); setDocs(data || []) } catch (e) { setDocs([]) }
  }

  const uploadDoc = async () => {
    if (!docTitle.trim() || !docContent.trim() || !selectedKb) return
    setBusy('doc')
    try {
      await api.post(`/rag/kb/${selectedKb}/docs`, { title: docTitle, content: docContent })
      setDocTitle(''); setDocContent('')
      selectKb(selectedKb); loadKbs()
    } finally { setBusy('') }
  }

  const ask = async () => {
    if (!question.trim() || !selectedKb) return
    setBusy('ask'); setAnswer(null)
    try {
      const { data } = await api.post(`/rag/kb/${selectedKb}/query`, { question, top_k: 4 })
      setAnswer(data)
    } catch (e) {
      setAnswer({ answer: '查询失败：' + (e.response?.data?.detail || e.message), sources: [] })
    } finally { setBusy('') }
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <BookOpen className="text-indigo-400" /> 知识库 (RAG)
        </h1>
        <p className="text-gray-500 mt-1">上传文档构建专属知识库，向量检索 + AI 问答</p>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* 知识库列表 */}
        <div className="bg-[#1a1a2e] rounded-xl p-5 border border-[#27272a]">
          <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
            <Database size={16} className="text-purple-400" /> 知识库
          </h3>
          <div className="flex gap-2 mb-4">
            <input value={kbName} onChange={(e) => setKbName(e.target.value)}
              placeholder="新知识库名称"
              className="flex-1 bg-[#0a0a0f] border border-[#27272a] rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-indigo-500" />
            <button onClick={createKb} disabled={busy === 'kb'}
              className="px-3 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-white">
              {busy === 'kb' ? <Loader2 size={16} className="animate-spin" /> : <Plus size={16} />}
            </button>
          </div>
          <div className="space-y-2">
            {kbs.map((kb) => (
              <button key={kb.id} onClick={() => selectKb(kb.id)}
                className={`w-full text-left px-3 py-2.5 rounded-lg border transition-all ${
                  selectedKb === kb.id ? 'bg-indigo-500/15 border-indigo-500/40 text-indigo-300' : 'bg-[#0a0a0f] border-[#27272a] text-gray-300 hover:border-gray-600'
                }`}>
                <p className="text-sm font-medium">{kb.name}</p>
                <p className="text-xs text-gray-500 mt-0.5">{kb.doc_count || 0} 文档 · {kb.chunk_count || 0} 片段</p>
              </button>
            ))}
            {kbs.length === 0 && <p className="text-gray-600 text-sm text-center py-4">还没有知识库</p>}
          </div>
        </div>

        {/* 文档上传 */}
        <div className="bg-[#1a1a2e] rounded-xl p-5 border border-[#27272a]">
          <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
            <FileText size={16} className="text-blue-400" /> 文档
          </h3>
          {selectedKb ? (
            <>
              <input value={docTitle} onChange={(e) => setDocTitle(e.target.value)}
                placeholder="文档标题"
                className="w-full bg-[#0a0a0f] border border-[#27272a] rounded-lg px-3 py-2 text-sm text-white mb-2 outline-none focus:border-indigo-500" />
              <textarea value={docContent} onChange={(e) => setDocContent(e.target.value)}
                placeholder="粘贴文档内容..." rows={6}
                className="w-full bg-[#0a0a0f] border border-[#27272a] rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-indigo-500 resize-none" />
              <button onClick={uploadDoc} disabled={busy === 'doc'}
                className="mt-3 w-full py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg text-white text-sm flex items-center justify-center gap-2">
                {busy === 'doc' ? <Loader2 size={15} className="animate-spin" /> : <Plus size={15} />} 上传并索引
              </button>
              <div className="mt-4 space-y-1.5">
                {docs.map((d) => (
                  <div key={d.id} className="flex items-center justify-between text-xs bg-[#0a0a0f] rounded px-3 py-2">
                    <span className="text-gray-300 truncate">{d.title}</span>
                    <span className={`shrink-0 ml-2 ${d.status === 'ready' ? 'text-green-400' : 'text-yellow-400'}`}>{d.status}</span>
                  </div>
                ))}
              </div>
            </>
          ) : <p className="text-gray-600 text-sm text-center py-8">← 先选择一个知识库</p>}
        </div>

        {/* 问答 */}
        <div className="bg-[#1a1a2e] rounded-xl p-5 border border-[#27272a]">
          <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
            <Search size={16} className="text-green-400" /> 智能问答
          </h3>
          <textarea value={question} onChange={(e) => setQuestion(e.target.value)}
            placeholder="基于知识库内容提问..." rows={3}
            className="w-full bg-[#0a0a0f] border border-[#27272a] rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-indigo-500 resize-none" />
          <button onClick={ask} disabled={busy === 'ask' || !selectedKb}
            className="mt-3 w-full py-2 bg-green-600 hover:bg-green-500 disabled:opacity-50 rounded-lg text-white text-sm flex items-center justify-center gap-2">
            {busy === 'ask' ? <Loader2 size={15} className="animate-spin" /> : <Search size={15} />} 检索并回答
          </button>
          {answer && (
            <div className="mt-4">
              <div className="bg-[#0a0a0f] rounded-lg p-3 text-sm text-gray-200 leading-relaxed max-h-48 overflow-auto">
                {answer.answer}
              </div>
              {answer.sources?.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs text-gray-500 mb-1.5">引用来源 ({answer.sources.length})</p>
                  {answer.sources.map((s, i) => (
                    <div key={i} className="text-xs bg-[#0a0a0f] rounded px-3 py-2 mb-1.5 text-gray-400">
                      <span className="text-indigo-400">{s.title || `片段${s.chunk_id}`}</span>
                      <span className="float-right text-gray-600">{(s.score * 100).toFixed(0)}%</span>
                      <p className="mt-1 text-gray-500 line-clamp-2">{s.content}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
