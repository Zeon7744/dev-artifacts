import { useEffect, useState } from 'react'
import { api } from '../hooks/useAuth'
import { Puzzle, Download, Search, Package, ChevronDown } from 'lucide-react'

export default function PluginsPage() {
  const [plugins, setPlugins] = useState([])
  const [filter, setFilter] = useState('')
  const [expanded, setExpanded] = useState(null)
  const [msg, setMsg] = useState('')

  const load = async () => {
    try { const { data } = await api.get('/plugins/'); setPlugins(data || []) } catch (e) {}
  }
  useEffect(() => { load() }, [])

  const install = async (nodeType) => {
    try {
      await api.post(`/plugins/install/${encodeURIComponent(nodeType)}`)
      setMsg(`✅ ${nodeType} 已安装`)
      load()
      setTimeout(() => setMsg(''), 2500)
    } catch (e) { setMsg('❌ 安装失败') }
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
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Puzzle className="text-indigo-400" /> 插件市场
        </h1>
        <p className="text-gray-500 mt-1">扩展工作流节点能力，安装后可在可视化编辑器中使用</p>
      </div>

      {msg && <div className="mb-4 px-4 py-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-sm text-indigo-300">{msg}</div>}

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
