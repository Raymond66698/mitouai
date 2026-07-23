import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Zap, TrendingUp, BarChart3, Code, ChevronRight } from 'lucide-react'

export default function Strategies() {
  const navigate = useNavigate()
  const [strategies, setStrategies] = useState([])
  const [loading, setLoading] = useState(true)
  const [category, setCategory] = useState('')

  useEffect(() => {
    fetchStrategies()
  }, [category])

  const fetchStrategies = async () => {
    setLoading(true)
    try {
      const url = category ? `/api/strategies?category=${category}` : '/api/strategies'
      const r = await fetch(url)
      const data = await r.json()
      setStrategies(data.strategies || [])
    } catch { }
    setLoading(false)
  }

  const cats = [
    { id: '', label: '全部', icon: Zap },
    { id: 'master', label: '投资大师', icon: TrendingUp },
    { id: 'quant', label: '量化因子', icon: BarChart3 },
    { id: 'technical', label: '技术流派', icon: Code },
  ]

  const catColors = {
    master: 'bg-primary-50 text-primary-700 border-primary-200',
    quant: 'bg-primary-50 text-primary-700 border-primary-200',
    technical: 'bg-purple-50 text-purple-700 border-purple-200',
    custom: 'bg-base-2 text-ink-secondary border-base-4',
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-ink-primary">策略超市</h1>
          <p className="text-ink-muted mt-1">13+ 投资策略模板，覆盖投资大师、量化因子、技术流派</p>
        </div>
      </div>

      {/* Category Filter */}
      <div className="flex gap-2 mb-6 flex-wrap">
        {cats.map(cat => {
          const Icon = cat.icon
          return (
            <button
              key={cat.id}
              onClick={() => setCategory(cat.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all
                ${category === cat.id
                  ? 'bg-primary-600 text-white shadow-md'
                  : 'bg-base-2 text-ink-secondary border border-base-4 hover:border-gray-300'
                }`}
            >
              <Icon className="w-4 h-4" />
              {cat.label}
            </button>
          )
        })}
      </div>

      {/* Strategy Cards */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-10 w-10 border-4 border-primary-500 border-t-transparent"></div>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {strategies.map(s => (
            <div
              key={s.id}
              onClick={() => navigate(`/analysis?strategy_id=${s.id}`)}
              className="bg-base-2 rounded-xl border border-base-4 p-5 hover:border-primary-100 hover:shadow-md transition-all group cursor-pointer"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="w-10 h-10 bg-gradient-to-br from-primary-100 to-purple-100 rounded-xl flex items-center justify-center text-lg">
                  {s.icon ? (
                    /\.(png|jpg|jpeg|svg|gif|webp)$/i.test(s.icon) ? (
                      <img src={s.icon} className="w-6 h-6" alt="" />
                    ) : (
                      <span className="text-2xl leading-none">{s.icon}</span>
                    )
                  ) : (
                    <span className="text-2xl leading-none">{s.name?.[0]}</span>
                  )}
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full border ${catColors[s.category] || catColors.custom}`}>
                  {{ master: '大师', quant: '量化', technical: '技术', custom: '自定义' }[s.category] || s.category}
                </span>
              </div>
              <h3 className="font-semibold text-ink-primary mb-1">{s.name}</h3>
              <p className="text-xs text-ink-muted mb-2">{s.author && `by ${s.author}`}</p>
              <p className="text-sm text-ink-muted line-clamp-2 mb-3">{s.description}</p>
              <div className="flex flex-wrap gap-1.5">
                {(s.tags || []).slice(0, 4).map(t => (
                  <span key={t} className="text-xs px-2 py-0.5 bg-base-2 text-ink-muted rounded-full">{t}</span>
                ))}
              </div>
              <div className="mt-3 pt-3 border-t border-gray-50 flex items-center justify-between">
                <span className="text-xs text-ink-muted">
                  {Object.keys(s.config_schema || {}).length} 个可调参数
                </span>
                <ChevronRight className="w-4 h-4 text-ink-muted group-hover:text-primary-500 transition-colors" />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
