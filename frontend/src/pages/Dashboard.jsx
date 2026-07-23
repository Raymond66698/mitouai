import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import api from '../api'
import {
  Search, TrendingUp, Zap, FileText, Star, BarChart3, ArrowRight,
  Newspaper, Sparkles, Filter, Crown, Coins, Radio, Activity,
  Gauge, Layers, PieChart
} from 'lucide-react'

const QUICK_TOOLS = [
  { to: '/analysis', icon: Search, label: 'AI 深度分析', desc: '多智能体联合研判', color: '#C8963E', bg: 'rgba(200,150,62,0.08)' },
  { to: '/screener', icon: Filter, label: 'AI 选股器', desc: '全市场智能筛选', color: '#059669', bg: 'rgba(5,150,105,0.08)' },
  { to: '/backtest', icon: TrendingUp, label: '策略回测', desc: '验证你的交易策略', color: '#2563EB', bg: 'rgba(37,99,235,0.08)' },
  { to: '/strategies', icon: Zap, label: '策略超市', desc: '大师策略一键应用', color: '#C41E3A', bg: 'rgba(196,30,58,0.08)' },
]

const MARKET_INDICES = [
  { code: '000001', name: '上证指数', key: 'sh' },
  { code: '399001', name: '深证成指', key: 'sz' },
  { code: '399006', name: '创业板指', key: 'cyb' },
  { code: '000688', name: '科创50', key: 'kc' },
  { code: '000300', name: '沪深300', key: 'hs300' },
]

const HOT_TAGS = ['贵州茅台', '宁德时代', '比亚迪', '中芯国际', '科创50']

// ── 数字滚动动画 ──
function useCountUp(end, duration = 1200, start = 0) {
  const [value, setValue] = useState(start)
  const ref = useRef(null)
  const hasAnimated = useRef(false)

  useEffect(() => {
    if (!ref.current) return
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !hasAnimated.current) {
          hasAnimated.current = true
          const startTime = performance.now()
          const tick = (now) => {
            const progress = Math.min((now - startTime) / duration, 1)
            const easeOutQuart = 1 - Math.pow(1 - progress, 4)
            setValue(start + (end - start) * easeOutQuart)
            if (progress < 1) requestAnimationFrame(tick)
          }
          requestAnimationFrame(tick)
        }
      },
      { threshold: 0.3 }
    )
    observer.observe(ref.current)
    return () => observer.disconnect()
  }, [end, duration, start])

  return [value, ref]
}

// ── 滚动揭示动画 ──
function useReveal(options = {}) {
  const ref = useRef(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    if (!ref.current) return
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setVisible(true)
            if (options.once !== false) observer.unobserve(entry.target)
          }
        })
      },
      { threshold: options.threshold || 0.12, rootMargin: options.margin || '0px 0px -40px 0px' }
    )
    observer.observe(ref.current)
    return () => observer.disconnect()
  }, [options.once, options.threshold, options.margin])

  return [ref, visible]
}

// ── 金色粒子背景 ──
function GoldParticles() {
  const particles = Array.from({ length: 18 }, (_, i) => ({
    id: i,
    size: 2 + Math.random() * 4,
    left: `${Math.random() * 100}%`,
    top: `${Math.random() * 100}%`,
    delay: `${Math.random() * 5}s`,
    duration: `${8 + Math.random() * 12}s`,
    opacity: 0.15 + Math.random() * 0.25,
  }))

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {particles.map((p) => (
        <div
          key={p.id}
          className="gold-particle"
          style={{
            width: p.size,
            height: p.size,
            left: p.left,
            top: p.top,
            animationDelay: p.delay,
            animationDuration: p.duration,
            opacity: p.opacity,
          }}
        />
      ))}
    </div>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [indices, setIndices] = useState([])
  const [news, setNews] = useState([])
  const [recentAnalysis, setRecentAnalysis] = useState([])
  const [marketOverview, setMarketOverview] = useState(null)
  const [loading, setLoading] = useState(true)
  const [mounted, setMounted] = useState(false)

  const [heroRef, heroVisible] = useReveal({ threshold: 0.05 })
  const [indicesRef, indicesVisible] = useReveal({ threshold: 0.1 })
  const [toolsRef, toolsVisible] = useReveal({ threshold: 0.1 })
  const [bottomRef, bottomVisible] = useReveal({ threshold: 0.1 })
  const [ctaRef, ctaVisible] = useReveal({ threshold: 0.2 })

  useEffect(() => {
    setMounted(true)
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      const [idxRes, newsRes, mktRes] = await Promise.all([
        api.get('/market/indices').catch(() => ({ data: { indices: [] } })),
        api.get('/market/news?limit=6').catch(() => ({ data: { news: [] } })),
        api.get('/quant/market-overview').catch(() => ({ data: null })),
      ])
      setIndices(idxRes.data?.indices || [])
      setNews(newsRes.data?.news || [])
      if (mktRes.data && !mktRes.data.error) setMarketOverview(mktRes.data)
    } catch {
      // 静默失败
    }
    try {
      const histRes = await api.get('/tokens/history?limit=3').catch(() => ({ data: { history: [] } }))
      setRecentAnalysis(histRes.data?.history?.filter(h => h.type === 'consume').slice(0, 3) || [])
    } catch {}
    setLoading(false)
  }

  const handleSearch = (e) => {
    e.preventDefault()
    if (query.trim()) {
      navigate(`/analysis?q=${encodeURIComponent(query.trim())}`)
    }
  }

  const formatPrice = (v) => {
    if (v == null) return '--'
    return Number(v).toFixed(2)
  }

  const formatChange = (v) => {
    if (v == null) return '--'
    const n = Number(v)
    return n > 0 ? `+${n.toFixed(2)}%` : `${n.toFixed(2)}%`
  }

  return (
    <div className="min-h-screen pb-12" style={{ background: '#FFF8EE' }}>
      {/* ── Hero 搜索区 ── */}
      <div
        ref={heroRef}
        className={`relative overflow-hidden rounded-2xl mb-8 transition-all duration-1000 ${heroVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}
        style={{
          background: 'linear-gradient(135deg, #FFF8EE 0%, #FFF3E0 30%, #FEF0D0 60%, #FFF8EE 100%)',
          border: '1px solid rgba(200, 150, 62, 0.15)',
        }}>
        <GoldParticles />

        {/* 顶部光晕 */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[700px] h-[350px] rounded-full opacity-30 pointer-events-none"
          style={{ background: 'radial-gradient(ellipse, rgba(232,168,23,0.25) 0%, transparent 70%)' }} />
        <div className="absolute top-0 right-0 w-[400px] h-[400px] rounded-full opacity-20 pointer-events-none"
          style={{ background: 'radial-gradient(circle, rgba(196,30,58,0.12) 0%, transparent 65%)' }} />

        <div className="relative px-6 py-10 md:py-14">
          <div className="max-w-2xl mx-auto text-center">
            <div className={`inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-medium mb-5 border transition-all duration-700 delay-100 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}
              style={{ background: 'rgba(200,150,62,0.08)', borderColor: 'rgba(200,150,62,0.2)', color: '#C8963E' }}>
              <Sparkles className="w-3.5 h-3.5" />
              今日市场已更新 · AI 分析师在线待命
            </div>

            <h1 className={`text-3xl md:text-4xl lg:text-5xl font-extrabold mb-4 text-gradient transition-all duration-700 delay-200 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
              AI 驱动 · 洞见财富
            </h1>
            <p className={`text-base md:text-lg mb-8 transition-all duration-700 delay-300 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`} style={{ color: '#6B5B4E' }}>
              多智能体联合研判，量化因子 + 大师方法论，让每一次决策都有数据支撑
            </p>

            <form onSubmit={handleSearch} className={`relative max-w-xl mx-auto transition-all duration-700 delay-400 ${mounted ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-4 scale-95'}`}>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="输入股票名称或代码，AI 帮你深度分析..."
                className="w-full pl-5 pr-28 py-4 text-base rounded-2xl border-2 transition-all outline-none"
                style={{
                  background: '#FFFFFF',
                  borderColor: 'rgba(200,150,62,0.3)',
                  boxShadow: '0 4px 20px rgba(200,150,62,0.08)',
                  color: '#1A1A2E',
                }}
                onFocus={e => { e.target.style.borderColor = '#C8963E'; e.target.style.boxShadow = '0 8px 32px rgba(200,150,62,0.2)'; }}
                onBlur={e => { e.target.style.borderColor = 'rgba(200,150,62,0.3)'; e.target.style.boxShadow = '0 4px 20px rgba(200,150,62,0.08)'; }}
              />
              <button type="submit" className="btn-primary absolute right-2 top-1/2 -translate-y-1/2 text-sm !py-2.5 hover:scale-105 transition-transform">
                <Search className="w-4 h-4" />
                分析
              </button>
            </form>

            <div className={`flex flex-wrap items-center justify-center gap-2 mt-5 transition-all duration-700 delay-500 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
              <span className="text-xs" style={{ color: '#A09080' }}>热门搜索：</span>
              {HOT_TAGS.map((s, i) => (
                <button key={s}
                  onClick={() => navigate(`/analysis?q=${encodeURIComponent(s)}`)}
                  className="text-xs px-3 py-1 rounded-full border transition-all hover:-translate-y-0.5 hover:shadow-md"
                  style={{
                    background: '#FFFFFF',
                    borderColor: '#F0E6D3',
                    color: '#6B5B4E',
                    transitionDelay: `${500 + i * 60}ms`,
                  }}
                  onMouseEnter={e => { e.target.style.borderColor = '#C8963E'; e.target.style.color = '#C8963E'; }}
                  onMouseLeave={e => { e.target.style.borderColor = '#F0E6D3'; e.target.style.color = '#6B5B4E'; }}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── 市场指数条 ── */}
      <div
        ref={indicesRef}
        className={`grid grid-cols-2 md:grid-cols-5 gap-3 mb-8 transition-all duration-700 ${indicesVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
        {indices.length > 0 ? indices.slice(0, 5).map((idx, i) => {
          const isStatic = idx.static || idx.value == null
          const isUp = (idx.change || 0) >= 0
          return (
            <div
              key={idx.code || i}
              className="card p-4 index-card group cursor-pointer"
              style={{ transitionDelay: `${i * 80}ms` }}
              onClick={() => navigate(`/analysis?q=${encodeURIComponent(idx.name || idx.code)}`)}>
              <div className="flex items-center justify-between mb-1">
                <p className="text-xs truncate font-medium" style={{ color: '#A09080' }}>{idx.name || idx.code}</p>
                <Activity className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" style={{ color: '#C8963E' }} />
              </div>
              <p className="text-2xl font-bold num mt-1" style={{ color: '#1A1A2E' }}>
                {isStatic ? '—' : formatPrice(idx.value)}
              </p>
              <div className="flex items-center gap-1.5 mt-1.5">
                {isStatic ? (
                  <span className="text-xs font-medium px-2 py-0.5 rounded-full" style={{ background: '#F0E6D3', color: '#8B7355' }}>
                    已收盘
                  </span>
                ) : (
                  <>
                    <span className={`text-xs font-semibold num ${isUp ? 'text-up-DEFAULT' : 'text-down-DEFAULT'}`}>
                      {formatChange(idx.change_pct || idx.change)}
                    </span>
                    {idx.change_amt != null && (
                      <span className={`text-2xs num ${isUp ? 'text-up-DEFAULT' : 'text-down-DEFAULT'}`}>
                        {isUp ? '+' : ''}{Number(idx.change_amt).toFixed(2)}
                      </span>
                    )}
                  </>
                )}
              </div>
              {/* 涨跌色底条 */}
              <div className="absolute bottom-0 left-0 right-0 h-0.5 rounded-b-2xl opacity-60"
                style={{ background: isStatic ? '#D4C4A8' : (isUp ? '#EF4444' : '#10B981') }} />
            </div>
          )
        }) : (
          <>
            {MARKET_INDICES.map((idx, i) => (
              <div key={idx.code} className="card p-4" style={{ transitionDelay: `${i * 80}ms` }}>
                <p className="skeleton h-3 w-16 rounded" />
                <p className="skeleton h-6 w-24 rounded mt-2" />
                <p className="skeleton h-3 w-20 rounded mt-1" />
              </div>
            ))}
          </>
        )}
      </div>

      {/* ── 市场概览条 ── */}
      {marketOverview && (
        <Link to="/market" className="block mb-8 group">
          <div className="card p-4 transition-all group-hover:shadow-lg"
            style={{ background: 'linear-gradient(135deg, rgba(200,150,62,0.04), rgba(255,255,255,0.6))' }}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4" style={{ color: '#C8963E' }} />
                <span className="text-sm font-bold" style={{ color: '#1A1A2E' }}>市场概览</span>
                <span className="text-2xs" style={{ color: '#A09080' }}>
                  {marketOverview.total_stocks?.toLocaleString() || 0} 只A股 · 更新于 {marketOverview.cache_time || '--'}
                </span>
              </div>
              <span className="text-xs flex items-center gap-1 transition-all group-hover:gap-2" style={{ color: '#C8963E' }}>
                查看详情 <ArrowRight className="w-3 h-3" />
              </span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <div className="flex items-center gap-2">
                <Gauge className="w-4 h-4 shrink-0" style={{ color: '#C8963E' }} />
                <div>
                  <div className="text-2xs" style={{ color: '#A09080' }}>中位PE</div>
                  <div className="text-base font-bold num" style={{ color: '#1A1A2E' }}>
                    {marketOverview.median_pe?.toFixed(1) || '--'}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 shrink-0" style={{ color: '#7C3AED' }} />
                <div>
                  <div className="text-2xs" style={{ color: '#A09080' }}>中位PB</div>
                  <div className="text-base font-bold num" style={{ color: '#1A1A2E' }}>
                    {marketOverview.median_pb?.toFixed(1) || '--'}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <PieChart className="w-4 h-4 shrink-0" style={{ color: '#2563EB' }} />
                <div>
                  <div className="text-2xs" style={{ color: '#A09080' }}>总市值</div>
                  <div className="text-base font-bold num" style={{ color: '#1A1A2E' }}>
                    {marketOverview.total_market_cap_yi >= 10000
                      ? `${(marketOverview.total_market_cap_yi / 10000).toFixed(1)}万亿`
                      : `${marketOverview.total_market_cap_yi?.toFixed(0) || 0}亿`}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 shrink-0" style={{ color: '#DC2626' }} />
                <div>
                  <div className="text-2xs" style={{ color: '#A09080' }}>上涨</div>
                  <div className="text-base font-bold num" style={{ color: '#DC2626' }}>
                    {marketOverview.up_count || 0}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 shrink-0" style={{ color: '#059669' }} />
                <div>
                  <div className="text-2xs" style={{ color: '#A09080' }}>下跌</div>
                  <div className="text-base font-bold num" style={{ color: '#059669' }}>
                    {marketOverview.down_count || 0}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Link>
      )}

      {/* ── 功能快捷入口 ── */}
      <div ref={toolsRef} className={`mb-8 transition-all duration-700 ${toolsVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold" style={{ color: '#1A1A2E' }}>⚡ 快速开始</h2>
          <Link to="/tokens" className="flex items-center gap-1 text-sm font-medium transition-all hover:gap-2"
            style={{ color: '#C8963E' }}>
            <Coins className="w-4 h-4" /> Token 中心 <ArrowRight className="w-3 h-3" />
          </Link>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {QUICK_TOOLS.map((tool, i) => {
            const Icon = tool.icon
            return (
              <Link key={i} to={tool.to}
                className="card card-hover p-5 group cursor-pointer tool-card"
                style={{ transitionDelay: `${i * 100}ms` }}>
                <div className="w-11 h-11 rounded-xl flex items-center justify-center mb-3 transition-all duration-300 group-hover:scale-110 group-hover:rotate-3"
                  style={{ background: tool.bg }}>
                  <Icon className="w-5 h-5" style={{ color: tool.color }} />
                </div>
                <h3 className="font-bold text-base mb-1 transition-colors group-hover:text-primary-600" style={{ color: '#1A1A2E' }}>{tool.label}</h3>
                <p className="text-xs" style={{ color: '#A09080' }}>{tool.desc}</p>
                <div className="mt-3 flex items-center gap-1 text-xs font-medium transition-all group-hover:gap-2" style={{ color: tool.color }}>
                  立即使用 <ArrowRight className="w-3 h-3" />
                </div>
              </Link>
            )
          })}
        </div>
      </div>

      {/* ── 底部双栏 ── */}
      <div ref={bottomRef} className={`grid grid-cols-1 lg:grid-cols-2 gap-6 transition-all duration-700 ${bottomVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
        {/* 最近分析 */}
        <div className="card p-6" style={{ transitionDelay: '0ms' }}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold" style={{ color: '#1A1A2E' }}>
              <FileText className="w-4 h-4 inline mr-1.5" style={{ color: '#C8963E' }} />
              最近分析
            </h3>
            <Link to="/analysis" className="text-xs font-medium transition-all hover:gap-1" style={{ color: '#C8963E' }}>
              全部 <ArrowRight className="w-3 h-3 inline" />
            </Link>
          </div>
          {recentAnalysis.length > 0 ? (
            <div className="space-y-3">
              {recentAnalysis.map((tx, i) => (
                <div key={i} className="flex items-center justify-between py-2 border-b last:border-0 news-item" style={{ borderColor: '#F0E6D3', transitionDelay: `${i * 80}ms` }}>
                  <div>
                    <p className="text-sm font-medium" style={{ color: '#1A1A2E' }}>
                      {tx.action === 'analysis_basic' ? '基础分析' : tx.action === 'analysis_deep' ? '深度分析' : tx.action === 'analysis_report' ? '深度研报' : tx.action || '分析'}
                    </p>
                    <p className="text-2xs" style={{ color: '#A09080' }}>
                      {tx.created_at?.slice(0, 16).replace('T', ' ') || ''}
                    </p>
                  </div>
                  <span className="text-xs font-semibold" style={{ color: '#C8963E' }}>
                    -{Math.abs(tx.tokens)} tokens
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-3xl mb-2">🔍</p>
              <p className="text-sm" style={{ color: '#A09080' }}>还没有分析记录</p>
              <button onClick={() => navigate('/analysis')} className="btn-primary text-xs mt-3 hover:scale-105 transition-transform">开始分析</button>
            </div>
          )}
        </div>

        {/* 市场要闻 */}
        <div className="card p-6" style={{ transitionDelay: '120ms' }}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold" style={{ color: '#1A1A2E' }}>
              <Newspaper className="w-4 h-4 inline mr-1.5" style={{ color: '#C8963E' }} />
              市场要闻
            </h3>
            <Link to="/brief" className="text-xs font-medium transition-all hover:gap-1" style={{ color: '#C8963E' }}>
              更多 <ArrowRight className="w-3 h-3 inline" />
            </Link>
          </div>
          {news.length > 0 ? (
            <div className="space-y-3">
              {news.slice(0, 6).map((item, i) => (
                <a key={i} href={item.url || '#'} target="_blank" rel="noopener noreferrer"
                  className="block py-2 border-b last:border-0 group news-item" style={{ borderColor: '#F0E6D3', transitionDelay: `${i * 80}ms` }}>
                  <p className="text-sm line-clamp-2 group-hover:underline transition-all" style={{ color: '#1A1A2E' }}>
                    {item.title}
                  </p>
                  <p className="text-2xs mt-1" style={{ color: '#A09080' }}>{item.time || item.date || ''}</p>
                </a>
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="py-2 border-b last:border-0" style={{ borderColor: '#F0E6D3' }}>
                  <div className="skeleton h-4 w-full rounded" />
                  <div className="skeleton h-3 w-20 rounded mt-2" />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ── Token 提醒卡片 ── */}
      <div ref={ctaRef} className={`mt-6 transition-all duration-700 ${ctaVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
        <div className="card p-5 flex items-center justify-between flex-wrap gap-4 cta-card" style={{
          background: 'linear-gradient(135deg, rgba(200,150,62,0.06), rgba(249,190,60,0.03))',
          borderColor: 'rgba(200,150,62,0.2)',
        }}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: 'linear-gradient(135deg, #C8963E, #E8A817)' }}>
              <Coins className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="font-bold text-sm" style={{ color: '#1A1A2E' }}>Token 消耗制</p>
              <p className="text-xs" style={{ color: '#A09080' }}>每次分析消耗 tokens，按需充值更灵活</p>
            </div>
          </div>
          <Link to="/tokens" className="btn-primary text-sm hover:scale-105 transition-transform">
            管理 Token <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>
    </div>
  )
}
