import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../hooks/useAuth'
import { LayoutDashboard, GitBranch, Bot, MessageSquare, Settings, LogOut, Zap } from 'lucide-react'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: '控制台' },
  { to: '/workflows', icon: GitBranch, label: '工作流' },
  { to: '/agents', icon: Bot, label: 'Agent' },
  { to: '/community', icon: MessageSquare, label: '社区' },
  { to: '/system', icon: Settings, label: '运维' },
]

export default function Layout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen bg-[#0a0a0f]">
      {/* 侧边栏 */}
      <aside className="w-64 bg-[#12121a] border-r border-[#27272a] flex flex-col">
        <div className="p-6 border-b border-[#27272a]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <Zap size={20} className="text-white" />
            </div>
            <div>
              <h1 className="font-bold text-white">AI Community</h1>
              <p className="text-xs text-gray-500">智能社区平台</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                  isActive
                    ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`
              }
            >
              <item.icon size={18} />
              <span className="text-sm font-medium">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-[#27272a]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-400 to-blue-500 flex items-center justify-center text-xs font-bold text-white">
                {user?.username?.[0]?.toUpperCase() || 'U'}
              </div>
              <span className="text-sm text-gray-300">{user?.username || 'User'}</span>
            </div>
            <button onClick={handleLogout} className="p-2 rounded-lg hover:bg-white/5 text-gray-500 hover:text-red-400 transition-all">
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      {/* 主内容区 */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
