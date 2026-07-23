import { useState, useEffect, useCallback } from 'react'
import {
  FileText, TrendingUp, Target, Loader2, Search, RefreshCw,
  Building2, Users, Award, ExternalLink, ChevronRight, Sparkles,
  AlertCircle, BarChart3,
} from 'lucide-react'

export default function Research() {
  const [loading, setLoading] = useState(true)
  const [ticker, setTicker] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [searching, setSearching] = useState(false)
  const [research, setResearch] = useState(null)
  const [hotReports, setHotReports] = useState([])
  const [chainData, setChainData] = useState(null)
  const [error, setError] = useState('')
  const [tab, setTab] = useState('hot')
  const token = localStorage.getItem('mitouai_token')
  const headers = { Authorization: `Bearer ${token}` }

  // 获取热门研报
  const fetchHotReports = useCallback(async () => {
    try {
      const res = await fetch('/api/research/hot?limit=20', { headers })
      const data = await res.json()
      setHotReports(data.reports || [])
    } catch (e) {
      console.error('fetchHotReports error:', e)
    }
  }, [])

  useEffect(() => {
    fetchHotReports().then(() => setLoading(false))
  }, [fetchHotReports])

  // 搜索股票
  const searchStocks = async (q) => {
    setTicker(q)
    if (q.length < 1) { setSearchResults([]); return }
    setSearching(true)
    try {
      const res = await fetch(`/api/market/search?q=${encodeURIComponent(q)}`, { headers })
      const data = await res.json()
      setSearchResults(data.results || [])
    } catch (e) {}
    setSearching(false)
  }

  // 获取个股研报
  const fetchStockResearch = async (code) => {
    setLoading(true)
    setError('')
    try {
      const [researchRes, chainRes] = await Promise.allSettled([
        fetch(`/api/research/stock/${code}`, { headers }).then(r => r.json()),
        fetch(`/api/research/chain/${code}`, { headers }).then(r => r.json()),
      ])
      if (researchRes.status === 'fulfilled') {
        setResearch(researchRes.value)
        setTab('stock')
      }
      if (chainRes.status === 'fulfilled') {
        setChainData(chainRes.value)
      }
    } catch (e) {
      setError('加载研报失败：' + e.message)
    }
    setLoading(false)
    setSearchResults([])
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-ink-primary flex items-center gap-2">
            <FileText className="w-6 h-6 text-indigo-500" />
            AI研报聚合
          </h1>
          <p className="text-ink-muted mt-1">券商研报摘要 + AI提炼核心观点 + 产业链分析</p>
        </div>
        <button onClick={() => { fetchHotReports(); setResearch(null); setTab('hot') }}
          className="p-2 text-ink-muted hover:text-ink-secondary rounded-lg hover:bg-base-3">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* 搜索框 */}
      <div className="relative mb-6">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-ink-muted" />
        <input
          type="text" value={ticker}
          onChange={e => searchStocks(e.target.value)}
          placeholder="输入股票名称或代码查看研报（如：贵州茅台 / 600519）"
          className="w-full pl-12 pr-4 py-3.5 border-2 border-base-4 rounded-xl focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 outline-none text-base transition-all bg-base-2"
        />
        {searching && <Loader2 className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 animate-spin text-indigo-500" />}
        {searchResults.length > 0 && (
          <div className="absolute z-20 left-0 right-0 top-full mt-1 bg-base-2 rounded-xl border border-base-4 shadow-lg max-h-64 overflow-y-auto">
            {searchResults.map((r, i) => (
              <button
                key={i} onClick={() => fetchStockResearch(r.code)}
                className="w-full flex items-center justify-between px-4 py-3 hover:bg-base-3 transition-colors text-left"
              >
                <div>
                  <span className="text-sm font-medium text-ink-primary">{r.name}</span>
                  <span className="text-xs text-ink-muted ml-2">{r.code}</span>
                </div>
                <ChevronRight className="w-4 h-4 text-ink-muted" />
              </button>
            ))}
          </div>
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
        </div>
      ) : (
        <>
          {/* 个股研报详情 */}
          {research && tab === 'stock' && (
            <div className="space-y-6">
              {/* AI 摘要 */}
              {research.ai_summary && (
                <div className="bg-gradient-to-br from-indigo-50 to-primary-100/30 rounded-2xl border border-indigo-100 p-6">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-xl flex items-center justify-center shrink-0">
                      <Sparkles className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-ink-primary mb-2">AI 研报摘要</h3>
                      <p className="text-ink-secondary leading-relaxed text-sm whitespace-pre-wrap">{research.ai_summary}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* 评级分布 + 一致性预期 */}
              <div className="grid md:grid-cols-2 gap-4">
                {Object.keys(research.ratings_summary || {}).length > 0 && (
                  <div className="bg-base-2 rounded-2xl border border-base-4 shadow-card p-5">
                    <h3 className="font-semibold text-ink-primary mb-3 flex items-center gap-2">
                      <Award className="w-4 h-4 text-amber-500" /> 机构评级分布
                    </h3>
                    <div className="space-y-2">
                      {Object.entries(research.ratings_summary).map(([rating, count], i) => {
                        const total = Object.values(research.ratings_summary).reduce((a, b) => a + b, 0)
                        const pct = total > 0 ? (count / total * 100).toFixed(0) : 0
                        const colors = {
                          '买入': 'bg-red-400', '增持': 'bg-accent-400', '推荐': 'bg-amber-400',
                          '强烈推荐': 'bg-red-500', '优于大市': 'bg-emerald-400',
                          '中性': 'bg-primary-300', '持有': 'bg-primary-400',
                          '减持': 'bg-green-400', '卖出': 'bg-green-500',
                        }
                        return (
                          <div key={i} className="flex items-center gap-3">
                            <span className="text-sm text-ink-secondary w-20">{rating}</span>
                            <div className="flex-1 h-2 bg-base-3 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full ${colors[rating] || 'bg-primary-300'}`}
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                            <span className="text-sm font-semibold text-ink-primary w-10 text-right">{count}</span>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}

                {Object.keys(research.consensus || {}).length > 0 && (
                  <div className="bg-base-2 rounded-2xl border border-base-4 shadow-card p-5">
                    <h3 className="font-semibold text-ink-primary mb-3 flex items-center gap-2">
                      <Target className="w-4 h-4 text-primary-500" /> 一致预期
                    </h3>
                    <div className="space-y-3">
                      {research.consensus.institutions > 0 && (
                        <div className="flex justify-between">
                          <span className="text-sm text-ink-muted">预测机构数</span>
                          <span className="text-sm font-semibold text-ink-primary">{research.consensus.institutions} 家</span>
                        </div>
                      )}
                      {research.consensus.revenue_forecast && (
                        <div className="flex justify-between">
                          <span className="text-sm text-ink-muted">预测营收</span>
                          <span className="text-sm font-semibold text-ink-primary">
                            {(research.consensus.revenue_forecast / 1e8).toFixed(2)} 亿
                          </span>
                        </div>
                      )}
                      {research.consensus.profit_forecast && (
                        <div className="flex justify-between">
                          <span className="text-sm text-ink-muted">预测净利润</span>
                          <span className="text-sm font-semibold text-ink-primary">
                            {(research.consensus.profit_forecast / 1e8).toFixed(2)} 亿
                          </span>
                        </div>
                      )}
                      {research.consensus.eps_forecast && (
                        <div className="flex justify-between">
                          <span className="text-sm text-ink-muted">预测EPS</span>
                          <span className="text-sm font-semibold text-ink-primary">
                            ¥{research.consensus.eps_forecast.toFixed(2)}
                          </span>
                        </div>
                      )}
                      {research.consensus.pe_forecast && (
                        <div className="flex justify-between">
                          <span className="text-sm text-ink-muted">预测PE</span>
                          <span className="text-sm font-semibold text-ink-primary">
                            {research.consensus.pe_forecast.toFixed(1)}x
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* 产业链 */}
              {chainData && (
                <div className="bg-base-2 rounded-2xl border border-base-4 shadow-card p-5">
                  <h3 className="font-semibold text-ink-primary mb-3 flex items-center gap-2">
                    <Building2 className="w-4 h-4 text-emerald-500" /> 产业链分析
                  </h3>
                  {chainData.industry && (
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-sm text-ink-muted">所属行业：</span>
                      <span className="px-3 py-1 bg-emerald-50 text-emerald-700 rounded-full text-sm font-medium">
                        {chainData.industry}
                      </span>
                    </div>
                  )}
                  {chainData.peers && chainData.peers.length > 0 && (
                    <div>
                      <span className="text-sm text-ink-muted mb-2 block">同行业公司：</span>
                      <div className="flex flex-wrap gap-2">
                        {chainData.peers.map((p, i) => (
                          <button
                            key={i}
                            onClick={() => fetchStockResearch(p.code)}
                            className="px-3 py-1.5 bg-base-2 hover:bg-indigo-50 hover:text-indigo-700 rounded-lg text-sm text-ink-secondary transition-colors"
                          >
                            {p.name}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* 研报列表 */}
              <div className="bg-base-2 rounded-2xl border border-base-4 shadow-card overflow-hidden">
                <div className="px-5 py-3 border-b border-base-4 font-semibold text-sm text-ink-primary">
                  券商研报 ({research.reports?.length || 0})
                </div>
                <div className="divide-y divide-base-4">
                  {research.reports?.map((r, i) => (
                    <div key={i} className="px-5 py-4 hover:bg-base-3 transition-colors">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <h4 className="text-sm font-medium text-ink-primary line-clamp-2">{r.title}</h4>
                          <div className="flex items-center gap-2 mt-1.5">
                            <span className="text-xs text-ink-muted flex items-center gap-1">
                              <Building2 className="w-3 h-3" /> {r.org}
                            </span>
                            <span className="text-xs text-ink-muted">·</span>
                            <span className="text-xs text-ink-muted flex items-center gap-1">
                              <Users className="w-3 h-3" /> {r.author}
                            </span>
                            <span className="text-xs text-ink-muted">·</span>
                            <span className="text-xs text-ink-muted">{r.date}</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-3 shrink-0">
                          {r.target_price && (
                            <div className="text-right">
                              <div className="text-xs text-ink-muted">目标价</div>
                              <div className="text-sm font-semibold text-ink-primary">¥{r.target_price.toFixed(2)}</div>
                            </div>
                          )}
                          {r.rating && (
                            <span className={`px-2.5 py-1 rounded-full text-xs font-medium
                              ${['买入', '增持', '推荐', '强烈推荐', '优于大市'].includes(r.rating)
                                ? 'bg-red-50 text-red-600'
                                : ['减持', '卖出'].includes(r.rating)
                                ? 'bg-green-50 text-green-600'
                                : 'bg-base-2 text-ink-secondary'}`}>
                              {r.rating}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                  {(!research.reports || research.reports.length === 0) && (
                    <div className="px-5 py-12 text-center text-ink-muted">暂无该股票研报数据</div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* 热门研报 */}
          {tab === 'hot' && (
            <div className="bg-base-2 rounded-2xl border border-base-4 shadow-card overflow-hidden">
              <div className="px-5 py-3 border-b border-base-4 font-semibold text-sm text-ink-primary flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-indigo-500" /> 最新研报
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="bg-base-2 text-xs text-ink-muted">
                      <th className="text-left px-4 py-3 font-medium">研报标题</th>
                      <th className="text-left px-4 py-3 font-medium hidden md:table-cell">机构</th>
                      <th className="text-left px-4 py-3 font-medium">股票</th>
                      <th className="text-center px-4 py-3 font-medium">评级</th>
                      <th className="text-right px-4 py-3 font-medium hidden sm:table-cell">目标价</th>
                      <th className="text-right px-4 py-3 font-medium hidden md:table-cell">日期</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-base-4">
                    {hotReports.map((r, i) => (
                      <tr key={i} className="hover:bg-base-3 transition-colors cursor-pointer"
                        onClick={() => r.code && fetchStockResearch(r.code)}>
                        <td className="px-4 py-3">
                          <div className="text-sm text-ink-primary line-clamp-1 max-w-xs">{r.title}</div>
                        </td>
                        <td className="px-4 py-3 text-sm text-ink-muted hidden md:table-cell">{r.org}</td>
                        <td className="px-4 py-3">
                          <span className="text-sm font-medium text-ink-primary">{r.name}</span>
                          <span className="text-xs text-ink-muted ml-1">{r.code}</span>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium
                            ${['买入', '增持', '推荐', '强烈推荐'].includes(r.rating)
                              ? 'bg-red-50 text-red-600'
                              : ['减持', '卖出'].includes(r.rating)
                              ? 'bg-green-50 text-green-600'
                              : 'bg-base-2 text-ink-secondary'}`}>
                            {r.rating || '--'}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right text-sm text-ink-secondary hidden sm:table-cell">
                          {r.target_price ? `¥${r.target_price.toFixed(2)}` : '--'}
                        </td>
                        <td className="px-4 py-3 text-right text-xs text-ink-muted hidden md:table-cell">{r.date}</td>
                      </tr>
                    ))}
                    {hotReports.length === 0 && (
                      <tr>
                        <td colSpan={6} className="px-4 py-12 text-center text-ink-muted">暂无研报数据</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
