import { useEffect, useState } from 'react'
import { api } from '../hooks/useAuth'
import { MessageSquare, Heart, Eye, Plus, X, Send } from 'lucide-react'

export default function CommunityPage() {
  const [posts, setPosts] = useState([])
  const [showCreate, setShowCreate] = useState(false)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')

  // 帖子详情弹窗
  const [detail, setDetail] = useState(null)
  const [comment, setComment] = useState('')
  const [loadingDetail, setLoadingDetail] = useState(false)

  const loadPosts = async () => {
    try {
      const { data } = await api.get('/community/posts')
      setPosts(data)
    } catch { setPosts([]) }
  }

  useEffect(() => { loadPosts() }, [])

  const handleCreate = async () => {
    if (!title.trim() || !content.trim()) return
    await api.post('/community/posts', { title, content })
    setShowCreate(false); setTitle(''); setContent('')
    loadPosts()
  }

  const openDetail = async (postId) => {
    setLoadingDetail(true)
    try {
      const { data } = await api.get(`/community/posts/${postId}`)
      setDetail(data)
      loadPosts() // 浏览数变化后刷新列表
    } catch { setDetail(null) }
    setLoadingDetail(false)
  }

  const like = async () => {
    if (!detail) return
    await api.post(`/community/posts/${detail.id}/like`)
    openDetail(detail.id)
  }

  const sendComment = async () => {
    if (!comment.trim() || !detail) return
    await api.post(`/community/posts/${detail.id}/comments`, { content: comment.trim() })
    setComment('')
    openDetail(detail.id)
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
          <div key={post.id}
            onClick={() => openDetail(post.id)}
            className="bg-[#1a1a2e] rounded-xl p-6 border border-[#27272a] hover:border-indigo-500/40 transition-all cursor-pointer">
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

      {/* 帖子详情弹窗 */}
      {detail && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" onClick={() => setDetail(null)}>
          <div className="bg-[#1a1a2e] rounded-xl border border-[#27272a] w-full max-w-2xl max-h-[85vh] flex flex-col animate-fade-in"
            onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-start p-6 border-b border-[#27272a]">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="px-2 py-0.5 rounded text-xs bg-indigo-500/10 text-indigo-400">{detail.post_type}</span>
                  <span className="text-xs text-gray-600">{detail.author}</span>
                </div>
                <h2 className="text-xl font-bold text-white">{detail.title}</h2>
              </div>
              <button onClick={() => setDetail(null)} className="text-gray-500 hover:text-white"><X size={20} /></button>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              <p className="text-sm text-gray-300 whitespace-pre-wrap mb-4">{detail.content}</p>

              <div className="flex items-center gap-4 text-xs text-gray-500 mb-6">
                <button onClick={like} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-pink-500/10 text-pink-400 hover:bg-pink-500/20 transition-all">
                  <Heart size={13} /> {detail.like_count || 0} 赞
                </button>
                <span className="flex items-center gap-1"><Eye size={12} /> {detail.view_count} 浏览</span>
                <span className="flex items-center gap-1"><MessageSquare size={12} /> {detail.comment_count || 0} 评论</span>
              </div>

              <div className="space-y-3">
                {detail.comments?.map((c) => (
                  <div key={c.id} className="p-3 rounded-lg bg-[#0a0a0f] border border-[#27272a]">
                    <p className="text-sm text-gray-300">{c.content}</p>
                    <p className="text-xs text-gray-600 mt-1">用户#{c.author_id} · {c.created_at?.slice(0, 19).replace('T', ' ')}</p>
                  </div>
                ))}
                {(!detail.comments || detail.comments.length === 0) && (
                  <p className="text-sm text-gray-600 text-center py-4">还没有评论，来说两句吧</p>
                )}
              </div>
            </div>

            <div className="flex gap-3 p-4 border-t border-[#27272a]">
              <input
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && sendComment()}
                placeholder="写下你的评论..."
                className="flex-1 px-4 py-2 rounded-lg bg-[#0a0a0f] border border-[#27272a] text-white text-sm focus:border-indigo-500 focus:outline-none"
              />
              <button onClick={sendComment} disabled={!comment.trim()}
                className="px-4 py-2 rounded-lg bg-indigo-500 hover:bg-indigo-600 text-white text-sm flex items-center gap-1.5 disabled:opacity-40">
                <Send size={14} /> 评论
              </button>
            </div>
          </div>
        </div>
      )}
      {loadingDetail && null}
    </div>
  )
}
