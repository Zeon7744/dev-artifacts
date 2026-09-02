import { useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import ReactFlow, { addEdge, useNodesState, useEdgesState, Controls, Background, MiniMap } from 'reactflow'
import 'reactflow/dist/style.css'
import { api } from '../hooks/useAuth'
import { Play, Save, Plus, Trash2 } from 'lucide-react'

const nodeTypes = {
  trigger: { label: '触发器', color: 'border-green-500', icon: '⚡' },
  action: { label: '动作', color: 'border-blue-500', icon: '⚙️' },
  condition: { label: '条件', color: 'border-yellow-500', icon: '🔀' },
  ai: { label: 'AI处理', color: 'border-purple-500', icon: '🤖' },
  transform: { label: '数据转换', color: 'border-cyan-500', icon: '🔄' },
  notify: { label: '通知', color: 'border-orange-500', icon: '🔔' },
}

let id = 0
const getId = () => `node_${id++}`

const initialNodes = [
  { id: 'node_0', type: 'input', position: { x: 250, y: 50 }, data: { label: '⚡ 触发器' }, className: 'workflow-node border-green-500' },
]

export default function WorkflowBuilderPage() {
  const { id: workflowId } = useParams()
  const navigate = useNavigate()
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [name, setName] = useState('新工作流')
  const [saving, setSaving] = useState(false)

  const onConnect = useCallback((params) => setEdges((eds) => addEdge({ ...params, animated: true, style: { stroke: '#6366f1' } }, eds)), [])

  const addNode = (type) => {
    const info = nodeTypes[type]
    const newNode = {
      id: getId(),
      position: { x: Math.random() * 400 + 100, y: Math.random() * 300 + 100 },
      data: { label: `${info.icon} ${info.label}` },
      className: `workflow-node ${info.color}`,
    }
    setNodes((nds) => [...nds, newNode])
  }

  const handleSave = async () => {
    setSaving(true)
    const definition = {
      nodes: nodes.map((n) => ({ id: n.id, type: n.data.label?.includes('触发') ? 'trigger' : n.data.label?.includes('AI') ? 'ai' : n.data.label?.includes('条件') ? 'condition' : 'action', config: {} })),
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
        <div className="w-48 bg-[#12121a] border-r border-[#27272a] p-4 space-y-2">
          <p className="text-xs text-gray-500 mb-3 uppercase tracking-wider">节点类型</p>
          {Object.entries(nodeTypes).map(([type, info]) => (
            <button key={type} onClick={() => addNode(type)} className="w-full flex items-center gap-2 px-3 py-2 rounded-lg bg-[#1a1a2e] border border-[#27272a] hover:border-indigo-500/50 text-sm text-gray-300 transition-all">
              <span>{info.icon}</span> {info.label}
            </button>
          ))}
        </div>

        {/* 画布 */}
        <div className="flex-1">
          <ReactFlow nodes={nodes} edges={edges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} onConnect={onConnect} fitView>
            <Controls className="!bg-[#1a1a2e] !border-[#27272a]" />
            <Background color="#27272a" gap={20} />
            <MiniMap className="!bg-[#12121a]" nodeColor="#6366f1" />
          </ReactFlow>
        </div>
      </div>
    </div>
  )
}
