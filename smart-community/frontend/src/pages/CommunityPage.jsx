import { useEffect, useState } from 'react'
import { api } from '../hooks/useAuth'
import { MessageSquare, Heart, Eye, Plus } from 'lucide-react'

export default function CommunityPage() {
  const [posts, setPosts] = useState([])
  const [showCreate, setShowCreate] = useState(false)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')

  useEffect(() => {
    api.get('/community/posts').then(({ data }) => setPosts(data)).catch(() => setPosts([]))
  }, [])

  const handleCreate = async () => {
    if (!title.trim() || !content.trim()) return
    await api.post('/community/posts', { title, content })
    setShowCreate(false); setTitle(''); setContent('')
    const { data } = await api.get('/community/posts')
    setPosts(data)
  }

  return (
    <div className="p-8 animate-fade-in">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">社区</h1>
          <p className="text-gray-500 mt-1">分享经验、讨论问题、协作创新</p>
        </div>
        <button onClick={() => setShowCreate(!showCreate)} className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-500 hover:bg-indigo-600 text-white transition-all">
          <Plus size={18} /> 发帖
        </button>
      </div>

      {showCreate && (
        <div className="bg-[#1a1a2e] rounded-xl p-6 border border-indigo-500/20 mb-6 animate-fade-in">
          <input value={title} onChange={(e) => setTitle(e.target.value)} className="w-full px-4 py-2 rounded-lg bg-[#0a0a0f] border border-[#27272a] text-white mb-3 focus:border-indigo-500 focus:outline-none" placeholder="标题" />
          <textarea value={content} onChange={(e) => setContent(e.target.value)} className="w-full px-4 py-2 rounded-lg bg-[#0a0a0f] border border-[#27272a] text-white h-32 resize-none focus:border-indigo-500 focus:outline-none" placeholder="内容..." />
          <div className="flex justify-end gap-3 mt-3">
            <button onClick={() => setShowCreate(false)} className="px-4 py-2 rounded-lg text-gray-400 hover:text-white text-sm">取消</button>
            <button onClick={handleCreate} className="px-4 py-2 rounded-lg bg-indigo-500 hover:bg-indigo-600 text-white text-sm">发布</button>
          </div>
        </div>
      )}

      <div className="space-y-4">
        {posts.map((post) => (
          <div key={post.id} className="bg-[#1a1a2e] rounded-xl p-6 border border-[#27272a] hover:border-indigo-500/20 transition-all">
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2 py-0.5 rounded text-xs bg-indigo-500/10 text-indigo-400">{post.post_type}</span>
              <span className="text-xs text-gray-600">{post.author}</span>
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">{post.title}</h3>
            <div className="flex items-center gap-4 text-xs text-gray-500">
              <span className="flex items-center gap-1"><Eye size={12} /> {post.view_count || 0}</span>
              <span className="flex items-center gap-1"><Heart size={12} /> {post.like_count || 0}</span>
              <span className="flex items-center gap-1"><MessageSquare size={12} /> {post.comment_count || 0}</span>
              {post.tags?.map((t) => <span key={t} className="px-2 py-0.5 rounded bg-gray-500/10 text-gray-400">{t}</span>)}
            </div>
          </div>
        ))}
        {posts.length === 0 && (
          <div className="text-center py-16 text-gray-500">
            <MessageSquare size={48} className="mx-auto mb-4 opacity-30" />
            <p>社区还没有帖子，发第一帖吧！</p>
          </div>
        )}
      </div>
    </div>
  )
}
