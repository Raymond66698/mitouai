import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Filter, ArrowUpDown, TrendingUp, TrendingDown, Loader2, Sparkles, SlidersHorizontal, Star, BarChart3, AlertCircle } from 'lucide-react'

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
    { id: 'buffett-value', name: '巴菲特', icon: '🏛️', color: '#C8963E' },
    { id: 'graham-value', name: '格雷厄姆', icon: '🕯️', color: '#C8963E' },
    { id: 'value-factor', name: '价值因子', icon: '💎', color: '#059669' },
    { id: 'quality-factor', name: '质量因子', icon: '⭐', color: '#7C3AED' },
    { id: 'momentum-factor', name: '动量因子', icon: '🚀', color: '#DC2626' },
    { id: 'lowvol-factor', name: '低波动', icon: '🛡️', color: '#0891B2' },
  ]

  const inputStyle = {
    background: '#FFFFFF',
    border: '1px solid #F0E6D3',
    color: '#1A1A2E',
  }

  return (
    <div className="animate-in">
      {/* ── 页头 ── */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center text-white shadow-lg"
            style={{ background: 'linear-gradient(135deg, #C8963E, #E8A817)', boxShadow: '0 4px 12px rgba(200,150,62,0.3)' }}>
            <Search className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-2xl font-bold" style={{ color: '#1A1A2E' }}>智能选股器</h1>
            <p className="text-sm" style={{ color: '#A09080' }}>多因子筛选 + AI自然语言选股，全市场5000+标的秒级筛选</p>
          </div>
        </div>
        {/* 合规声明 */}
        <div className="flex items-start gap-2 px-4 py-2.5 rounded-lg" style={{ background: 'rgba(196,30,58,0.04)', border: '1px solid rgba(196,30,58,0.1)' }}>
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" style={{ color: '#C41E3A' }} />
          <span className="text-xs" style={{ color: '#A3152E' }}>
            本工具仅用于金融知识教育展示，筛选结果不构成投资建议。市场有风险，投资需谨慎。
          </span>
        </div>
      </div>

      {/* ── 搜索栏 ── */}
      <div className="card p-4 mb-6">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5" style={{ color: '#A09080' }} />
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
              placeholder="用自然语言描述选股条件（如：PE小于20且ROE大于15%的白酒股）"
              className="w-full pl-12 pr-4 py-3.5 rounded-xl outline-none text-base transition-all"
              style={inputStyle}
              onFocus={e => { e.target.style.borderColor = '#C8963E'; e.target.style.boxShadow = '0 0 0 3px rgba(200,150,62,0.1)' }}
              onBlur={e => { e.target.style.borderColor = '#F0E6D3'; e.target.style.boxShadow = 'none' }}
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={loading}
            className="btn-primary text-sm font-semibold flex items-center gap-2 shrink-0 disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Sparkles className="w-5 h-5" />}
            AI选股
          </button>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="px-4 py-3.5 rounded-xl font-medium flex items-center gap-2 transition-all shrink-0"
            style={showFilters
              ? { background: 'rgba(200,150,62,0.12)', color: '#C8963E', border: '1px solid rgba(200,150,62,0.3)' }
              : { background: '#FFFFFF', color: '#6B5B4E', border: '1px solid #F0E6D3' }}
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
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all hover:shadow-sm"
              style={{ background: `${s.color}10`, color: s.color, borderColor: `${s.color}30` }}
            >
              <span>{s.icon}</span> {s.name}
            </button>
          ))}
        </div>
      </div>

      {/* ── 高级筛选面板 ── */}
      {showFilters && (
        <div className="card p-5 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold flex items-center gap-2" style={{ color: '#1A1A2E' }}>
              <Filter className="w-4 h-4" style={{ color: '#C8963E' }} /> 高级筛选条件
            </h3>
            <button onClick={() => setFilters({ min_pe:'',max_pe:'',min_pb:'',max_pb:'',min_mv:'',max_mv:'',min_turnover:'',sector:'',exclude_st:true })}
              className="text-xs transition-colors" style={{ color: '#A09080' }}>重置</button>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            {[
              { key: 'min_pe', label: '市盈率 PE (最低)', placeholder: '如 5' },
              { key: 'max_pe', label: '市盈率 PE (最高)', placeholder: '如 25' },
              { key: 'min_pb', label: '市净率 PB (最低)', placeholder: '如 0.5' },
              { key: 'max_pb', label: '市净率 PB (最高)', placeholder: '如 5' },
              { key: 'min_mv', label: '最低市值 (亿)', placeholder: '如 100' },
              { key: 'max_mv', label: '最高市值 (亿)', placeholder: '如 1000' },
              { key: 'min_turnover', label: '最低换手率 (%)', placeholder: '如 1' },
              { key: 'sector', label: '行业关键词', placeholder: '如 医药/白酒' },
            ].map(f => (
              <div key={f.key}>
                <label className="block text-xs mb-1" style={{ color: '#A09080' }}>{f.label}</label>
                <input
                  type={f.key === 'sector' ? 'text' : 'number'}
                  value={filters[f.key]}
                  onChange={e => setFilters({...filters, [f.key]: e.target.value})}
                  placeholder={f.placeholder}
                  className="w-full px-3 py-2 rounded-lg text-sm outline-none transition-all"
                  style={inputStyle}
                  onFocus={e => e.target.style.borderColor = '#C8963E'}
                  onBlur={e => e.target.style.borderColor = '#F0E6D3'}
                />
              </div>
            ))}
          </div>
          <div className="flex items-center justify-between">
            <label className="flex items-center gap-2 text-sm" style={{ color: '#6B5B4E' }}>
              <input type="checkbox" checked={filters.exclude_st}
                onChange={e => setFilters({...filters, exclude_st: e.target.checked})}
                className="rounded" style={{ accentColor: '#C8963E' }} />
              排除 ST 股票
            </label>
            <button onClick={handleFilterSearch} disabled={loading}
              className="btn-primary text-sm font-medium flex items-center gap-2 disabled:opacity-50">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
              开始筛选
            </button>
          </div>
        </div>
      )}

      {/* ── 筛选条件提示 ── */}
      {parsedConditions && Object.keys(parsedConditions).length > 0 && (
        <div className="flex items-center gap-2 mb-4 flex-wrap">
          <span className="text-xs" style={{ color: '#A09080' }}>筛选条件：</span>
          {Object.entries(parsedConditions).filter(([k]) => k !== 'sort_by' && k !== 'exclude_st' && k !== 'nl_query' && k !== 'strategy_id').map(([k, v]) => (
            <span key={k} className="px-2 py-0.5 rounded-full text-xs"
              style={{ background: 'rgba(200,150,62,0.08)', color: '#C8963E' }}>
              {k}: {typeof v === 'number' ? v.toFixed(1) : v}
            </span>
          ))}
          {parsedConditions.exclude_st && (
            <span className="px-2 py-0.5 rounded-full text-xs"
              style={{ background: 'rgba(200,150,62,0.08)', color: '#C8963E' }}>排除ST</span>
          )}
          {parsedConditions.strategy_id && (
            <span className="px-2 py-0.5 rounded-full text-xs"
              style={{ background: 'rgba(196,30,58,0.08)', color: '#C41E3A' }}>策略: {parsedConditions.strategy_id}</span>
          )}
          {totalScanned > 0 && (
            <span className="text-xs ml-2" style={{ color: '#A09080' }}>
              从 {totalScanned.toLocaleString()} 只股票中筛选出 {total} 只
            </span>
          )}
        </div>
      )}

      {/* ── 结果表格 ── */}
      {results.length > 0 && (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr style={{ borderBottom: '1px solid #F0E6D3' }}>
                  {[
                    { label: '#', align: 'left', sortable: false },
                    { label: '股票', align: 'left', sortable: false },
                    { label: '评分', align: 'right', sortable: true, field: 'score' },
                    { label: '最新价', align: 'right', sortable: false },
                    { label: '涨跌幅', align: 'right', sortable: true, field: 'change_pct' },
                    { label: 'PE', align: 'right', sortable: true, field: 'pe' },
                    { label: 'PB', align: 'right', sortable: false },
                    { label: '市值', align: 'right', sortable: true, field: 'mv' },
                    { label: '换手率', align: 'right', sortable: false },
                    { label: '操作', align: 'center', sortable: false },
                  ].map((col, i) => (
                    <th key={i}
                      className={`px-4 py-3 text-xs font-medium uppercase cursor-${col.sortable ? 'pointer' : 'default'}`}
                      style={{ color: '#A09080', textAlign: col.align }}
                      onClick={() => col.sortable && toggleSort(col.field)}>
                      {col.sortable ? (
                        <span className="flex items-center justify-end gap-1 transition-colors hover:text-amber-600">
                          {col.label} {sortBy === col.field && <ArrowUpDown className="w-3 h-3" />}
                        </span>
                      ) : col.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sortedResults.map((stock, i) => (
                  <tr key={stock.code} className="transition-colors"
                    style={{ borderBottom: '1px solid #FFF8EE' }}
                    onMouseEnter={e => e.currentTarget.style.background = '#FFF8EE'}
                    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                    <td className="px-4 py-3">
                      <span className="text-xs font-semibold" style={{ color: '#A09080' }}>{i + 1}</span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold"
                          style={{ background: 'rgba(200,150,62,0.1)', color: '#C8963E' }}>
                          {stock.name?.[0]}
                        </div>
                        <div>
                          <div className="font-medium text-sm" style={{ color: '#1A1A2E' }}>{stock.name}</div>
                          <div className="text-xs font-mono" style={{ color: '#A09080' }}>{stock.code}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Star className="w-3.5 h-3.5" style={{ color: '#E8A817', fill: '#E8A817' }} />
                        <span className="font-semibold text-sm num" style={{ color: '#6B5B4E' }}>{stock.score || '--'}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="text-sm font-medium num" style={{ color: '#1A1A2E' }}>
                        {stock.price ? stock.price.toFixed(2) : '--'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="inline-flex items-center gap-1 text-sm font-medium num"
                        style={{ color: (stock.change_pct || 0) >= 0 ? '#DC2626' : '#059669' }}>
                        {(stock.change_pct || 0) >= 0 ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                        {stock.change_pct != null ? `${stock.change_pct > 0 ? '+' : ''}${stock.change_pct.toFixed(2)}%` : '--'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="text-sm num" style={{ color: '#6B5B4E' }}>{formatPE(stock.pe)}</span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="text-sm num" style={{ color: '#6B5B4E' }}>
                        {stock.pb && stock.pb > 0 ? stock.pb.toFixed(1) : '--'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="text-sm num" style={{ color: '#6B5B4E' }}>{formatMV(stock.total_mv)}</span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="text-sm num" style={{ color: '#6B5B4E' }}>
                        {stock.turnover ? `${stock.turnover.toFixed(2)}%` : '--'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <button
                        onClick={() => navigate(`/analysis?q=${stock.name}`)}
                        className="px-3 py-1.5 text-xs rounded-lg transition-colors font-medium"
                        style={{ background: 'rgba(200,150,62,0.08)', color: '#C8963E' }}
                        onMouseEnter={e => { e.target.style.background = 'rgba(200,150,62,0.15)' }}
                        onMouseLeave={e => { e.target.style.background = 'rgba(200,150,62,0.08)' }}>
                        分析
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {total > 30 && (
            <div className="px-4 py-3 text-center text-sm" style={{ color: '#A09080', borderTop: '1px solid #F0E6D3' }}>
              显示前30条，共 {total} 条结果
            </div>
          )}
        </div>
      )}

      {/* ── 空状态 ── */}
      {!loading && results.length === 0 && (
        <div className="text-center py-20">
          <div className="w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-4"
            style={{ background: '#FFF8EE' }}>
            <Search className="w-10 h-10" style={{ color: '#A09080' }} />
          </div>
          <h3 className="text-lg font-medium mb-2" style={{ color: '#A09080' }}>输入条件开始选股</h3>
          <p className="text-sm max-w-md mx-auto" style={{ color: '#A09080' }}>
            支持自然语言描述，或使用高级筛选精确设置条件。
          </p>
          {conditionsHelp?.examples && (
            <div className="mt-4 flex flex-wrap gap-2 justify-center">
              {conditionsHelp.examples.slice(0, 4).map((ex, i) => (
                <button key={i} onClick={() => { setQuery(ex); handleSearch() }}
                  className="px-3 py-1.5 text-xs rounded-full transition-colors"
                  style={{ background: '#FFFFFF', color: '#6B5B4E', border: '1px solid #F0E6D3' }}
                  onMouseEnter={e => { e.target.style.borderColor = '#C8963E'; e.target.style.color = '#C8963E' }}
                  onMouseLeave={e => { e.target.style.borderColor = '#F0E6D3'; e.target.style.color = '#6B5B4E' }}>
                  {ex}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── 加载 ── */}
      {loading && (
        <div className="text-center py-20">
          <Loader2 className="w-10 h-10 animate-spin mx-auto mb-4" style={{ color: '#C8963E' }} />
          <p style={{ color: '#A09080' }}>正在扫描全市场股票...</p>
          <p className="text-xs mt-1" style={{ color: '#A09080' }}>大约需要 5-10 秒</p>
        </div>
      )}
    </div>
  )
}
