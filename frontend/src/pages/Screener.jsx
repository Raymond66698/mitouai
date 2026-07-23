import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Filter, X, ArrowUpDown, TrendingUp, TrendingDown, Loader2, Sparkles, SlidersHorizontal, Star, Zap, BarChart3 } from 'lucide-react'

export default function Screener() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState([])
  const [total, setTotal] = useState(0)
  const [totalScanned, setTotalScanned] = useState(0)
  const [parsedConditions, setParsedConditions] = useState(null)
  const [showFilters, setShowFilters] = useState(false)
  const [sortBy, setSortBy] = useState('score')
  const [sortDir, setSortDir] = useState('desc')

  // 高级筛选条件
  const [filters, setFilters] = useState({
    min_pe: '', max_pe: '', min_pb: '', max_pb: '',
    min_mv: '', max_mv: '', min_turnover: '',
    sector: '', exclude_st: true,
  })

  const [conditionsHelp, setConditionsHelp] = useState(null)

  useEffect(() => {
    fetch('/api/screener/conditions')
      .then(r => r.json())
      .then(d => setConditionsHelp(d))
      .catch(() => {})
  }, [])

  const handleSearch = async () => {
    if (!query.trim()) return
    setLoading(true)
    try {
      const r = await fetch(`/api/screener/search?q=${encodeURIComponent(query.trim())}&top_n=30`)
      const data = await r.json()
      setResults(data.results || [])
      setTotal(data.total || 0)
      setTotalScanned(data.total_scanned || 0)
      setParsedConditions(data.parsed_conditions || null)
    } catch (e) {
      console.error('搜索失败', e)
    }
    setLoading(false)
  }

  const handleFilterSearch = async () => {
    setLoading(true)
    try {
      const conditions = {}
      Object.entries(filters).forEach(([k, v]) => {
        if (v !== '' && v !== false) conditions[k] = k === 'sector' ? v : parseFloat(v)
        if (k === 'exclude_st' && v) conditions[k] = true
      })
      conditions.sort_by = sortBy

      const r = await fetch('/api/screener/filter', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(conditions),
      })
      const data = await r.json()
      setResults(data.results || [])
      setTotal(data.total || 0)
      setTotalScanned(data.total_scanned || 0)
      setParsedConditions(conditions)
    } catch (e) {
      console.error('筛选失败', e)
    }
    setLoading(false)
  }

  const handleStrategy = async (strategyId) => {
    setLoading(true)
    try {
      const r = await fetch(`/api/screener/strategy/${strategyId}?top_n=30`)
      const data = await r.json()
      setResults(data.results || [])
      setTotal(data.total || 0)
      setTotalScanned(data.total_scanned || 0)
      setParsedConditions({ strategy_id: strategyId })
    } catch (e) {
      console.error('策略选股失败', e)
    }
    setLoading(false)
  }

  const sortedResults = [...results].sort((a, b) => {
    const mul = sortDir === 'desc' ? -1 : 1
    if (sortBy === 'score') return ((b.score || 0) - (a.score || 0)) * mul * -1
    if (sortBy === 'change_pct') return ((b.change_pct || 0) - (a.change_pct || 0)) * mul * -1
    if (sortBy === 'pe') return ((a.pe || 9999) - (b.pe || 9999)) * mul * -1
    if (sortBy === 'mv') return ((b.total_mv || 0) - (a.total_mv || 0)) * mul * -1
    return 0
  })

  const toggleSort = (field) => {
    if (sortBy === field) setSortDir(d => d === 'desc' ? 'asc' : 'desc')
    else { setSortBy(field); setSortDir('desc') }
  }

  const formatMV = (mv) => {
    if (!mv) return '--'
    const yi = mv / 1e8
    if (yi >= 10000) return `${(yi/10000).toFixed(1)}万亿`
    return `${yi.toFixed(0)}亿`
  }

  const formatPE = (pe) => {
    if (!pe || pe <= 0) return '--'
    return pe.toFixed(1)
  }

  const quickStrategies = [
    { id: 'buffett-value', name: '巴菲特', icon: '🏛️', color: 'bg-primary-50 text-primary-700 border-primary-200' },
    { id: 'graham-value', name: '格雷厄姆', icon: '🕯️', color: 'bg-primary-50 text-primary-700 border-primary-200' },
    { id: 'value-factor', name: '价值因子', icon: '💎', color: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
    { id: 'quality-factor', name: '质量因子', icon: '⭐', color: 'bg-purple-50 text-purple-700 border-purple-200' },
    { id: 'momentum-factor', name: '动量因子', icon: '🚀', color: 'bg-red-50 text-red-700 border-red-200' },
    { id: 'lowvol-factor', name: '低波动', icon: '🛡️', color: 'bg-base-2 text-ink-secondary border-base-4' },
  ]

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-ink-primary">智能选股器</h1>
        <p className="text-ink-muted mt-1">多因子筛选 + AI自然语言选股，全市场5000+标的秒级筛选</p>
      </div>

      {/* 搜索栏 */}
      <div className="bg-base-2 rounded-2xl border border-base-4 shadow-card p-4 mb-6">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-ink-muted" />
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
              placeholder="用自然语言描述选股条件（如：PE小于20且ROE大于15%的白酒股）"
              className="w-full pl-12 pr-4 py-3.5 border-2 border-base-4 rounded-xl focus:border-primary-400 outline-none text-base transition-all"
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={loading}
            className="px-6 py-3.5 bg-primary-600 text-white rounded-xl font-semibold hover:bg-primary-700 transition-all flex items-center gap-2 shrink-0 disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Sparkles className="w-5 h-5" />}
            AI选股
          </button>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`px-4 py-3.5 rounded-xl font-medium flex items-center gap-2 transition-all shrink-0
              ${showFilters ? 'bg-primary-50 text-primary-700 border border-primary-200' : 'bg-base-2 text-ink-secondary border border-base-4 hover:bg-base-3'}`}
          >
            <SlidersHorizontal className="w-5 h-5" />
            高级筛选
          </button>
        </div>

        {/* 快捷策略 */}
        <div className="flex gap-2 mt-3 flex-wrap">
          {quickStrategies.map(s => (
            <button
              key={s.id}
              onClick={() => handleStrategy(s.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all hover:shadow-sm ${s.color}`}
            >
              <span>{s.icon}</span> {s.name}
            </button>
          ))}
        </div>
      </div>

      {/* 高级筛选面板 */}
      {showFilters && (
        <div className="bg-base-2 rounded-2xl border border-base-4 shadow-card p-5 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-ink-primary flex items-center gap-2">
              <Filter className="w-4 h-4" /> 高级筛选条件
            </h3>
            <button onClick={() => setFilters({ min_pe:'',max_pe:'',min_pb:'',max_pb:'',min_mv:'',max_mv:'',min_turnover:'',sector:'',exclude_st:true })}
              className="text-xs text-ink-muted hover:text-ink-secondary">重置</button>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            <div>
              <label className="block text-xs text-ink-muted mb-1">市盈率 PE (最低)</label>
              <input type="number" value={filters.min_pe} onChange={e => setFilters({...filters, min_pe: e.target.value})}
                placeholder="如 5" className="w-full px-3 py-2 border border-base-4 rounded-lg text-sm focus:border-primary-400 outline-none" />
            </div>
            <div>
              <label className="block text-xs text-ink-muted mb-1">市盈率 PE (最高)</label>
              <input type="number" value={filters.max_pe} onChange={e => setFilters({...filters, max_pe: e.target.value})}
                placeholder="如 25" className="w-full px-3 py-2 border border-base-4 rounded-lg text-sm focus:border-primary-400 outline-none" />
            </div>
            <div>
              <label className="block text-xs text-ink-muted mb-1">市净率 PB (最低)</label>
              <input type="number" value={filters.min_pb} onChange={e => setFilters({...filters, min_pb: e.target.value})}
                placeholder="如 0.5" className="w-full px-3 py-2 border border-base-4 rounded-lg text-sm focus:border-primary-400 outline-none" />
            </div>
            <div>
              <label className="block text-xs text-ink-muted mb-1">市净率 PB (最高)</label>
              <input type="number" value={filters.max_pb} onChange={e => setFilters({...filters, max_pb: e.target.value})}
                placeholder="如 5" className="w-full px-3 py-2 border border-base-4 rounded-lg text-sm focus:border-primary-400 outline-none" />
            </div>
            <div>
              <label className="block text-xs text-ink-muted mb-1">最低市值 (亿)</label>
              <input type="number" value={filters.min_mv} onChange={e => setFilters({...filters, min_mv: e.target.value})}
                placeholder="如 100" className="w-full px-3 py-2 border border-base-4 rounded-lg text-sm focus:border-primary-400 outline-none" />
            </div>
            <div>
              <label className="block text-xs text-ink-muted mb-1">最高市值 (亿)</label>
              <input type="number" value={filters.max_mv} onChange={e => setFilters({...filters, max_mv: e.target.value})}
                placeholder="如 1000" className="w-full px-3 py-2 border border-base-4 rounded-lg text-sm focus:border-primary-400 outline-none" />
            </div>
            <div>
              <label className="block text-xs text-ink-muted mb-1">最低换手率 (%)</label>
              <input type="number" value={filters.min_turnover} onChange={e => setFilters({...filters, min_turnover: e.target.value})}
                placeholder="如 1" className="w-full px-3 py-2 border border-base-4 rounded-lg text-sm focus:border-primary-400 outline-none" />
            </div>
            <div>
              <label className="block text-xs text-ink-muted mb-1">行业关键词</label>
              <input type="text" value={filters.sector} onChange={e => setFilters({...filters, sector: e.target.value})}
                placeholder="如 医药/白酒" className="w-full px-3 py-2 border border-base-4 rounded-lg text-sm focus:border-primary-400 outline-none" />
            </div>
          </div>
          <div className="flex items-center justify-between">
            <label className="flex items-center gap-2 text-sm text-ink-secondary">
              <input type="checkbox" checked={filters.exclude_st}
                onChange={e => setFilters({...filters, exclude_st: e.target.checked})}
                className="rounded border-base-4 text-primary-600" />
              排除 ST 股票
            </label>
            <button onClick={handleFilterSearch} disabled={loading}
              className="px-5 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition-all disabled:opacity-50 flex items-center gap-2">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
              开始筛选
            </button>
          </div>
        </div>
      )}

      {/* 解析后的条件提示 */}
      {parsedConditions && Object.keys(parsedConditions).length > 0 && (
        <div className="flex items-center gap-2 mb-4 flex-wrap">
          <span className="text-xs text-ink-muted">筛选条件：</span>
          {Object.entries(parsedConditions).filter(([k]) => k !== 'sort_by' && k !== 'exclude_st' && k !== 'nl_query').map(([k, v]) => (
            <span key={k} className="px-2 py-0.5 bg-primary-50 text-primary-700 rounded-full text-xs">
              {k}: {typeof v === 'number' ? v.toFixed(1) : v}
            </span>
          ))}
          {parsedConditions.exclude_st && (
            <span className="px-2 py-0.5 bg-primary-50 text-primary-700 rounded-full text-xs">排除ST</span>
          )}
          {totalScanned > 0 && (
            <span className="text-xs text-ink-muted ml-2">
              从 {totalScanned.toLocaleString()} 只股票中筛选出 {total} 只
            </span>
          )}
        </div>
      )}

      {/* 结果表格 */}
      {results.length > 0 && (
        <div className="bg-base-2 rounded-2xl border border-base-4 shadow-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-base-4 bg-base-2">
                  <th className="text-left px-4 py-3 text-xs font-medium text-ink-muted uppercase">#</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-ink-muted uppercase">股票</th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-ink-muted uppercase cursor-pointer hover:text-primary-600"
                    onClick={() => toggleSort('score')}>
                    <span className="flex items-center justify-end gap-1">
                      评分 {sortBy === 'score' && <ArrowUpDown className="w-3 h-3" />}
                    </span>
                  </th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-ink-muted uppercase">最新价</th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-ink-muted uppercase cursor-pointer hover:text-primary-600"
                    onClick={() => toggleSort('change_pct')}>
                    <span className="flex items-center justify-end gap-1">
                      涨跌幅 {sortBy === 'change_pct' && <ArrowUpDown className="w-3 h-3" />}
                    </span>
                  </th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-ink-muted uppercase cursor-pointer hover:text-primary-600"
                    onClick={() => toggleSort('pe')}>
                    <span className="flex items-center justify-end gap-1">
                      PE {sortBy === 'pe' && <ArrowUpDown className="w-3 h-3" />}
                    </span>
                  </th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-ink-muted uppercase">PB</th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-ink-muted uppercase cursor-pointer hover:text-primary-600"
                    onClick={() => toggleSort('mv')}>
                    <span className="flex items-center justify-end gap-1">
                      市值 {sortBy === 'mv' && <ArrowUpDown className="w-3 h-3" />}
                    </span>
                  </th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-ink-muted uppercase">换手率</th>
                  <th className="text-center px-4 py-3 text-xs font-medium text-ink-muted uppercase">操作</th>
                </tr>
              </thead>
              <tbody>
                {sortedResults.map((stock, i) => {
                  const code = stock.code
                  const suffix = code && code.length >= 3 ? code.slice(-3) : ''
                  return (
                    <tr key={code} className="border-b border-gray-50 hover:bg-base-3 transition-colors">
                      <td className="px-4 py-3">
                        <span className="text-xs font-semibold text-ink-muted">{i + 1}</span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-7 h-7 bg-gradient-to-br from-primary-100 to-purple-100 rounded-lg flex items-center justify-center text-xs font-bold text-primary-600">
                            {stock.name?.[0]}
                          </div>
                          <div>
                            <div className="font-medium text-sm text-ink-primary">{stock.name}</div>
                            <div className="text-xs text-ink-muted">{code}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-1">
                          <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
                          <span className="font-semibold text-sm text-ink-secondary">{stock.score || '--'}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span className="text-sm font-medium text-ink-primary">
                          {stock.price ? stock.price.toFixed(2) : '--'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span className={`inline-flex items-center gap-1 text-sm font-medium
                          ${(stock.change_pct || 0) >= 0 ? 'text-red-500' : 'text-green-500'}`}>
                          {(stock.change_pct || 0) >= 0 ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                          {stock.change_pct != null ? `${stock.change_pct > 0 ? '+' : ''}${stock.change_pct.toFixed(2)}%` : '--'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span className="text-sm text-ink-secondary">{formatPE(stock.pe)}</span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span className="text-sm text-ink-secondary">
                          {stock.pb && stock.pb > 0 ? stock.pb.toFixed(1) : '--'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span className="text-sm text-ink-secondary">{formatMV(stock.total_mv)}</span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span className="text-sm text-ink-secondary">
                          {stock.turnover ? `${stock.turnover.toFixed(2)}%` : '--'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <button
                          onClick={() => navigate(`/analysis?q=${stock.name}`)}
                          className="px-3 py-1.5 text-xs bg-primary-50 text-primary-700 rounded-lg hover:bg-primary-100 transition-colors font-medium"
                        >
                          分析
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          {total > 30 && (
            <div className="px-4 py-3 text-center text-sm text-ink-muted bg-base-2 border-t border-base-4">
              显示前30条，共 {total} 条结果
            </div>
          )}
        </div>
      )}

      {/* 空状态 */}
      {!loading && results.length === 0 && (
        <div className="text-center py-20">
          <div className="w-20 h-20 bg-base-3 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Search className="w-10 h-10 text-ink-muted" />
          </div>
          <h3 className="text-lg font-medium text-ink-muted mb-2">输入条件开始选股</h3>
          <p className="text-sm text-ink-muted max-w-md mx-auto">
            支持自然语言描述，或使用高级筛选精确设置条件。
          </p>
          {conditionsHelp?.examples && (
            <div className="mt-4 flex flex-wrap gap-2 justify-center">
              {conditionsHelp.examples.slice(0, 4).map((ex, i) => (
                <button key={i} onClick={() => { setQuery(ex); handleSearch() }}
                  className="px-3 py-1.5 text-xs bg-base-2 text-ink-secondary rounded-full hover:bg-primary-50 hover:text-primary-600 transition-colors border border-base-4">
                  {ex}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 加载 */}
      {loading && (
        <div className="text-center py-20">
          <Loader2 className="w-10 h-10 text-primary-500 animate-spin mx-auto mb-4" />
          <p className="text-ink-muted">正在扫描全市场股票...</p>
          <p className="text-xs text-ink-muted mt-1">大约需要 5-10 秒</p>
        </div>
      )}
    </div>
  )
}
