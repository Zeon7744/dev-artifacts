import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import ReactFlow, { addEdge, useNodesState, useEdgesState, Controls, Background, MiniMap } from 'reactflow'
import 'reactflow/dist/style.css'
import { api } from '../hooks/useAuth'
import { Play, Save, Plus, Trash2, Puzzle } from 'lucide-react'

const nodeTypes = {
  trigger: { label: '触发器', color: 'border-green-500', icon: '⚡' },
  action: { label: '动作', color: 'border-blue-500', icon: '⚙️' },
  condition: { label: '条件', color: 'border-yellow-500', icon: '🔀' },
  ai: { label: 'AI处理', color: 'border-purple-500', icon: '🤖' },
  transform: { label: '数据转换', color: 'border-cyan-500', icon: '🔄' },
  notify: { label: '通知', color: 'border-orange-500', icon: '🔔' },
}

const PLUGIN_PREFIX = 'plugin.'

let id = 1
const getId = () => `node_${id++}`

const initialNodes = [
  { id: 'node_0', type: 'input', position: { x: 250, y: 50 }, data: { label: '⚡ 触发器', nodeType: 'trigger', config: {} }, className: 'workflow-node border-green-500' },
]

// 根据插件 config_schema 生成默认配置
const buildDefaultConfig = (schema) => {
  const config = {}
  for (const field of schema?.fields || []) {
    if (field.default !== undefined) {
      config[field.key] = field.default
    } else if (field.type === 'checkbox') {
      config[field.key] = false
    } else if (field.type === 'number') {
      config[field.key] = ''
    } else {
      config[field.key] = ''
    }
  }
  return config
}

// options 支持 [{label, value}] 或纯字符串数组
const normalizeOptions = (options) =>
  (options || []).map((o) => (typeof o === 'string' ? { label: o, value: o } : { label: o.label ?? o.value, value: o.value }))

export default function WorkflowBuilderPage() {
  const { id: workflowId } = useParams()
  const navigate = useNavigate()
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [name, setName] = useState('新工作流')
  const [saving, setSaving] = useState(false)
  const [plugins, setPlugins] = useState([])

  // 拉取插件市场节点；失败时静默降级（插件分组不显示）
  useEffect(() => {
    api.get('/plugins/')
      .then(({ data }) => setPlugins(Array.isArray(data) ? data : []))
      .catch(() => {})
  }, [])

  const onConnect = useCallback((params) => setEdges((eds) => addEdge({ ...params, animated: true, style: { stroke: '#6366f1' } }, eds)), [])

  const addNode = (type) => {
    const info = nodeTypes[type]
    const newNode = {
      id: getId(),
      position: { x: Math.random() * 400 + 100, y: Math.random() * 300 + 100 },
      data: { label: `${info.icon} ${info.label}`, nodeType: type, config: {} },
      className: `workflow-node ${info.color}`,
    }
    setNodes((nds) => [...nds, newNode])
  }

  const addPluginNode = (plugin) => {
    const schema = plugin.config_schema || {}
    const newNode = {
      id: getId(),
      position: { x: Math.random() * 400 + 100, y: Math.random() * 300 + 100 },
      data: {
        // 画布卡片显示插件名而非原始 node_type
        label: (
          <div className="text-left">
            <div className="font-medium text-gray-100">🧩 {plugin.name}</div>
            <div className="text-[10px] text-emerald-400/70 font-mono mt-0.5">{plugin.node_type}</div>
          </div>
        ),
        nodeType: plugin.node_type,
        pluginName: plugin.name,
        config: buildDefaultConfig(schema),
        configSchema: schema,
      },
      className: 'workflow-node border-emerald-500',
    }
    setNodes((nds) => [...nds, newNode])
  }

  const updateNodeConfig = (nodeId, key, value) => {
    setNodes((nds) =>
      nds.map((n) =>
        n.id === nodeId ? { ...n, data: { ...n.data, config: { ...(n.data.config || {}), [key]: value } } } : n
      )
    )
  }

  const deleteNode = (nodeId) => {
    setNodes((nds) => nds.filter((n) => n.id !== nodeId))
    setEdges((eds) => eds.filter((e) => e.source !== nodeId && e.target !== nodeId))
  }

  const selectedNode = nodes.find((n) => n.selected)
  const selectedIsPlugin = selectedNode?.data?.nodeType?.startsWith(PLUGIN_PREFIX)
  const selectedSchema =
    selectedNode?.data?.configSchema ||
    plugins.find((p) => p.node_type === selectedNode?.data?.nodeType)?.config_schema ||
    null

  // 插件节点缺少 schema 时（如历史数据）按需拉取，失败静默
  useEffect(() => {
    const sel = nodes.find((n) => n.selected)
    if (sel && sel.data?.nodeType?.startsWith(PLUGIN_PREFIX) && !sel.data.configSchema) {
      api
        .get(`/plugins/${encodeURIComponent(sel.data.nodeType)}/schema`)
        .then(({ data }) => {
          setNodes((nds) =>
            nds.map((n) =>
              n.id === sel.id
                ? { ...n, data: { ...n.data, configSchema: data.config_schema || {}, pluginName: data.name || n.data.pluginName } }
                : n
            )
          )
        })
        .catch(() => {})
    }
  }, [nodes, setNodes])

  const renderConfigField = (node, field) => {
    const value = node.data.config?.[field.key]
    const setVal = (v) => updateNodeConfig(node.id, field.key, v)
    const labelEl = (
      <label className="block text-xs text-gray-400 mb-1">
        {field.label}
        {field.required && <span className="text-red-400 ml-0.5">*</span>}
      </label>
    )
    const inputCls =
      'w-full px-3 py-2 rounded-lg bg-[#1a1a2e] border border-[#27272a] text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-emerald-500/60 transition-all'

    let control = null
    switch (field.type) {
      case 'textarea':
        control = (
          <textarea
            rows={3}
            className={inputCls + ' resize-y'}
            value={value ?? ''}
            placeholder={field.placeholder}
            onChange={(e) => setVal(e.target.value)}
          />
        )
        break
      case 'select':
        control = (
          <select className={inputCls} value={value ?? ''} onChange={(e) => setVal(e.target.value)}>
            {normalizeOptions(field.options).map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        )
        break
      case 'number':
        control = (
          <input
            type="number"
            className={inputCls}
            value={value ?? ''}
            placeholder={field.placeholder}
            onChange={(e) => {
              const v = e.target.value
              setVal(v === '' ? '' : Number.isNaN(Number(v)) ? v : Number(v))
            }}
          />
        )
        break
      case 'checkbox':
        control = (
          <button
            type="button"
            onClick={() => setVal(!value)}
            className={`w-10 h-5 rounded-full transition-colors relative ${value ? 'bg-emerald-500' : 'bg-[#27272a]'}`}
          >
            <span className={`absolute top-0.5 h-4 w-4 rounded-full bg-white transition-all ${value ? 'left-[22px]' : 'left-0.5'}`} />
          </button>
        )
        break
      case 'text':
      default:
        control = (
          <input
            type="text"
            className={inputCls}
            value={value ?? ''}
            placeholder={field.placeholder}
            onChange={(e) => setVal(e.target.value)}
          />
        )
    }

    return (
      <div key={field.key}>
        {labelEl}
        {control}
        {field.help && <p className="text-[11px] text-gray-500 mt-1 leading-relaxed">{field.help}</p>}
      </div>
    )
  }

  const handleSave = async () => {
    setSaving(true)
    const definition = {
      nodes: nodes.map((n) => ({
        id: n.id,
        type: n.data.nodeType || (n.data.label?.includes?.('触发') ? 'trigger' : 'action'),
        config: n.data.config || {},
      })),
      edges: edges.map((e) => ({ from: e.source, to: e.target })),
    }
    try {
      if (workflowId && workflowId !== 'new') {
        await api.put(`/workflows/${workflowId}`, { name, definition })
      } else {
        await api.post('/workflows/', { name, definition })
      }
      navigate('/workflows')
    } catch (err) {
      console.error(err)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="h-screen flex flex-col bg-[#0a0a0f]">
      {/* 顶部工具栏 */}
      <div className="h-14 bg-[#12121a] border-b border-[#27272a] flex items-center justify-between px-6">
        <input value={name} onChange={(e) => setName(e.target.value)} className="bg-transparent text-white text-lg font-semibold focus:outline-none border-b border-transparent focus:border-indigo-500" />
        <div className="flex items-center gap-3">
          <button onClick={handleSave} disabled={saving} className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-500 hover:bg-indigo-600 text-white text-sm transition-all disabled:opacity-50">
            <Save size={16} /> {saving ? '保存中...' : '保存'}
          </button>
        </div>
      </div>

      <div className="flex-1 flex">
        {/* 节点面板 */}
        <div className="w-48 bg-[#12121a] border-r border-[#27272a] p-4 space-y-2 overflow-y-auto">
          <p className="text-xs text-gray-500 mb-3 uppercase tracking-wider">节点类型</p>
          {Object.entries(nodeTypes).map(([type, info]) => (
            <button key={type} onClick={() => addNode(type)} className="w-full flex items-center gap-2 px-3 py-2 rounded-lg bg-[#1a1a2e] border border-[#27272a] hover:border-indigo-500/50 text-sm text-gray-300 transition-all">
              <span>{info.icon}</span> {info.label}
            </button>
          ))}

          {/* 插件市场节点（拉取失败时不显示） */}
          {plugins.length > 0 && (
            <div className="pt-2 mt-2 border-t border-[#27272a]">
              <p className="text-xs text-gray-500 mb-2 uppercase tracking-wider flex items-center gap-1">
                <Puzzle size={12} className="text-emerald-400" /> 插件节点
              </p>
              <div className="space-y-2">
                {plugins.map((p) => (
                  <button
                    key={p.node_type}
                    title={p.description || p.name}
                    onClick={() => addPluginNode(p)}
                    className="w-full px-3 py-2 rounded-lg bg-[#1a1a2e] border border-emerald-500/30 hover:border-emerald-500/60 text-left transition-all"
                  >
                    <span className="flex items-center gap-2 text-sm text-gray-300">
                      <Puzzle size={14} className="text-emerald-400 shrink-0" />
                      <span className="truncate">{p.name}</span>
                    </span>
                    <span className="block text-[10px] text-gray-500 font-mono truncate pl-6 mt-0.5">{p.node_type}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 画布 */}
        <div className="flex-1">
          <ReactFlow nodes={nodes} edges={edges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} onConnect={onConnect} fitView>
            <Controls className="!bg-[#1a1a2e] !border-[#27272a]" />
            <Background color="#27272a" gap={20} />
            <MiniMap className="!bg-[#12121a]" nodeColor={(n) => (n.data?.nodeType?.startsWith(PLUGIN_PREFIX) ? '#10b981' : '#6366f1')} />
          </ReactFlow>
        </div>

        {/* 节点配置面板 */}
        {selectedNode && (
          <div className="w-72 bg-[#12121a] border-l border-[#27272a] p-4 overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <p className="text-xs text-gray-500 uppercase tracking-wider">节点配置</p>
              <button onClick={() => deleteNode(selectedNode.id)} title="删除节点" className="p-1.5 rounded-lg text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-all">
                <Trash2 size={14} />
              </button>
            </div>

            {selectedIsPlugin ? (
              <>
                <div className="mb-4 px-3 py-2 rounded-lg bg-[#1a1a2e] border border-emerald-500/30">
                  <p className="text-sm text-gray-200 flex items-center gap-1.5">
                    <Puzzle size={14} className="text-emerald-400 shrink-0" />
                    <span className="truncate">{selectedNode.data.pluginName || '插件节点'}</span>
                  </p>
                  <p className="text-[10px] text-gray-500 font-mono mt-0.5 truncate">{selectedNode.data.nodeType}</p>
                </div>
                {selectedSchema?.fields?.length ? (
                  <div className="space-y-3">{selectedSchema.fields.map((field) => renderConfigField(selectedNode, field))}</div>
                ) : (
                  <p className="text-xs text-gray-500">该插件暂无可配置项</p>
                )}
              </>
            ) : (
              <div className="px-3 py-2 rounded-lg bg-[#1a1a2e] border border-[#27272a]">
                <p className="text-sm text-gray-300">{selectedNode.data.label}</p>
                <p className="text-[11px] text-gray-500 mt-1">内置节点，暂无需额外配置</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
