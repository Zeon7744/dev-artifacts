import { useEffect, useState } from 'react'
import { api, useAuthStore } from '../hooks/useAuth'
import { Puzzle, Download, Search, Package, ChevronDown, PlusCircle, ShieldCheck, XCircle, FlaskConical, Send } from 'lucide-react'

const STATUS_LABEL = {
  pending_review: { text: '待审核', cls: 'bg-yellow-500/10 text-yellow-400' },
  approved: { text: '已上架', cls: 'bg-green-500/10 text-green-400' },
  rejected: { text: '已驳回', cls: 'bg-red-500/10 text-red-400' },
}

// 提交表单默认示例代码
const SAMPLE_CODE = `# execute(config, ctx) 为同步函数，运行在安全沙箱（无 import/文件/网络）
def execute(config, ctx):
    values = config.get("values", [1, 2, 3])
    return {"sum": sum(values), "count": len(values)}
`

export default function PluginsPage() {
  const user = useAuthStore((s) => s.user)
  const isAdmin = user?.role === 'admin'
  const [plugins, setPlugins] = useState([])
  const [filter, setFilter] = useState('')
  const [expanded, setExpanded] = useState(null)
  const [msg, setMsg] = useState('')

  // 开发者面板
  const [showDev, setShowDev] = useState(false)
  const [myPlugins, setMyPlugins] = useState([])
  const [form, setForm] = useState({ name: '', node_type: '', description: '', code: SAMPLE_CODE })
  const [testResult, setTestResult] = useState('')

  // 管理员审核
  const [pending, setPending] = useState([])
  const [rejectComment, setRejectComment] = useState({})

  const load = async () => {
    try { const { data } = await api.get('/plugins/'); setPlugins(data || []) } catch (e) {}
  }
  const loadMine = async () => {
    try { const { data } = await api.get('/plugins/custom/mine'); setMyPlugins(data || []) } catch (e) {}
  }
  const loadPending = async () => {
    if (!isAdmin) return
    try { const { data } = await api.get('/plugins/admin/pending'); setPending(data || []) } catch (e) {}
  }

  useEffect(() => { load() }, [])
  useEffect(() => { if (showDev) loadMine() }, [showDev])
  useEffect(() => { loadPending() }, [isAdmin])

  const flash = (t) => { setMsg(t); setTimeout(() => setMsg(''), 3000) }

  const install = async (nodeType) => {
    try {
      await api.post(`/plugins/install/${encodeURIComponent(nodeType)}`)
      flash(`✅ ${nodeType} 已安装`)
      load()
    } catch (e) { flash('❌ 安装失败') }
  }

  const submitPlugin = async () => {
    if (!form.name.trim() || !form.node_type.trim()) return flash('请填写名称和 node_type')
    try {
      const { data } = await api.post('/plugins/custom', {
        name: form.name,
        node_type: form.node_type.startsWith('plugin.') ? form.node_type : `plugin.${form.node_type}`,
        description: form.description,
        code: form.code,
        config_schema: { fields: [] },
      })
      flash(`✅ 提交成功（#${data.id}），可试跑后提交审核`)
      setForm({ name: '', node_type: '', description: '', code: SAMPLE_CODE })
      loadMine()
    } catch (e) { flash(`❌ ${e.response?.data?.detail || '提交失败'}`) }
  }

  const testPlugin = async (p) => {
    try {
      const { data } = await api.post(`/plugins/custom/${p.id}/test`, { config: { values: [1, 2, 3, 4] }, ctx: {} })
      setTestResult(`#${p.id} ` + (data.success ? `✅ 输出: ${JSON.stringify(data.output)}（${data.elapsed_ms}ms）` : `❌ ${data.error}`))
    } catch (e) { setTestResult(`#${p.id} ❌ 试跑失败`) }
  }

  const requestReview = async (p) => {
    try {
      await api.post(`/plugins/custom/${p.id}/publish`)
      flash('📨 已提交审核，等待管理员处理')
      loadMine()
      loadPending()
    } catch (e) { flash('❌ 提交审核失败') }
  }

  const approve = async (p) => {
    try {
      await api.post(`/plugins/admin/${p.id}/approve`, { comment: '审核通过' })
      flash(`✅ 已批准 ${p.node_type}`)
      loadPending(); load(); loadMine()
    } catch (e) { flash('❌ 批准失败') }
  }

  const reject = async (p) => {
    const comment = rejectComment[p.id] || '未通过审核'
    try {
      await api.post(`/plugins/admin/${p.id}/reject`, { comment })
      flash(`已驳回 ${p.node_type}`)
      setRejectComment((s) => ({ ...s, [p.id]: '' }))
      loadPending(); loadMine()
    } catch (e) { flash('❌ 驳回失败') }
  }

  const filtered = plugins.filter((p) =>
    !filter || p.name.toLowerCase().includes(filter.toLowerCase()) || p.description?.toLowerCase().includes(filter.toLowerCase())
  )

  const typeColor = (t) => {
    if (t?.includes('text')) return 'text-blue-400 bg-blue-500/10'
    if (t?.includes('json')) return 'text-purple-400 bg-purple-500/10'
    if (t?.includes('math')) return 'text-orange-400 bg-orange-500/10'
    return 'text-gray-400 bg-white/5'
  }

  return (
    <div className="p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Puzzle className="text-indigo-400" /> 插件市场
          </h1>
          <p className="text-gray-500 mt-1">扩展工作流节点能力，安装后可在可视化编辑器中使用</p>
        </div>
        <button onClick={() => setShowDev(!showDev)}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm transition-all">
          <PlusCircle size={16} /> 开发者中心
        </button>
      </div>

      {msg && <div className="mb-4 px-4 py-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-sm text-indigo-300">{msg}</div>}

      {/* 管理员待审面板 */}
      {isAdmin && pending.length > 0 && (
        <div className="mb-6 bg-[#1a1a2e] rounded-xl border border-yellow-500/30 p-5">
          <h3 className="text-white font-semibold flex items-center gap-2 mb-4">
            <ShieldCheck size={18} className="text-yellow-400" /> 待审核插件（{pending.length}）
          </h3>
          <div className="space-y-3">
            {pending.map((p) => (
              <div key={p.id} className="flex items-start justify-between gap-4 p-3 rounded-lg bg-[#0a0a0f] border border-[#27272a]">
                <div className="min-w-0">
                  <p className="text-sm text-white font-medium">{p.name} <span className="text-xs text-gray-500 font-mono ml-2">{p.node_type}</span></p>
                  <p className="text-xs text-gray-500 mt-0.5">{p.description || '无描述'}</p>
                  <input
                    value={rejectComment[p.id] || ''}
                    onChange={(e) => setRejectComment((s) => ({ ...s, [p.id]: e.target.value }))}
                    placeholder="驳回原因（可选）"
                    className="mt-2 w-full px-3 py-1.5 rounded bg-[#1a1a2e] border border-[#27272a] text-xs text-white outline-none focus:border-yellow-500"
                  />
                </div>
                <div className="flex gap-2 shrink-0">
                  <button onClick={() => approve(p)} className="px-3 py-1.5 rounded-lg bg-green-600 hover:bg-green-500 text-white text-xs flex items-center gap-1">
                    <ShieldCheck size={13} /> 通过
                  </button>
                  <button onClick={() => reject(p)} className="px-3 py-1.5 rounded-lg bg-red-600/80 hover:bg-red-500 text-white text-xs flex items-center gap-1">
                    <XCircle size={13} /> 驳回
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 开发者中心 */}
      {showDev && (
        <div className="mb-6 bg-[#1a1a2e] rounded-xl border border-emerald-500/20 p-5 animate-fade-in">
          <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
            <FlaskConical size={18} className="text-emerald-400" /> 提交自定义插件
          </h3>
          <div className="grid grid-cols-2 gap-3 mb-3">
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="插件名称" className="px-3 py-2 rounded-lg bg-[#0a0a0f] border border-[#27272a] text-sm text-white outline-none focus:border-emerald-500" />
            <input value={form.node_type} onChange={(e) => setForm({ ...form, node_type: e.target.value })}
              placeholder="node_type，如 plugin.my_sms" className="px-3 py-2 rounded-lg bg-[#0a0a0f] border border-[#27272a] text-sm text-white font-mono outline-none focus:border-emerald-500" />
          </div>
          <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
            placeholder="描述（可选）" className="w-full px-3 py-2 rounded-lg bg-[#0a0a0f] border border-[#27272a] text-sm text-white mb-3 outline-none focus:border-emerald-500" />
          <textarea value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })}
            className="w-full px-3 py-2 rounded-lg bg-[#0a0a0f] border border-[#27272a] text-sm text-emerald-300 font-mono h-36 resize-none outline-none focus:border-emerald-500" />
          <div className="flex justify-end mt-3">
            <button onClick={submitPlugin} className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm flex items-center gap-1.5">
              <Send size={14} /> 提交（自动安全校验）
            </button>
          </div>

          {testResult && <div className="mt-3 px-3 py-2 rounded-lg bg-[#0a0a0f] text-xs text-gray-300 font-mono">{testResult}</div>}

          {myPlugins.length > 0 && (
            <div className="mt-5 border-t border-[#27272a] pt-4">
              <p className="text-sm text-gray-400 mb-3">我的插件</p>
              <div className="space-y-2">
                {myPlugins.map((p) => {
                  const st = STATUS_LABEL[p.review_status] || STATUS_LABEL.pending_review
                  return (
                    <div key={p.id} className="flex items-center justify-between p-3 rounded-lg bg-[#0a0a0f] border border-[#27272a]">
                      <div className="min-w-0">
                        <p className="text-sm text-white">
                          {p.name}
                          <span className={`ml-2 text-xs px-2 py-0.5 rounded-full ${st.cls}`}>{st.text}</span>
                        </p>
                        <p className="text-xs text-gray-500 font-mono mt-0.5">{p.node_type}</p>
                        {p.review_status === 'rejected' && p.review_comment && (
                          <p className="text-xs text-red-400 mt-1">驳回原因：{p.review_comment}</p>
                        )}
                      </div>
                      <div className="flex gap-2 shrink-0">
                        <button onClick={() => testPlugin(p)} className="px-2.5 py-1.5 rounded-lg bg-white/5 text-gray-300 text-xs hover:bg-white/10 flex items-center gap-1">
                          <FlaskConical size={12} /> 试跑
                        </button>
                        {!p.is_published && (
                          <button onClick={() => requestReview(p)} className="px-2.5 py-1.5 rounded-lg bg-emerald-600/80 hover:bg-emerald-500 text-white text-xs flex items-center gap-1">
                            <Send size={12} /> {p.review_status === 'rejected' ? '重新提交' : '提交审核'}
                          </button>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="relative mb-6 max-w-md">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
        <input value={filter} onChange={(e) => setFilter(e.target.value)}
          placeholder="搜索插件..."
          className="w-full bg-[#1a1a2e] border border-[#27272a] rounded-lg pl-10 pr-4 py-2.5 text-sm text-white outline-none focus:border-indigo-500" />
      </div>

      <div className="grid grid-cols-2 gap-4">
        {filtered.map((p) => (
          <div key={p.node_type} className="bg-[#1a1a2e] rounded-xl border border-[#27272a] hover:border-indigo-500/30 transition-all overflow-hidden">
            <div className="p-5">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${typeColor(p.node_type)}`}>
                    <Package size={18} />
                  </div>
                  <div>
                    <h3 className="text-white font-semibold">{p.name}</h3>
                    <p className="text-xs text-gray-500 font-mono">{p.node_type} · v{p.version}</p>
                  </div>
                </div>
                {p.is_builtin ? (
                  <span className="text-xs px-2 py-1 rounded-full bg-green-500/10 text-green-400">内置</span>
                ) : (
                  <button onClick={() => install(p.node_type)}
                    className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white">
                    <Download size={13} /> {p.install_count > 0 ? `${p.install_count} 已装` : '安装'}
                  </button>
                )}
              </div>
              <p className="text-sm text-gray-400">{p.description}</p>
              {p.config_schema && (
                <button onClick={() => setExpanded(expanded === p.node_type ? null : p.node_type)}
                  className="mt-3 text-xs text-indigo-400 flex items-center gap-1">
                  <ChevronDown size={14} className={`transition-transform ${expanded === p.node_type ? 'rotate-180' : ''}`} />
                  配置项
                </button>
              )}
            </div>
            {expanded === p.node_type && p.config_schema && (
              <div className="px-5 pb-4 border-t border-[#27272a] pt-3">
                <pre className="text-xs text-gray-500 font-mono whitespace-pre-wrap">{JSON.stringify(p.config_schema, null, 2)}</pre>
              </div>
            )}
          </div>
        ))}
        {filtered.length === 0 && (
          <div className="col-span-2 text-center text-gray-600 py-12">
            <Puzzle size={40} className="mx-auto mb-3 opacity-30" />
            没有匹配的插件
          </div>
        )}
      </div>
    </div>
  )
}
