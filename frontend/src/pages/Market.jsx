import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  BarChart3, TrendingUp, TrendingDown, Activity, Database,
  AlertCircle, Loader2, RefreshCw, ArrowRight, ChevronRight,
  Flame, Snowflake, Gauge, Layers, PieChart
} from 'lucide-react'
import { Pie } from 'react-chartjs-2'
import {
  Chart as ChartJS, ArcElement, Tooltip, Legend,
  CategoryScale, LinearScale, BarElement, Title
} from 'chart.js'

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title)

const API_BASE = import.meta.env.VITE_API_URL || '/api'

export default function Market() {
  const navigate = useNavigate()
  const [overview, setOverview] = useState(null)
  const [breadth, setBreadth] = useState(null)
  const [topCheap, setTopCheap] = useState(null)
  const [topExpensive, setTopExpensive] = useState(null)
  const [topGainers, setTopGainers] = useState(null)
  const [topLosers, setTopLosers] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('valuation')
  const [rankMetric, setRankMetric] = useState('pe_ttm')

  useEffect(() => {
    loadAll()
  }, [])

  const loadAll = async () => {
    setLoading(true)
    try {
      const [ovRes, brRes, cheapRes, expRes, gainRes, loseRes] = await Promise.all([
        fetch(`${API_BASE}/quant/market-overview`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/quant/market/breadth`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/quant/market/top-stocks?metric=pe_ttm&n=10&direction=cheapest`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/quant/market/top-stocks?metric=pe_ttm&n=10&direction=most_expensive`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/quant/market/top-stocks?metric=change_pct&n=10&direction=most_expensive`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/quant/market/top-stocks?metric=change_pct&n=10&direction=cheapest`).then(r => r.json()).catch(() => null),
      ])
      setOverview(ovRes)
      setBreadth(brRes)
      setTopCheap(cheapRes)
      setTopExpensive(expRes)
      setTopGainers(gainRes)
      setTopLosers(loseRes)
    } catch (e) {
      console.error('加载数据失败', e)
    }
    setLoading(false)
  }

  const formatMV = (yi) => {
    if (!yi) return '--'
    if (yi >= 10000) return `${(yi / 10000).toFixed(1)}万亿`
    return `${yi.toFixed(0)}亿`
  }

  const formatPE = (pe) => {
    if (!pe || pe <= 0) return '--'
    return pe.toFixed(1)
  }

  // 涨跌分布饼图数据
  const breadthData = useMemo(() => {
    if (!breadth) return null
    return {
      labels: ['涨停', '大涨(5-9%)', '小涨(0-5%)', '平盘', '小跌(0-5%)', '大跌(5-9%)', '跌停'],
      datasets: [{
        data: [
          breadth.limit_up || 0,
          breadth.big_up || 0,
          breadth.small_up || 0,
          breadth.flat_count || 0,
          breadth.small_down || 0,
          breadth.big_down || 0,
          breadth.limit_down || 0,
        ],
        backgroundColor: [
          '#DC2626', '#EF4444', '#F87171', '#D4C4A8',
          '#86EFAC', '#10B981', '#059669',
        ],
        borderColor: '#FFFFFF',
        borderWidth: 2,
      }],
    }
  }, [breadth])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-10 h-10 animate-spin" style={{ color: '#C8963E' }} />
      </div>
    )
  }

  return (
    <div className="animate-in">
      {/* ── 页头 ── */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center text-white shadow-lg"
            style={{ background: 'linear-gradient(135deg, #C8963E, #E8A817)', boxShadow: '0 4px 12px rgba(200,150,62,0.3)' }}>
            <BarChart3 className="w-5 h-5" />
          </div>
          <div className="flex-1">
            <h1 className="text-2xl font-bold" style={{ color: '#1A1A2E' }}>市场概览</h1>
            <p className="text-sm" style={{ color: '#A09080' }}>
              全A股实时统计 · 估值分布 · 涨跌概况
              {overview?.cache_time && <span className="ml-2">· 数据更新于 {overview.cache_time}</span>}
            </p>
          </div>
          <button onClick={loadAll}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm transition-all"
            style={{ background: '#FFFFFF', border: '1px solid #F0E6D3', color: '#6B5B4E' }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = '#C8963E'; e.currentTarget.style.color = '#C8963E' }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = '#F0E6D3'; e.currentTarget.style.color = '#6B5B4E' }}>
            <RefreshCw className="w-3.5 h-3.5" />
            刷新
          </button>
        </div>
        {/* 合规声明 */}
        <div className="flex items-start gap-2 px-4 py-2.5 rounded-lg" style={{ background: 'rgba(196,30,58,0.04)', border: '1px solid rgba(196,30,58,0.1)' }}>
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" style={{ color: '#C41E3A' }} />
          <span className="text-xs" style={{ color: '#A3152E' }}>
            本页面数据仅用于金融知识教育展示，不构成投资建议。市场有风险，投资需谨慎。
          </span>
        </div>
      </div>

      {/* ── 核心指标卡片 ── */}
      {overview && !overview.error && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          <MetricCard
            icon={Gauge}
            label="全A中位PE"
            value={overview.median_pe?.toFixed(1) || '--'}
            sub={`均值 ${overview.avg_pe?.toFixed(1) || '--'}`}
            color="#C8963E"
          />
          <MetricCard
            icon={Layers}
            label="全A中位PB"
            value={overview.median_pb?.toFixed(1) || '--'}
            sub={`均值 ${overview.avg_pb?.toFixed(1) || '--'}`}
            color="#7C3AED"
          />
          <MetricCard
            icon={PieChart}
            label="总市值"
            value={formatMV(overview.total_market_cap_yi)}
            sub={`${overview.total_stocks?.toLocaleString() || 0} 只股票`}
            color="#2563EB"
          />
          <MetricCard
            icon={Activity}
            label="涨跌比"
            value={overview.up_count != null ? `${overview.up_count} : ${overview.down_count}` : '--'}
            sub={breadth ? `涨停 ${breadth.limit_up || 0} · 跌停 ${breadth.limit_down || 0}` : ''}
            color={overview.up_count >= overview.down_count ? '#DC2626' : '#059669'}
          />
        </div>
      )}

      {/* ── 涨跌分布 + 估值排名 ── */}
      <div className="grid lg:grid-cols-3 gap-4 mb-6">
        {/* 涨跌分布饼图 */}
        {breadthData && (
          <div className="card p-5">
            <div className="flex items-center gap-2 mb-4">
              <PieChart className="w-4 h-4" style={{ color: '#C8963E' }} />
              <h2 className="text-base font-bold" style={{ color: '#1A1A2E' }}>涨跌分布</h2>
            </div>
            <div style={{ height: '240px' }}>
              <Pie
                data={breadthData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      position: 'bottom',
                      labels: { font: { size: 10 }, color: '#6B5B4E', padding: 8, boxWidth: 12 },
                    },
                  },
                }}
              />
            </div>
          </div>
        )}

        {/* 估值排名 Tab */}
        <div className="card p-5 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" style={{ color: '#C8963E' }} />
              <h2 className="text-base font-bold" style={{ color: '#1A1A2E' }}>市场估值排名</h2>
            </div>
            <div className="flex gap-1">
              <button
                onClick={() => setActiveTab('valuation')}
                className="px-3 py-1 rounded-lg text-xs font-medium transition-all"
                style={activeTab === 'valuation'
                  ? { background: 'rgba(200,150,62,0.12)', color: '#C8963E' }
                  : { color: '#A09080' }}>
                估值
              </button>
              <button
                onClick={() => setActiveTab('movers')}
                className="px-3 py-1 rounded-lg text-xs font-medium transition-all"
                style={activeTab === 'movers'
                  ? { background: 'rgba(196,30,58,0.08)', color: '#C41E3A' }
                  : { color: '#A09080' }}>
                涨跌幅
              </button>
            </div>
          </div>

          {activeTab === 'valuation' ? (
            <div className="grid md:grid-cols-2 gap-4">
              {/* 最低PE */}
              <div>
                <div className="flex items-center gap-1.5 mb-2">
                  <Snowflake className="w-3.5 h-3.5" style={{ color: '#059669' }} />
                  <span className="text-xs font-semibold" style={{ color: '#059669' }}>PE 最低 Top 10</span>
                </div>
                <StockList stocks={topCheap?.stocks} metric="pe_ttm" color="#059669" navigate={navigate} />
              </div>
              {/* 最高PE */}
              <div>
                <div className="flex items-center gap-1.5 mb-2">
                  <Flame className="w-3.5 h-3.5" style={{ color: '#DC2626' }} />
                  <span className="text-xs font-semibold" style={{ color: '#DC2626' }}>PE 最高 Top 10</span>
                </div>
                <StockList stocks={topExpensive?.stocks} metric="pe_ttm" color="#DC2626" navigate={navigate} />
              </div>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 gap-4">
              {/* 涨幅最大 */}
              <div>
                <div className="flex items-center gap-1.5 mb-2">
                  <TrendingUp className="w-3.5 h-3.5" style={{ color: '#DC2626' }} />
                  <span className="text-xs font-semibold" style={{ color: '#DC2626' }}>涨幅最大 Top 10</span>
                </div>
                <StockList stocks={topGainers?.stocks} metric="change_pct" color="#DC2626" navigate={navigate} />
              </div>
              {/* 跌幅最大 */}
              <div>
                <div className="flex items-center gap-1.5 mb-2">
                  <TrendingDown className="w-3.5 h-3.5" style={{ color: '#059669' }} />
                  <span className="text-xs font-semibold" style={{ color: '#059669' }}>跌幅最大 Top 10</span>
                </div>
                <StockList stocks={topLosers?.stocks} metric="change_pct" color="#059669" navigate={navigate} />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── 数据来源说明 ── */}
      <div className="card p-4 flex items-center gap-3">
        <Database className="w-4 h-4 shrink-0" style={{ color: '#C8963E' }} />
        <span className="text-xs" style={{ color: '#A09080' }}>
          数据来源：东方财富实时行情（stock_zh_a_spot_em），覆盖沪深京全市场A股。
          基本面数据每2小时自动刷新缓存，涨跌分布为请求时刻快照。
        </span>
      </div>
    </div>
  )
}

// ── 指标卡片组件 ──
function MetricCard({ icon: Icon, label, value, sub, color }) {
  return (
    <div className="card p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center"
          style={{ background: `${color}15` }}>
          <Icon className="w-4 h-4" style={{ color }} />
        </div>
      </div>
      <div className="text-2xl font-bold num" style={{ color: '#1A1A2E' }}>{value}</div>
      <div className="text-xs mt-0.5" style={{ color: '#A09080' }}>{label}</div>
      {sub && <div className="text-2xs mt-0.5" style={{ color: '#6B5B4E' }}>{sub}</div>}
    </div>
  )
}

// ── 股票列表组件 ──
function StockList({ stocks, metric, color, navigate }) {
  if (!stocks || stocks.length === 0) {
    return (
      <div className="text-center py-6">
        <Loader2 className="w-5 h-5 animate-spin mx-auto" style={{ color: '#A09080' }} />
      </div>
    )
  }

  return (
    <div className="space-y-1 max-h-[320px] overflow-y-auto pr-1">
      {stocks.map((s, i) => {
        const val = s[metric]
        const isChange = metric === 'change_pct'
        const valColor = isChange ? (val >= 0 ? '#DC2626' : '#059669') : color
        return (
          <button
            key={s.code}
            onClick={() => navigate(`/analysis?q=${encodeURIComponent(s.name || s.code)}`)}
            className="w-full flex items-center gap-2 py-1.5 px-2 rounded-lg transition-all text-left group"
            style={{ background: '#FFF8EE', border: '1px solid #F0E6D3' }}
            onMouseEnter={e => { e.currentTarget.style.background = '#FFFFFF'; e.currentTarget.style.borderColor = `${color}40` }}
            onMouseLeave={e => { e.currentTarget.style.background = '#FFF8EE'; e.currentTarget.style.borderColor = '#F0E6D3' }}>
            <span className="text-2xs font-bold w-5 text-center shrink-0" style={{ color: '#A09080' }}>{i + 1}</span>
            <div className="min-w-0 flex-1">
              <div className="text-xs font-medium truncate" style={{ color: '#1A1A2E' }}>{s.name}</div>
              <div className="text-2xs font-mono" style={{ color: '#A09080' }}>{s.code}</div>
            </div>
            {s.price != null && (
              <span className="text-xs font-mono num shrink-0" style={{ color: '#6B5B4E' }}>
                {s.price.toFixed(2)}
              </span>
            )}
            <span className="text-xs font-bold font-mono num shrink-0 w-14 text-right" style={{ color: valColor }}>
              {isChange
                ? `${val >= 0 ? '+' : ''}${val.toFixed(2)}%`
                : val != null ? val.toFixed(1) : '--'}
            </span>
            <ChevronRight className="w-3 h-3 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" style={{ color }} />
          </button>
        )
      })}
    </div>
  )
}
