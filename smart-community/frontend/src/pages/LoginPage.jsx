import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../hooks/useAuth'
import { Zap, Eye, EyeOff } from 'lucide-react'

export default function LoginPage() {
  const [isRegister, setIsRegister] = useState(false)
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPwd, setShowPwd] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login, register } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (isRegister) {
        await register(username, email, password)
      } else {
        await login(username, password)
      }
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || '登录失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0a0a0f] relative overflow-hidden">
      {/* 背景动效 */}
      <div className="absolute inset-0">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
      </div>

      <div className="relative w-full max-w-md p-8">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 mb-4 animate-pulse-glow">
            <Zap size={32} className="text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white">AI Smart Community</h1>
          <p className="text-gray-500 mt-2">智能化社区 · 自动化工作流 · AI驱动</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-[#1a1a2e] rounded-2xl p-8 border border-[#27272a] shadow-2xl">
          <h2 className="text-xl font-semibold text-white mb-6">
            {isRegister ? '创建账号' : '欢迎回来'}
          </h2>

          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
              {error}
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-2">用户名</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-3 rounded-lg bg-[#0a0a0f] border border-[#27272a] text-white placeholder-gray-600 focus:border-indigo-500 focus:outline-none transition-all"
                placeholder="输入用户名"
                required
              />
            </div>

            {isRegister && (
              <div className="animate-fade-in">
                <label className="block text-sm text-gray-400 mb-2">邮箱</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-3 rounded-lg bg-[#0a0a0f] border border-[#27272a] text-white placeholder-gray-600 focus:border-indigo-500 focus:outline-none transition-all"
                  placeholder="your@email.com"
                  required
                />
              </div>
            )}

            <div>
              <label className="block text-sm text-gray-400 mb-2">密码</label>
              <div className="relative">
                <input
                  type={showPwd ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 rounded-lg bg-[#0a0a0f] border border-[#27272a] text-white placeholder-gray-600 focus:border-indigo-500 focus:outline-none transition-all pr-12"
                  placeholder="输入密码"
                  required
                />
                <button type="button" onClick={() => setShowPwd(!showPwd)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300">
                  {showPwd ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-6 py-3 rounded-lg bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-medium hover:from-indigo-600 hover:to-purple-700 transition-all disabled:opacity-50"
          >
            {loading ? '处理中...' : isRegister ? '注册' : '登录'}
          </button>

          <p className="text-center mt-4 text-sm text-gray-500">
            {isRegister ? '已有账号？' : '没有账号？'}
            <button type="button" onClick={() => setIsRegister(!isRegister)} className="text-indigo-400 hover:text-indigo-300 ml-1">
              {isRegister ? '去登录' : '去注册'}
            </button>
          </p>
        </form>
      </div>
    </div>
  )
}
