import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { Search, BarChart3, Zap, User, Bell, Settings, LogOut, Menu, X } from 'lucide-react'

export default function Navbar() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)

  const links = user ? [
    { to: '/', label: '首页', icon: BarChart3 },
    { to: '/analysis', label: '投研分析', icon: Search },
    { to: '/strategies', label: '策略超市', icon: Zap },
    { to: '/plans', label: '套餐', icon: Zap },
    { to: '/notifications', label: '通知', icon: Bell },
    { to: '/settings', label: '设置', icon: Settings },
  ] : []

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 text-xl font-bold text-primary-600 shrink-0">
            <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-purple-500 rounded-lg flex items-center justify-center text-white font-bold text-sm">
              觅
            </div>
            觅投AI
          </Link>

          {/* Desktop Nav */}
          {user && (
            <div className="hidden md:flex items-center gap-1">
              {links.map(link => {
                const Icon = link.icon
                const active = location.pathname === link.to
                return (
                  <Link
                    key={link.to}
                    to={link.to}
                    className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors
                      ${active
                        ? 'bg-primary-50 text-primary-700'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                      }`}
                  >
                    <Icon className="w-4 h-4" />
                    {link.label}
                  </Link>
                )
              })}
            </div>
          )}

          {/* Right side */}
          <div className="flex items-center gap-3">
            {user ? (
              <div className="hidden md:flex items-center gap-3">
                <span className="text-sm text-gray-500">
                  {user.display_name}
                  <span className="ml-1 px-1.5 py-0.5 text-xs rounded-full bg-primary-50 text-primary-600 font-medium">
                    {user.plan_name || '免费版'}
                  </span>
                </span>
                <button
                  onClick={logout}
                  className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
                  title="退出登录"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="hidden md:flex items-center gap-2">
                <Link to="/login" className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
                  登录
                </Link>
                <Link to="/register" className="px-4 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
                  免费注册
                </Link>
              </div>
            )}

            {/* Mobile menu toggle */}
            <button
              className="md:hidden p-2 text-gray-600 hover:bg-gray-100 rounded-lg"
              onClick={() => setMenuOpen(!menuOpen)}
            >
              {menuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {menuOpen && user && (
          <div className="md:hidden border-t border-gray-100 py-3 space-y-1">
            {links.map(link => {
              const Icon = link.icon
              const active = location.pathname === link.to
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  onClick={() => setMenuOpen(false)}
                  className={`flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors
                    ${active ? 'bg-primary-50 text-primary-700' : 'text-gray-600 hover:bg-gray-100'}`}
                >
                  <Icon className="w-4 h-4" />
                  {link.label}
                </Link>
              )
            })}
            <button
              onClick={() => { logout(); setMenuOpen(false) }}
              className="flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium text-red-600 hover:bg-red-50 w-full"
            >
              <LogOut className="w-4 h-4" />
              退出登录
            </button>
          </div>
        )}
        {menuOpen && !user && (
          <div className="md:hidden border-t border-gray-100 py-3 space-y-1">
            <Link to="/login" onClick={() => setMenuOpen(false)} className="block px-3 py-2.5 text-sm text-gray-700 hover:bg-gray-100 rounded-lg">
              登录
            </Link>
            <Link to="/register" onClick={() => setMenuOpen(false)} className="block px-3 py-2.5 text-sm bg-primary-600 text-white rounded-lg text-center">
              免费注册
            </Link>
          </div>
        )}
      </div>
    </nav>
  )
}
