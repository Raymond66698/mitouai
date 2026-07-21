import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { Search, Zap, TrendingUp, BarChart3, ChevronRight, ArrowUpRight } from 'lucide-react'
import { useState, useEffect } from 'react'

export default function Dashboard() {
  const { user, refreshUser } = useAuth()
  const [stocks, setStocks] = useState('')

  useEffect(() => { refreshUser() }, [])

  const cards = [
    {
      title: '投研分析',
      desc: '搜索股票，启动多智能体深度分析',
      icon: Search,
      link: '/analysis',
      color: 'from-blue-500 to-blue-600',
    },
    {
      title: '策略超市',
      desc: '13+投资策略模板，自由选择',
      icon: Zap,
      link: '/strategies',
      color: 'from-purple-500 to-purple-600',
    },
    {
      title: '今日配额',
      desc: `${user?.remaining || 0} 次剩余 / ${user?.plan_name || '免费版'}`,
      icon: TrendingUp,
      link: '/plans',
      color: 'from-emerald-500 to-emerald-600',
    },
  ]

  return (
    <div>
      {/* Welcome */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          你好，{user?.display_name || '投资者'}
        </h1>
        <p className="text-gray-500 mt-1">
          今日剩余 {user?.remaining || 0} 次分析 · {user?.plan_name || '免费版'}
        </p>
      </div>

      {/* Quick Search */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 mb-8">
        <div className="flex items-center gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={stocks}
              onChange={e => setStocks(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && stocks.trim()) {
                  window.location.href = `/analysis?q=${encodeURIComponent(stocks.trim())}`
                }
              }}
              placeholder="输入股票名称或代码（如：贵州茅台 / 600519）"
              className="w-full pl-12 pr-4 py-3.5 border-2 border-gray-100 rounded-xl focus:border-primary-400 focus:ring-2 focus:ring-primary-100 outline-none text-lg transition-all"
            />
          </div>
          <Link
            to={stocks.trim() ? `/analysis?q=${encodeURIComponent(stocks.trim())}` : '/analysis'}
            className="px-6 py-3.5 bg-primary-600 text-white rounded-xl font-semibold hover:bg-primary-700 transition-all flex items-center gap-2 shrink-0"
          >
            <Search className="w-5 h-5" />
            开始分析
          </Link>
        </div>
      </div>

      {/* Cards */}
      <div className="grid md:grid-cols-3 gap-6 mb-8">
        {cards.map((card, i) => {
          const Icon = card.icon
          return (
            <Link
              key={i}
              to={card.link}
              className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 hover:shadow-md hover:border-primary-100 transition-all group"
            >
              <div className={`w-12 h-12 bg-gradient-to-br ${card.color} rounded-xl flex items-center justify-center mb-4`}>
                <Icon className="w-6 h-6 text-white" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-1">{card.title}</h3>
              <p className="text-sm text-gray-500 mb-3">{card.desc}</p>
              <span className="text-primary-600 text-sm font-medium flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                进入 <ArrowUpRight className="w-3 h-3" />
              </span>
            </Link>
          )
        })}
      </div>

      {/* Recent / Tips */}
      <div className="bg-gradient-to-r from-primary-50 to-purple-50 rounded-2xl p-6 border border-primary-100">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 bg-primary-100 rounded-xl flex items-center justify-center shrink-0">
            <BarChart3 className="w-5 h-5 text-primary-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">快速上手</h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li className="flex items-center gap-2">
                <ChevronRight className="w-3 h-3 text-primary-500" />
                在搜索框输入股票名称或代码，开始首次分析
              </li>
              <li className="flex items-center gap-2">
                <ChevronRight className="w-3 h-3 text-primary-500" />
                前往「策略超市」选择巴菲特、林奇等大师策略
              </li>
              <li className="flex items-center gap-2">
                <ChevronRight className="w-3 h-3 text-primary-500" />
                在「设置→通知」中配置 PushPlus 微信推送，分析完成即时通知
              </li>
              <li className="flex items-center gap-2">
                <ChevronRight className="w-3 h-3 text-primary-500" />
                免费版每日3次分析，随时可升级到专业版（¥39/月）或大师版（¥99/月）
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
