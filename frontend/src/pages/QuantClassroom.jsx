import { useState, useEffect, useMemo, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  BookOpen, Sigma, TrendingUp, Activity, BarChart3, Layers,
  GitCompare, Search, ChevronRight, X, Loader2, Calculator,
  GraduationCap, Database, RefreshCw, AlertCircle, Lightbulb,
  ArrowRight, Hash
} from 'lucide-react'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, Title, Tooltip, Legend, Filler
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

const API_BASE = import.meta.env.VITE_API_URL || '/api'

// ── 因子类别图标映射 ──
const CATEGORY_ICONS = {
  price: Sigma,
  momentum: TrendingUp,
  trend: Activity,
  volatility: BarChart3,
  quantile: Layers,
  rank: Hash,
  correlation: GitCompare,
  volume: Database,
}

const CATEGORY_COLORS = {
  price: '#C8963E',
  momentum: '#C41E3A',
  trend: '#7C3AED',
  volatility: '#0891B2',
  quantile: '#059669',
  rank: '#D97706',
  correlation: '#DB2777',
  volume: '#2563EB',
}

export default function QuantClassroom() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [categories, setCategories] = useState({})
  const [factors, setFactors] = useState([])
  const [allFactors, setAllFactors] = useState([])
  const [activeCategory, setActiveCategory] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedFactor, setSelectedFactor] = useState(null)
  const [classroomData, setClassroomData] = useState(null)
  const [classroomLoading, setClassroomLoading] = useState(false)
  const [dataStatus, setDataStatus] = useState(null)

  // 因子计算
  const [calcTicker, setCalcTicker] = useState('600519.SS')
  const [calcResult, setCalcResult] = useState(null)
  const [calcLoading, setCalcLoading] = useState(false)
  const [calcError, setCalcError] = useState('')

  // 多股对比
  const [compareTickers, setCompareTickers] = useState('600519.SS,000001.SZ')
  const [compareFactor, setCompareFactor] = useState('RSV5')
  const [compareResult, setCompareResult] = useState(null)
  const [compareLoading, setCompareLoading] = useState(false)

  // 可用股票列表
  const [stockList, setStockList] = useState([])

  // ── 初始化加载 ──
  useEffect(() => {
    fetchCategories()
    fetchAllFactors()
    fetchDataStatus()
    fetchStockList()
  }, [])

  // ── URL 参数处理 ──
  useEffect(() => {
    const factor = searchParams.get('factor')
    if (factor && allFactors.length > 0) {
      openClassroom(factor)
    }
  }, [searchParams, allFactors])

  const fetchCategories = async () => {
    try {
      const r = await fetch(`${API_BASE}/quant/categories`)
      const data = await r.json()
      setCategories(data)
    } catch (e) { console.error('Failed to fetch categories:', e) }
  }

  const fetchAllFactors = async () => {
    try {
      const r = await fetch(`${API_BASE}/quant/factors`)
      const data = await r.json()
      setAllFactors(data.factors || [])
      setFactors(data.factors || [])
    } catch (e) { console.error('Failed to fetch factors:', e) }
  }

  const fetchDataStatus = async () => {
    try {
      const r = await fetch(`${API_BASE}/quant/data/status`)
      const data = await r.json()
      setDataStatus(data)
    } catch (e) { console.error('Failed to fetch data status:', e) }
  }

  const fetchStockList = async () => {
    try {
      const r = await fetch(`${API_BASE}/quant/data/stocks`)
      const data = await r.json()
      setStockList(data.stocks || [])
    } catch (e) { console.error('Failed to fetch stock list:', e) }
  }

  // ── 筛选因子 ──
  const filteredFactors = useMemo(() => {
    let result = allFactors
    if (activeCategory) {
      result = result.filter(f => f.category === activeCategory)
    }
    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      result = result.filter(f =>
        f.name.toLowerCase().includes(q) ||
        f.desc.toLowerCase().includes(q) ||
        f.formula.toLowerCase().includes(q)
      )
    }
    return result
  }, [allFactors, activeCategory, searchQuery])

  // ── 打开策略小课堂 ──
  const openClassroom = useCallback(async (factorName) => {
    setSelectedFactor(factorName)
    setClassroomLoading(true)
    setClassroomData(null)
    try {
      const r = await fetch(`${API_BASE}/quant/classroom/${factorName}`)
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      const data = await r.json()
      setClassroomData(data)
    } catch (e) {
      setClassroomData({ error: e.message })
    }
    setClassroomLoading(false)
  }, [])

  // ── 计算因子 ──
  const calculateFactors = async () => {
    if (!calcTicker.trim()) return
    setCalcLoading(true)
    setCalcError('')
    setCalcResult(null)
    try {
      const r = await fetch(`${API_BASE}/quant/factors/${calcTicker.trim()}?last_n=1`)
      if (!r.ok) {
        const err = await r.json()
        throw new Error(err.detail || `HTTP ${r.status}`)
      }
      const data = await r.json()
      setCalcResult(data)
    } catch (e) {
      setCalcError(e.message)
    }
    setCalcLoading(false)
  }

  // ── 多股对比 ──
  const runCompare = async () => {
    if (!compareTickers.trim() || !compareFactor.trim()) return
    setCompareLoading(true)
    setCompareResult(null)
    try {
      const r = await fetch(`${API_BASE}/quant/compare?tickers=${compareTickers.trim()}&factor=${compareFactor.trim()}&last_n=30`)
      if (!r.ok) {
        const err = await r.json()
        throw new Error(err.detail || `HTTP ${r.status}`)
      }
      const data = await r.json()
      setCompareResult(data)
    } catch (e) {
      setCompareResult({ error: e.message })
    }
    setCompareLoading(false)
  }

  const totalFactors = useMemo(() =>
    Object.values(categories).reduce((sum, c) => sum + (c.count || 0), 0), [categories])

  return (
    <div className="animate-in">
      {/* ── 页头 ── */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center text-white shadow-lg"
            style={{ background: 'linear-gradient(135deg, #C8963E, #E8A817)', boxShadow: '0 4px 12px rgba(200,150,62,0.3)' }}>
            <GraduationCap className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-2xl font-bold" style={{ color: '#1A1A2E' }}>策略小课堂</h1>
            <p className="text-sm" style={{ color: '#A09080' }}>
              基于 Qlib Alpha158 因子库 · {totalFactors} 个量化因子 · 8 大类别
            </p>
          </div>
        </div>
        {/* 合规声明 */}
        <div className="flex items-start gap-2 px-4 py-2.5 rounded-lg" style={{ background: 'rgba(196,30,58,0.04)', border: '1px solid rgba(196,30,58,0.1)' }}>
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" style={{ color: '#C41E3A' }} />
          <span className="text-xs" style={{ color: '#A3152E' }}>
            本页面所有因子数据仅用于金融知识教育展示，不构成投资建议。量化因子是历史数据的统计特征，不代表未来走势。
          </span>
        </div>
      </div>

      {/* ── 数据状态条 ── */}
      {dataStatus && (
        <div className="flex items-center gap-4 px-4 py-2.5 rounded-xl mb-6" style={{ background: '#FFFFFF', border: '1px solid #F0E6D3' }}>
          <Database className="w-4 h-4" style={{ color: '#C8963E' }} />
          <span className="text-xs" style={{ color: '#6B5B4E' }}>
            已入库 <b style={{ color: '#1A1A2E' }}>{dataStatus.stock_count}</b> 只股票 ·
            {' '}{dataStatus.calendar_days} 个交易日 ·
            {' '}{dataStatus.bin_files} 个数据文件 ·
            {' '}{dataStatus.total_size_mb} MB
          </span>
          {stockList.length > 0 && (
            <div className="flex gap-1.5 ml-auto">
              {stockList.slice(0, 5).map(s => (
                <span key={s.code} className="badge badge-gold text-2xs cursor-pointer"
                  onClick={() => setCalcTicker(s.code)}>
                  {s.name || s.code}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── 因子类别卡片 ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        {Object.entries(categories).map(([key, info]) => {
          const Icon = CATEGORY_ICONS[key] || BookOpen
          const color = CATEGORY_COLORS[key] || '#C8963E'
          const active = activeCategory === key
          return (
            <button
              key={key}
              onClick={() => setActiveCategory(active ? '' : key)}
              className="card card-hover p-4 text-left transition-all"
              style={active ? { borderColor: color, boxShadow: `0 4px 16px ${color}20` } : {}}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center"
                  style={{ background: `${color}15` }}>
                  <Icon className="w-4 h-4" style={{ color }} />
                </div>
                <span className="text-lg font-bold" style={{ color: '#1A1A2E' }}>{info.count}</span>
              </div>
              <div className="text-sm font-semibold" style={{ color: '#1A1A2E' }}>{info.label}</div>
              <div className="text-2xs mt-0.5" style={{ color: '#A09080' }}>{key}</div>
            </button>
          )
        })}
      </div>

      {/* ── 因子百科 ── */}
      <div className="card p-5 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4" style={{ color: '#C8963E' }} />
            <h2 className="text-base font-bold" style={{ color: '#1A1A2E' }}>因子百科</h2>
            {activeCategory && (
              <span className="badge badge-gold">
                {categories[activeCategory]?.label} · {categories[activeCategory]?.count} 个
              </span>
            )}
            <button
              onClick={() => { setActiveCategory(''); setSearchQuery('') }}
              className="text-xs hover:underline"
              style={{ color: '#A09080', display: activeCategory || searchQuery ? 'inline' : 'none' }}
            >
              清除筛选
            </button>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5" style={{ color: '#A09080' }} />
            <input
              type="text"
              placeholder="搜索因子名称、公式..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="input-light !py-1.5 !pl-9 !pr-3 text-sm w-64"
            />
          </div>
        </div>

        {/* 因子列表 */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-2.5 max-h-[480px] overflow-y-auto pr-1">
          {filteredFactors.length === 0 ? (
            <div className="col-span-full text-center py-12" style={{ color: '#A09080' }}>
              <Search className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <p className="text-sm">未找到匹配的因子</p>
            </div>
          ) : (
            filteredFactors.map((f, i) => {
              const color = CATEGORY_COLORS[f.category] || '#C8963E'
              return (
                <button
                  key={f.name}
                  onClick={() => openClassroom(f.name)}
                  className="flex items-start gap-3 p-3 rounded-xl text-left transition-all group"
                  style={{ background: '#FFF8EE', border: '1px solid #F0E6D3' }}
                  onMouseEnter={e => {
                    e.currentTarget.style.borderColor = color + '40'
                    e.currentTarget.style.background = '#FFFFFF'
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.borderColor = '#F0E6D3'
                    e.currentTarget.style.background = '#FFF8EE'
                  }}
                >
                  <div className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 text-xs font-bold"
                    style={{ background: `${color}15`, color }}>
                    {i + 1}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-sm font-bold font-mono" style={{ color: '#1A1A2E' }}>{f.name}</span>
                      <span className="text-2xs px-1.5 py-0.5 rounded"
                        style={{ background: `${color}10`, color }}>
                        {categories[f.category]?.label || f.category}
                      </span>
                    </div>
                    <p className="text-xs line-clamp-1" style={{ color: '#6B5B4E' }}>{f.desc}</p>
                  </div>
                  <ChevronRight className="w-3.5 h-3.5 shrink-0 mt-1 opacity-0 group-hover:opacity-100 transition-opacity" style={{ color }} />
                </button>
              )
            })
          )}
        </div>
      </div>

      {/* ── 因子计算器 ── */}
      <div className="grid lg:grid-cols-2 gap-4 mb-6">
        {/* 单股因子计算 */}
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Calculator className="w-4 h-4" style={{ color: '#C8963E' }} />
            <h2 className="text-base font-bold" style={{ color: '#1A1A2E' }}>因子计算器</h2>
          </div>

          <div className="flex gap-2 mb-4">
            <input
              type="text"
              value={calcTicker}
              onChange={e => setCalcTicker(e.target.value)}
              placeholder="股票代码 (如 600519.SS)"
              className="input-light flex-1 text-sm font-mono"
              onKeyDown={e => e.key === 'Enter' && calculateFactors()}
            />
            <button
              onClick={calculateFactors}
              disabled={calcLoading}
              className="btn-primary text-sm whitespace-nowrap"
            >
              {calcLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
              计算
            </button>
          </div>

          {/* 快捷股票选择 */}
          {stockList.length > 0 && (
            <div className="flex gap-1.5 mb-4 flex-wrap">
              {stockList.map(s => (
                <button
                  key={s.code}
                  onClick={() => setCalcTicker(s.code)}
                  className="text-xs px-2.5 py-1 rounded-lg transition-all"
                  style={{
                    background: calcTicker === s.code ? 'rgba(200,150,62,0.12)' : '#FFF8EE',
                    color: calcTicker === s.code ? '#C8963E' : '#6B5B4E',
                    border: '1px solid ' + (calcTicker === s.code ? 'rgba(200,150,62,0.3)' : '#F0E6D3'),
                  }}
                >
                  {s.name || s.code}
                </button>
              ))}
            </div>
          )}

          {/* 计算结果 */}
          {calcError && (
            <div className="text-sm py-3 px-4 rounded-lg" style={{ background: 'rgba(196,30,58,0.06)', color: '#C41E3A' }}>
              {calcError}
            </div>
          )}

          {calcResult && (
            <div className="animate-in">
              <div className="flex items-center justify-between mb-3 pb-2" style={{ borderBottom: '1px solid #F0E6D3' }}>
                <div>
                  <span className="text-sm font-bold" style={{ color: '#1A1A2E' }}>{calcResult.ticker}</span>
                  <span className="text-xs ml-2" style={{ color: '#A09080' }}>{calcResult.symbol}</span>
                </div>
                <span className="text-xs" style={{ color: '#A09080' }}>{calcResult.date} · {calcResult.total_factors} 因子</span>
              </div>
              <div className="space-y-1 max-h-[360px] overflow-y-auto pr-1">
                {calcResult.factors?.map(f => {
                  const color = CATEGORY_COLORS[f.category] || '#C8963E'
                  return (
                    <div key={f.name} className="flex items-center gap-3 py-1.5 px-2 rounded-lg hover:bg-base-1 transition-colors">
                      <span className="text-xs font-mono font-bold w-16 shrink-0" style={{ color: '#1A1A2E' }}>{f.name}</span>
                      <span className="text-xs flex-1 truncate" style={{ color: '#6B5B4E' }}>{f.desc}</span>
                      <span className="text-xs font-mono font-semibold num" style={{ color }}>
                        {typeof f.value === 'number' ? f.value.toFixed(4) : f.value}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {!calcResult && !calcError && !calcLoading && (
            <div className="text-center py-8" style={{ color: '#A09080' }}>
              <Calculator className="w-8 h-8 mx-auto mb-2 opacity-20" />
              <p className="text-xs">输入股票代码，计算全部 158 个量化因子</p>
            </div>
          )}
        </div>

        {/* 多股对比 */}
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <GitCompare className="w-4 h-4" style={{ color: '#C41E3A' }} />
            <h2 className="text-base font-bold" style={{ color: '#1A1A2E' }}>多股因子对比</h2>
          </div>

          <div className="space-y-2 mb-4">
            <div className="flex gap-2">
              <input
                type="text"
                value={compareTickers}
                onChange={e => setCompareTickers(e.target.value)}
                placeholder="股票代码，逗号分隔"
                className="input-light flex-1 text-sm font-mono"
              />
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={compareFactor}
                onChange={e => setCompareFactor(e.target.value)}
                placeholder="因子名称 (如 RSV5)"
                className="input-light flex-1 text-sm font-mono"
              />
              <button
                onClick={runCompare}
                disabled={compareLoading}
                className="btn-primary text-sm whitespace-nowrap"
              >
                {compareLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <GitCompare className="w-4 h-4" />}
                对比
              </button>
            </div>
          </div>

          {/* 对比结果 */}
          {compareResult?.error && (
            <div className="text-sm py-3 px-4 rounded-lg" style={{ background: 'rgba(196,30,58,0.06)', color: '#C41E3A' }}>
              {compareResult.error}
            </div>
          )}

          {compareResult && !compareResult.error && (
            <div className="animate-in">
              <div className="mb-3 pb-2" style={{ borderBottom: '1px solid #F0E6D3' }}>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-bold font-mono" style={{ color: '#1A1A2E' }}>{compareResult.factor}</span>
                  <span className="text-xs" style={{ color: '#A09080' }}>{compareResult.desc}</span>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => openClassroom(compareResult.factor)}
                    className="text-xs flex items-center gap-1 hover:underline"
                    style={{ color: '#C8963E' }}
                  >
                    <Lightbulb className="w-3 h-3" />
                    查看因子解读
                  </button>
                  <span className="text-2xs" style={{ color: '#A09080' }}>
                    最近 {compareResult.dates?.length || 0} 个交易日
                  </span>
                </div>
              </div>

              {/* 对比折线图 */}
              {compareResult.stocks && compareResult.dates && (
                <div className="mb-3" style={{ height: '220px' }}>
                  <Line
                    data={{
                      labels: compareResult.dates,
                      datasets: compareResult.stocks.map((s, i) => {
                        const colors = ['#C8963E', '#C41E3A', '#2563EB', '#059669', '#7C3AED']
                        const color = colors[i % colors.length]
                        return {
                          label: s.ticker,
                          data: s.values,
                          borderColor: color,
                          backgroundColor: color + '15',
                          tension: 0.3,
                          pointRadius: 2,
                          pointHoverRadius: 5,
                          borderWidth: 2,
                        }
                      }),
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'top',
                          labels: { font: { size: 11 }, color: '#6B5B4E' }
                        },
                      },
                      scales: {
                        x: {
                          ticks: { font: { size: 9 }, color: '#A09080', maxRotation: 0 },
                          grid: { display: false },
                        },
                        y: {
                          ticks: { font: { size: 10 }, color: '#A09080' },
                          grid: { color: '#F0E6D3' },
                        },
                      },
                    }}
                  />
                </div>
              )}

              {/* 数值表 */}
              <div className="space-y-1">
                {compareResult.stocks?.map(s => {
                  const latest = s.values[s.values.length - 1]
                  const prev = s.values[s.values.length - 2]
                  const change = prev != null ? latest - prev : null
                  return (
                    <div key={s.ticker} className="flex items-center justify-between py-1.5 px-2 rounded-lg" style={{ background: '#FFF8EE' }}>
                      <span className="text-xs font-mono font-semibold" style={{ color: '#1A1A2E' }}>{s.ticker}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold num" style={{ color: '#1A1A2E' }}>
                          {latest != null ? latest.toFixed(4) : '—'}
                        </span>
                        {change != null && (
                          <span className="text-xs num" style={{ color: change >= 0 ? '#DC2626' : '#059669' }}>
                            {change >= 0 ? '+' : ''}{change.toFixed(4)}
                          </span>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {!compareResult && !compareLoading && (
            <div className="text-center py-8" style={{ color: '#A09080' }}>
              <GitCompare className="w-8 h-8 mx-auto mb-2 opacity-20" />
              <p className="text-xs">输入多只股票代码和因子名，对比因子走势</p>
            </div>
          )}
        </div>
      </div>

      {/* ── 因子课堂弹窗 ── */}
      {selectedFactor && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: 'rgba(26,26,46,0.4)', backdropFilter: 'blur(4px)' }}
          onClick={() => setSelectedFactor(null)}
        >
          <div
            className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-y-auto animate-scale-in"
            onClick={e => e.stopPropagation()}
            style={{ boxShadow: '0 24px 64px rgba(139,115,85,0.2)' }}
          >
            {/* 弹窗头 */}
            <div className="flex items-center justify-between p-5 sticky top-0 bg-white z-10" style={{ borderBottom: '1px solid #F0E6D3' }}>
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg flex items-center justify-center"
                  style={{ background: `${CATEGORY_COLORS[classroomData?.category || 'price']}15` }}>
                  <Lightbulb className="w-4 h-4" style={{ color: CATEGORY_COLORS[classroomData?.category || 'price'] }} />
                </div>
                <div>
                  <h3 className="text-lg font-bold font-mono" style={{ color: '#1A1A2E' }}>{selectedFactor}</h3>
                  {classroomData && (
                    <span className="text-xs" style={{ color: '#A09080' }}>
                      {classroomData.category_label} · 策略小课堂
                    </span>
                  )}
                </div>
              </div>
              <button onClick={() => setSelectedFactor(null)} className="p-2 rounded-lg transition-all" style={{ color: '#A09080' }}>
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* 弹窗内容 */}
            <div className="p-5">
              {classroomLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin" style={{ color: '#C8963E' }} />
                </div>
              ) : classroomData?.error ? (
                <div className="text-sm py-4 text-center" style={{ color: '#C41E3A' }}>
                  加载失败: {classroomData.error}
                </div>
              ) : classroomData ? (
                <div className="space-y-5">
                  {/* 公式 */}
                  <div>
                    <div className="text-xs font-semibold mb-1.5 flex items-center gap-1" style={{ color: '#A09080' }}>
                      <Sigma className="w-3.5 h-3.5" /> 计算公式
                    </div>
                    <div className="px-4 py-3 rounded-lg font-mono text-sm" style={{ background: '#FFF8EE', color: '#1A1A2E', border: '1px solid #F0E6D3' }}>
                      {classroomData.formula}
                    </div>
                  </div>

                  {/* 释义 */}
                  <div>
                    <div className="text-xs font-semibold mb-1.5 flex items-center gap-1" style={{ color: '#A09080' }}>
                      <BookOpen className="w-3.5 h-3.5" /> 因子释义
                    </div>
                    <p className="text-sm leading-relaxed" style={{ color: '#1A1A2E' }}>{classroomData.desc}</p>
                  </div>

                  {/* 教学解读 */}
                  <div>
                    <div className="text-xs font-semibold mb-1.5 flex items-center gap-1" style={{ color: '#A09080' }}>
                      <GraduationCap className="w-3.5 h-3.5" /> 教学解读
                    </div>
                    <div className="px-4 py-3 rounded-lg" style={{ background: 'rgba(200,150,62,0.04)', border: '1px solid rgba(200,150,62,0.12)' }}>
                      <p className="text-sm leading-relaxed" style={{ color: '#3D2A0C' }}>{classroomData.teaching}</p>
                    </div>
                  </div>

                  {/* 示例数据 */}
                  {classroomData.example && (
                    <div>
                      <div className="text-xs font-semibold mb-1.5 flex items-center gap-1" style={{ color: '#A09080' }}>
                        <BarChart3 className="w-3.5 h-3.5" /> 示例数据 · {classroomData.example.ticker}
                      </div>
                      <div className="px-4 py-3 rounded-lg" style={{ background: '#FFF8EE', border: '1px solid #F0E6D3' }}>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs" style={{ color: '#6B5B4E' }}>最近 10 个交易日</span>
                          <span className="text-sm font-bold num" style={{ color: '#C8963E' }}>
                            最新值: {classroomData.example.latest_value != null
                              ? classroomData.example.latest_value.toFixed(4)
                              : '—'}
                          </span>
                        </div>
                        {/* 迷你折线图 */}
                        <div style={{ height: '120px' }}>
                          <Line
                            data={{
                              labels: classroomData.example.dates,
                              datasets: [{
                                label: selectedFactor,
                                data: classroomData.example.values,
                                borderColor: '#C8963E',
                                backgroundColor: 'rgba(200,150,62,0.08)',
                                fill: true,
                                tension: 0.3,
                                pointRadius: 2,
                                pointHoverRadius: 4,
                                borderWidth: 2,
                              }],
                            }}
                            options={{
                              responsive: true,
                              maintainAspectRatio: false,
                              plugins: { legend: { display: false } },
                              scales: {
                                x: { ticks: { font: { size: 8 }, color: '#A09080', maxRotation: 0 }, grid: { display: false } },
                                y: { ticks: { font: { size: 9 }, color: '#A09080' }, grid: { color: '#F0E6D3' } },
                              },
                            }}
                          />
                        </div>
                      </div>
                    </div>
                  )}

                  {/* 合规声明 */}
                  <div className="flex items-start gap-2 px-3 py-2 rounded-lg" style={{ background: 'rgba(196,30,58,0.04)' }}>
                    <AlertCircle className="w-3.5 h-3.5 mt-0.5 shrink-0" style={{ color: '#C41E3A' }} />
                    <span className="text-2xs" style={{ color: '#A3152E' }}>{classroomData.disclaimer}</span>
                  </div>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
