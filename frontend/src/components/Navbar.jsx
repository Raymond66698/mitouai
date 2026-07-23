import { useState, useRef, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import   {
    BarChart3, Search, Zap, Bell, Settings, LogOut, Menu, X,
    TrendingUp, Radio, Star, FileText, DollarSign, GitBranch,
  Share2, Filter, Sparkles, ChevronDown, User, Crown, Coins,
  GraduationCap, BookMarked
} from 'lucide-react'

const navGroups = [
  {
    label: 'AI 分析', icon: Sparkles,
    children: [
      { to: '/analysis', label: '投研分析', desc: 'AI多智能体深度分析', icon: Search },
      { to: '/screener', label: 'AI 选股器', desc: '自然语言智能选股', icon: Filter },
      { to: '/backtest', label: '策略回测', desc: '验证历史表现', icon: TrendingUp },
    ]
  },
  {
    label: '数据中心', icon: BarChart3,
    children: [
      { to: '/brief', label: '每日播报', desc: 'AI市场综述', icon: Radio },
      { to: '/research', label: '研报聚合', desc: 'AI摘要研报', icon: FileText },
      { to: '/capital', label: '资金流向', desc: '北向/龙虎榜', icon: DollarSign },
      { to: '/chain', label: '产业链', desc: '上下游图谱', icon: GitBranch },
    ]
  },
  { to: '/strategies', label: '策略超市', icon: Zap },
  { to: '/classroom', label: '策略小课堂', icon: GraduationCap },
  { to: '/notes', label: '知识笔记', icon: BookMarked },
  { to: '/community', label: '策略广场', icon: Share2 },
  {
    label: '我的', icon: User,
    children: [
      { to: '/watchlist', label: '我的投资', desc: '自选股与组合', icon: Star },
      { to: '/tokens', label: 'Token 中心', desc: '余额与套餐', icon: Coins },
      { to: '/notifications', label: '消息通知', icon: Bell },
      { to: '/settings', label: '账户设置', icon: Settings },
    ]
  },
]

export default function Navbar() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)
  const [activeDropdown, setActiveDropdown] = useState(null)
  const dropdownRef = useRef(null)

  useEffect(() => {
    const handler = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setActiveDropdown(null)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const isActive = (to) => location.pathname === to
  const isGroupActive = (group) => {
    if (group.to) return isActive(group.to)
    if (group.children) return group.children.some(c => isActive(c.to))
    return false
  }

  return (
    <nav className="sticky top-0 z-50 border-b" style={{
      background: 'rgba(255, 251, 245, 0.85)',
      backdropFilter: 'blur(20px)',
      borderColor: 'rgba(200, 150, 62, 0.12)',
    }}>
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-14">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5 shrink-0 group">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-sm transition-shadow"
              style={{
                background: 'linear-gradient(135deg, #C8963E, #E8A817)',
                boxShadow: '0 2px 12px rgba(200, 150, 62, 0.3)',
              }}>
              觅
            </div>
            <span className="text-lg font-bold" style={{ color: '#3D2A0C' }}>觅投AI</span>
          </Link>

          {/* Desktop Nav - always visible */}
          <div className="hidden md:flex items-center gap-1" ref={dropdownRef}>
            {navGroups.map((group, i) => {
              const active = isGroupActive(group)
              if (group.to) {
                const Icon = group.icon
                return (
                  <Link key={i} to={group.to}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[13px] font-medium transition-all
                      ${active
                        ? 'text-white'
                        : 'hover:bg-base-1'
                      }`}
                    style={
                      active
                        ? { background: 'linear-gradient(135deg, #C8963E, #E8A817)', boxShadow: '0 2px 8px rgba(200, 150, 62, 0.25)' }
                        : { color: '#6B5B4E' }
                    }>
                    <Icon className="w-3.5 h-3.5" />
                    {group.label}
                  </Link>
                )
              }
              const Icon = group.icon
              const open = activeDropdown === i
              return (
                <div key={i} className="relative">
                  <button
                    onClick={() => setActiveDropdown(open ? null : i)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[13px] font-medium transition-all
                      ${active ? 'text-white' : 'hover:bg-base-1'}`}
                    style={
                      active
                        ? { background: 'linear-gradient(135deg, #C8963E, #E8A817)', boxShadow: '0 2px 8px rgba(200, 150, 62, 0.25)' }
                        : { color: '#6B5B4E' }
                    }>
                    <Icon className="w-3.5 h-3.5" />
                    {group.label}
                    <ChevronDown className={`w-3 h-3 transition-transform duration-200 ${open ? 'rotate-180' : ''}`} />
                  </button>
                  {open && (
                    <div className="absolute top-full left-0 mt-1.5 w-52 bg-white border rounded-xl shadow-2xl py-2 animate-scale-in origin-top-left"
                      style={{ borderColor: '#F0E6D3', boxShadow: '0 8px 30px rgba(139, 115, 85, 0.15)' }}>
                      {group.children.map((child, j) => {
                        const ChildIcon = child.icon
                        const childActive = isActive(child.to)
                        return (
                          <Link key={j} to={child.to} onClick={() => setActiveDropdown(null)}
                            className={`flex items-start gap-3 px-4 py-2.5 mx-2 rounded-lg transition-all
                              ${childActive ? '' : 'hover:bg-base-1'}`}
                            style={childActive ? { background: 'rgba(200, 150, 62, 0.1)' } : {}}>
                            <ChildIcon className={`w-4 h-4 mt-0.5 shrink-0 ${childActive ? '' : ''}`}
                              style={childActive ? { color: '#C8963E' } : { color: '#A09080' }} />
                            <div>
                              <div className="text-[13px] font-medium" style={childActive ? { color: '#C8963E' } : { color: '#1A1A2E' }}>
                                {child.label}
                              </div>
                              <div className="text-2xs mt-0.5" style={{ color: '#A09080' }}>{child.desc}</div>
                            </div>
                          </Link>
                        )
                      })}
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          {/* Right side */}
          <div className="flex items-center gap-2">
            {user ? (
              <div className="hidden md:flex items-center gap-2">
                <Link to="/pricing"
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-[13px] font-medium transition-all"
                  style={{ color: '#C41E3A' }}
                  onMouseEnter={e => { e.target.style.background = 'rgba(196, 30, 58, 0.06)' }}
                  onMouseLeave={e => { e.target.style.background = 'transparent' }}>
                  <Crown className="w-3.5 h-3.5" />
                  升级 Pro
                </Link>
                <div className="w-px h-5 mx-1" style={{ background: '#F0E6D3' }} />
                <span className="text-[13px]" style={{ color: '#6B5B4E' }}>{user.display_name}</span>
                <span className="badge badge-gold text-2xs">{user.plan_name || '免费版'}</span>
                <button onClick={logout} className="p-1.5 rounded-lg transition-all"
                  style={{ color: '#A09080' }}
                  onMouseEnter={e => { e.target.style.background = '#FFF3E0'; e.target.style.color = '#6B5B4E' }}
                  onMouseLeave={e => { e.target.style.background = 'transparent'; e.target.style.color = '#A09080' }}
                  title="退出登录">
                  <LogOut className="w-3.5 h-3.5" />
                </button>
              </div>
            ) : (
              <div className="hidden md:flex items-center gap-2">
                <Link to="/login" className="px-4 py-1.5 text-[13px] font-medium rounded-lg transition-all"
                  style={{ color: '#6B5B4E' }}
                  onMouseEnter={e => { e.target.style.background = '#FFF3E0'; e.target.style.color = '#3D2A0C' }}
                  onMouseLeave={e => { e.target.style.background = 'transparent'; e.target.style.color = '#6B5B4E' }}>
                  登录
                </Link>
                <Link to="/register" className="btn-primary text-[13px] !py-1.5 !px-4">免费注册</Link>
              </div>
            )}
            <button className="md:hidden p-1.5 rounded-lg transition-all"
              style={{ color: '#6B5B4E' }}
              onClick={() => setMenuOpen(!menuOpen)}>
              {menuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {menuOpen && user && (
          <div className="md:hidden border-t py-3 space-y-1 animate-slide-down" style={{ borderColor: '#F0E6D3' }}>
            {navGroups.map((group, i) => {
              if (group.to) {
                const Icon = group.icon
                return (
                  <Link key={i} to={group.to} onClick={() => setMenuOpen(false)}
                    className={`flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors
                      ${isActive(group.to) ? '' : ''}`}
                    style={isActive(group.to)
                      ? { background: 'linear-gradient(135deg, #C8963E, #E8A817)', color: '#fff' }
                      : { color: '#6B5B4E' }}>
                    <Icon className="w-4 h-4" />{group.label}
                  </Link>
                )
              }
              return (
                <div key={i}>
                  <div className="px-3 py-1.5 text-2xs font-semibold uppercase tracking-wider" style={{ color: '#A09080' }}>
                    {group.label}
                  </div>
                  {group.children.map((child, j) => {
                    const ChildIcon = child.icon
                    return (
                      <Link key={j} to={child.to} onClick={() => setMenuOpen(false)}
                        className={`flex items-center gap-2.5 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors`}
                        style={isActive(child.to)
                          ? { background: 'rgba(200, 150, 62, 0.1)', color: '#C8963E' }
                          : { color: '#6B5B4E' }}>
                        <ChildIcon className="w-4 h-4" />
                        <div>
                          <div>{child.label}</div>
                          <div className="text-2xs" style={{ color: '#A09080' }}>{child.desc}</div>
                        </div>
                      </Link>
                    )
                  })}
                </div>
              )
            })}
            <button onClick={() => { logout(); setMenuOpen(false) }}
              className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium w-full"
              style={{ color: '#C41E3A' }}>
              <LogOut className="w-4 h-4" />退出登录
            </button>
          </div>
        )}
        {menuOpen && !user && (
          <div className="md:hidden border-t py-3 space-y-2" style={{ borderColor: '#F0E6D3' }}>
            <Link to="/login" onClick={() => setMenuOpen(false)} className="block px-3 py-2.5 text-sm rounded-lg"
              style={{ color: '#6B5B4E' }}>登录</Link>
            <Link to="/register" onClick={() => setMenuOpen(false)}
              className="block px-3 py-2.5 text-sm text-white rounded-lg text-center font-medium"
              style={{ background: 'linear-gradient(135deg, #C8963E, #E8A817)' }}>免费注册</Link>
          </div>
        )}
      </div>
    </nav>
  )
}
