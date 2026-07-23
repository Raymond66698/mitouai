import { useState, useEffect, useCallback } from 'react'
import {
  Radio, TrendingUp, TrendingDown, Sparkles, Loader2, RefreshCw,
  Newspaper, PieChart, Zap, AlertCircle, Calendar, DollarSign,
  ExternalLink, ChevronRight, Flame, Snowflake,
} from 'lucide-react'

export default function DailyBrief() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [overview, setOverview] = useState(null)
  const [aiSummary, setAiSummary] = useState('')
  const [events, setEvents] = useState([])
  const [concepts, setConcepts] = useState([])
  const [activeTab, setActiveTab] = useState('overview')

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError('')
    const token = localStorage.getItem('mitouai_token')
    const headers = { Authorization: `Bearer ${token}` }

    try {
      const [ovRes, aiRes, evRes, coRes] = await Promise.allSettled([
        fetch('/api/brief/overview', { headers }).then(r => r.json()),
        fetch('/api/brief/ai-summary', { headers }).then(r => r.json()),
        fetch('/api/brief/events', { headers }).then(r => r.json()),
        fetch('/api/brief/concepts', { headers }).then(r => r.json()),
      ])

      if (ovRes.status === 'fulfilled') {
        setOverview(ovRes.value)
        if (ovRes.value?.ai_summary) setAiSummary(ovRes.value.ai_summary)
      }
      if (aiRes.status === 'fulfilled' && aiRes.value?.ai_summary) {
        setAiSummary(aiRes.value.ai_summary)
      }
      if (evRes.status === 'fulfilled') setEvents(evRes.value?.events || [])
      if (coRes.status === 'fulfilled') setConcepts(coRes.value?.concepts || [])

      const allFailed = [ovRes, aiRes, evRes, coRes].every(r => r.status === 'rejected')
      if (allFailed) setError('数据加载失败，请稍后重试')
    } catch (e) {
      setError('网络错误：' + e.message)
    }
    setLoading(false)
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  const tabs = [
    { id: 'overview', label: '市场概览', icon: Radio },
    { id: 'sectors', label: '概念异动', icon: Zap },
    { id: 'events', label: '事件提醒', icon: Calendar },
  ]

  const stats = overview?.market_stats || {}
  const nf = overview?.north_flow || {}

  return (
    <div className="max-w-7xl mx-auto">
      {/* 头部 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-ink-primary flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-amber-500" />
            每日AI市场播报
          </h1>
          <p className="text-ink-muted mt-1">
            {overview?.date || '加载中...'} · AI实时解读市场动态
          </p>
        </div>
        <button onClick={fetchData} className="p-2 text-ink-muted hover:text-ink-secondary rounded-lg hover:bg-base-3">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {error && (
        <div className="bg-red-50 text-red-600 rounded-xl p-4 mb-6 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" /> {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
        </div>
      ) : (
        <>
          {/* AI 市场综述 */}
          {aiSummary && (
            <div className="bg-gradient-to-br from-primary-50 via-accent-50 to-primary-100/30 rounded-2xl border border-primary-100 p-6 mb-6">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-indigo-500 rounded-xl flex items-center justify-center shrink-0">
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-ink-primary mb-2">AI 市场综述</h3>
                  <p className="text-ink-secondary leading-relaxed text-sm whitespace-pre-wrap">{aiSummary}</p>
                </div>
              </div>
            </div>
          )}

          {/* 指数卡片 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
            {(overview?.indices || []).map((idx, i) => (
              <div key={i} className="bg-base-2 rounded-xl border border-base-4 p-4 hover:shadow-sm transition-all">
                <div className="text-xs text-ink-muted mb-1">{idx.name}</div>
                <div className="text-xl font-bold text-ink-primary">
                  {idx.value ? idx.value.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) : '--'}
                </div>
                <div className={`flex items-center gap-1 text-sm font-medium mt-1
                  ${(idx.change || 0) >= 0 ? 'text-red-500' : 'text-green-500'}`}>
                  {(idx.change || 0) >= 0 ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                  {idx.change != null ? `${idx.change > 0 ? '+' : ''}${idx.change.toFixed(2)}%` : '--'}
                  <span className="text-xs ml-1">{idx.change_amt ? `${idx.change_amt > 0 ? '+' : ''}${idx.change_amt.toFixed(2)}` : ''}</span>
                </div>
              </div>
            ))}
          </div>

          {/* 市场统计 */}
          {Object.keys(stats).length > 0 && (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
              <div className="bg-base-2 rounded-xl border border-base-4 p-3 text-center">
                <div className="text-xs text-ink-muted mb-1">上涨家数</div>
                <div className="text-lg font-bold text-red-500">{stats.up_count}</div>
              </div>
              <div className="bg-base-2 rounded-xl border border-base-4 p-3 text-center">
                <div className="text-xs text-ink-muted mb-1">下跌家数</div>
                <div className="text-lg font-bold text-green-500">{stats.down_count}</div>
              </div>
              <div className="bg-base-2 rounded-xl border border-base-4 p-3 text-center">
                <div className="text-xs text-ink-muted mb-1">成交额</div>
                <div className="text-lg font-bold text-ink-primary">{stats.total_amount_yi ? `${(stats.total_amount_yi / 10000).toFixed(2)}万亿` : '--'}</div>
              </div>
              <div className="bg-base-2 rounded-xl border border-base-4 p-3 text-center">
                <div className="text-xs text-ink-muted mb-1">上涨比例</div>
                <div className="text-lg font-bold text-ink-primary">{stats.up_ratio}%</div>
              </div>
              <div className="bg-base-2 rounded-xl border border-base-4 p-3 text-center">
                <div className="text-xs text-ink-muted mb-1">北向资金</div>
                <div className={`text-lg font-bold ${(nf.net_flow || 0) >= 0 ? 'text-red-500' : 'text-green-500'}`}>
                  {nf.net_flow ? `${nf.net_flow > 0 ? '+' : ''}${nf.net_flow.toFixed(1)}亿` : '--'}
                </div>
              </div>
            </div>
          )}

          {/* Tab 切换 */}
          <div className="flex gap-1 bg-base-3 rounded-xl p-1 mb-6">
            {tabs.map(tab => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all flex-1 justify-center
                    ${activeTab === tab.id ? 'bg-base-2 text-primary-700 shadow-card' : 'text-ink-muted hover:text-ink-secondary'}`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              )
            })}
          </div>

          {/* Tab: 市场概览 */}  
          {activeTab === 'overview' && (
            <div className="grid md:grid-cols-2 gap-6">
              {/* 领涨板块 */}
              <div className="bg-base-2 rounded-2xl border border-base-4 shadow-card p-5">
                <h3 className="font-semibold text-ink-primary mb-3 flex items-center gap-2">
                  <Flame className="w-4 h-4 text-red-500" /> 领涨板块
                </h3>
                <div className="space-y-3">
                  {(overview?.top_sectors || []).map((s, i) => (
                    <div key={i} className="flex items-center justify-between">
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        <span className="text-xs text-ink-muted w-5">{i + 1}</span>
                        <span className="text-sm text-ink-secondary truncate">{s.name}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-ink-muted">领涨: {s.leader || '--'}</span>
                        <span className="text-sm font-semibold text-red-500 w-16 text-right">+{s.change_pct?.toFixed(1)}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* 领跌板块 */}
              <div className="bg-base-2 rounded-2xl border border-base-4 shadow-card p-5">
                <h3 className="font-semibold text-ink-primary mb-3 flex items-center gap-2">
                  <Snowflake className="w-4 h-4 text-green-500" /> 领跌板块
                </h3>
                <div className="space-y-3">
                  {(overview?.bottom_sectors || []).map((s, i) => (
                    <div key={i} className="flex items-center justify-between">
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        <span className="text-xs text-ink-muted w-5">{i + 1}</span>
                        <span className="text-sm text-ink-secondary truncate">{s.name}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-ink-muted">领跌: {s.leader || '--'}</span>
                        <span className="text-sm font-semibold text-green-500 w-16 text-right">{s.change_pct?.toFixed(1)}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Tab: 概念异动 */}
          {activeTab === 'sectors' && (
            <div className="bg-base-2 rounded-2xl border border-base-4 shadow-card overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="bg-base-2 text-xs text-ink-muted">
                      <th className="text-left px-4 py-3 font-medium">概念板块</th>
                      <th className="text-right px-4 py-3 font-medium">涨跌幅</th>
                      <th className="text-right px-4 py-3 font-medium hidden md:table-cell">上涨</th>
                      <th className="text-right px-4 py-3 font-medium hidden md:table-cell">下跌</th>
                      <th className="text-right px-4 py-3 font-medium hidden sm:table-cell">领涨股</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-base-4">
                    {concepts.map((c, i) => (
                      <tr key={i} className="hover:bg-base-3 transition-colors">
                        <td className="px-4 py-3">
                          <span className="text-sm font-medium text-ink-primary">{c.name}</span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <span className={`text-sm font-semibold ${c.change_pct >= 0 ? 'text-red-500' : 'text-green-500'}`}>
                            {c.change_pct > 0 ? '+' : ''}{c.change_pct.toFixed(1)}%
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right text-sm text-ink-secondary hidden md:table-cell">{c.up_count}</td>
                        <td className="px-4 py-3 text-right text-sm text-ink-secondary hidden md:table-cell">{c.down_count}</td>
                        <td className="px-4 py-3 text-right text-sm text-ink-muted hidden sm:table-cell">{c.leader || '--'}</td>
                      </tr>
                    ))}
                    {concepts.length === 0 && (
                      <tr>
                        <td colSpan={5} className="px-4 py-8 text-center text-ink-muted">暂无数据</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab: 事件提醒 */}
          {activeTab === 'events' && (
            <div className="space-y-3">
              {events.length === 0 ? (
                <div className="bg-base-2 rounded-2xl border border-base-4 p-8 text-center text-ink-muted">
                  <Calendar className="w-10 h-10 mx-auto mb-2" />
                  今日暂无重要事件提醒
                </div>
              ) : (
                events.map((ev, i) => (
                  <div key={i} className="bg-base-2 rounded-xl border border-base-4 p-4 hover:shadow-sm transition-all">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0
                          ${ev.type === '财报' ? 'bg-primary-50 text-primary-600' :
                            ev.type === '解禁' ? 'bg-primary-50 text-primary-600' :
                            ev.type === '分红' ? 'bg-emerald-50 text-emerald-600' :
                            'bg-base-2 text-ink-secondary'}`}>
                          <DollarSign className="w-4 h-4" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-base-3 text-ink-secondary">
                              {ev.type}
                            </span>
                            <span className="text-sm font-semibold text-ink-primary">
                              {ev.name} ({ev.code})
                            </span>
                          </div>
                          <p className="text-sm text-ink-muted mt-1">{ev.title}</p>
                          {ev.detail && <p className="text-xs text-ink-muted mt-0.5">{ev.detail}</p>}
                        </div>
                      </div>
                      <span className="text-xs text-ink-muted shrink-0">{ev.date}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
