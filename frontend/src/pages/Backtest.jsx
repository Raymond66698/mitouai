import { useState } from 'react'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, Title, Tooltip, Legend, Filler
} from 'chart.js'
import { TrendingUp, TrendingDown, Activity, BarChart3, Loader2, AlertTriangle, CheckCircle, XCircle, Search, ChevronRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

const STRATEGIES = [
  { id: 'ma_crossover', name: '均线交叉', desc: '短期均线上穿长期均线买入', icon: '📈', params: [{ key: 'short_period', label: '短周期', default: 5 }, { key: 'long_period', label: '长周期', default: 20 }] },
  { id: 'momentum', name: '动量突破', desc: 'N日涨幅超阈值买入', icon: '🚀', params: [{ key: 'lookback_days', label: '回溯天数', default: 20 }, { key: 'threshold', label: '阈值(%)', default: 5 }] },
  { id: 'rsi_reversal', name: 'RSI反转', desc: 'RSI超卖买入，超买卖出', icon: '🔄', params: [{ key: 'rsi_period', label: 'RSI周期', default: 14 }, { key: 'oversold', label: '超卖线', default: 30 }, { key: 'overbought', label: '超买线', default: 70 }] },
  { id: 'buy_hold', name: '买入持有', desc: '作为回测基准对比', icon: '💎', params: [] },
]

export default function Backtest() {
  const navigate = useNavigate()
  const [ticker, setTicker] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [selectedStock, setSelectedStock] = useState(null)
  const [strategy, setStrategy] = useState('ma_crossover')
  const [params, setParams] = useState({ short_period: 5, long_period: 20 })
  const [lookback, setLookback] = useState(365)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [compareResults, setCompareResults] = useState(null)
  const [compareLoading, setCompareLoading] = useState(false)

  const handleSearch = async (q) => {
    if (!q || q.length < 1) { setSearchResults([]); return }
    try {
      const r = await fetch(`/api/analysis/search?q=${encodeURIComponent(q)}`)
      const data = await r.json()
      setSearchResults(data.results || [])
    } catch { }
  }

  const handleRun = async () => {
    if (!selectedStock) return
    setLoading(true)
    setResult(null)
    try {
      const r = await fetch('/api/backtest/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticker: selectedStock.code,
          strategy,
          params,
          initial_capital: 100000,
          start_date: new Date(Date.now() - lookback * 86400000).toISOString().slice(0, 10),
          end_date: new Date().toISOString().slice(0, 10),
        }),
      })
      const data = await r.json()
      setResult(data)
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  const handleCompare = async () => {
    if (!selectedStock) return
    setCompareLoading(true)
    try {
      const r = await fetch('/api/backtest/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticker: selectedStock.code,
          strategies: ['buy_hold', 'ma_crossover', 'momentum', 'rsi_reversal'],
          start_date: new Date(Date.now() - lookback * 86400000).toISOString().slice(0, 10),
          end_date: new Date().toISOString().slice(0, 10),
        }),
      })
      const data = await r.json()
      setCompareResults(data.comparison || {})
    } catch (e) { console.error(e) }
    setCompareLoading(false)
  }

  const chartData = result?.equity_curve ? {
    labels: result.equity_curve.map(p => p.date),
    datasets: [{
      label: '策略权益',
      data: result.equity_curve.map(p => p.value),
      borderColor: '#C8963E',
      backgroundColor: 'rgba(124, 58, 237, 0.1)',
      fill: true,
      tension: 0.3,
      pointRadius: 0,
      borderWidth: 2,
    }],
  } : null

  const compareChartData = compareResults && Object.keys(compareResults).length > 0 ? {
    labels: compareResults[Object.keys(compareResults)[0]]?.equity_curve?.map(p => p.date) || [],
    datasets: Object.entries(compareResults).map(([k, v]) => ({
      label: STRATEGIES.find(s => s.id === k)?.name || k,
      data: v.equity_curve?.map(p => p.value) || [],
      borderColor: k === 'buy_hold' ? '#6b7280' : k === 'ma_crossover' ? '#C8963E' : k === 'momentum' ? '#ef4444' : '#f59e0b',
      tension: 0.3,
      pointRadius: 0,
      borderWidth: 2,
    })),
  } : null

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: true, position: 'top', labels: { boxWidth: 12, padding: 15, font: { size: 11 } } },
      tooltip: {
        callbacks: {
          label: ctx => `¥${ctx.parsed.y.toLocaleString()}`,
        },
      },
    },
    scales: {
      x: { display: true, ticks: { maxTicksLimit: 8, font: { size: 10 } }, grid: { display: false } },
      y: {
        ticks: {
          callback: v => '¥' + (v / 10000).toFixed(1) + '万',
          font: { size: 10 },
        },
        grid: { color: '#F0E6D3' },
      },
    },
    interaction: { intersect: false, mode: 'index' },
  }

  const ratingColor = { A: 'text-emerald-600 bg-emerald-50', B: 'text-primary-600 bg-primary-50', C: 'text-primary-600 bg-primary-50', D: 'text-red-600 bg-red-50' }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-ink-primary">策略回测</h1>
        <p className="text-ink-muted mt-1">历史数据验证策略有效性，对比不同策略的收益与风险</p>
      </div>

      {/* 回测配置 */}
      <div className="grid lg:grid-cols-3 gap-6 mb-6">
        <div className="lg:col-span-2 bg-base-2 rounded-2xl border border-base-4 shadow-card p-5">
          <h3 className="font-semibold text-ink-primary mb-4 flex items-center gap-2">
            <Activity className="w-4 h-4" /> 回测配置
          </h3>

          {/* 股票搜索 */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-ink-secondary mb-1.5">选择股票</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-muted" />
              <input
                type="text" value={ticker}
                onChange={e => { setTicker(e.target.value); handleSearch(e.target.value) }}
                placeholder="输入股票名称或代码"
                className="w-full pl-10 pr-4 py-2.5 border border-base-4 rounded-xl focus:border-primary-400 outline-none text-sm"
              />
            </div>
            {searchResults.length > 0 && (
              <div className="mt-1 border border-base-4 rounded-lg divide-y divide-base-4 max-h-40 overflow-y-auto">
                {searchResults.slice(0, 8).map(s => (
                  <button key={s.code} onClick={() => { setSelectedStock(s); setTicker(s.name); setSearchResults([]) }}
                    className={`w-full px-3 py-2 text-left hover:bg-base-3 text-sm flex items-center justify-between
                      ${selectedStock?.code === s.code ? 'bg-primary-50 text-primary-700' : 'text-ink-secondary'}`}>
                    <span>{s.name} <span className="text-ink-muted text-xs">{s.code}</span></span>
                    {selectedStock?.code === s.code && <CheckCircle className="w-4 h-4" />}
                  </button>
                ))}
              </div>
            )}
            {selectedStock && (
              <div className="mt-2 flex items-center gap-2">
                <span className="px-2 py-0.5 bg-primary-50 text-primary-700 rounded-lg text-xs font-medium">
                  {selectedStock.name} {selectedStock.code}
                </span>
                <button onClick={() => { setSelectedStock(null); setTicker('') }}
                  className="text-ink-muted hover:text-ink-secondary"><XCircle className="w-3.5 h-3.5" /></button>
              </div>
            )}
          </div>

          {/* 策略选择 */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-ink-secondary mb-2">选择策略</label>
            <div className="grid grid-cols-2 gap-2">
              {STRATEGIES.map(s => (
                <button key={s.id} onClick={() => { setStrategy(s.id); setParams(Object.fromEntries(s.params.map(p => [p.key, p.default]))) }}
                  className={`p-3 rounded-xl border text-left transition-all
                    ${strategy === s.id ? 'border-primary-300 bg-primary-50' : 'border-base-4 hover:border-gray-300'}`}>
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{s.icon}</span>
                    <div>
                      <div className="font-medium text-sm text-ink-primary">{s.name}</div>
                      <div className="text-xs text-ink-muted">{s.desc}</div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* 参数 */}
          {STRATEGIES.find(s => s.id === strategy)?.params.length > 0 && (
            <div className="mb-4">
              <label className="block text-sm font-medium text-ink-secondary mb-2">策略参数</label>
              <div className="flex gap-3 flex-wrap">
                {STRATEGIES.find(s => s.id === strategy).params.map(p => (
                  <div key={p.key}>
                    <label className="block text-xs text-ink-muted mb-1">{p.label}</label>
                    <input type="number" value={params[p.key] || ''}
                      onChange={e => setParams({ ...params, [p.key]: parseFloat(e.target.value) || 0 })}
                      className="w-20 px-2 py-1.5 border border-base-4 rounded-lg text-sm text-center focus:border-primary-400 outline-none" />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 回测周期 */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-ink-secondary mb-2">回测周期</label>
            <div className="flex gap-2">
              {[{ label: '3个月', days: 90 }, { label: '6个月', days: 180 }, { label: '1年', days: 365 }, { label: '2年', days: 730 }, { label: '3年', days: 1095 }].map(o => (
                <button key={o.days} onClick={() => setLookback(o.days)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all
                    ${lookback === o.days ? 'bg-primary-600 text-white' : 'bg-base-3 text-ink-secondary hover:bg-gray-200'}`}>
                  {o.label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex gap-3">
            <button onClick={handleRun} disabled={!selectedStock || loading}
              className="px-5 py-2.5 bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 transition-all disabled:opacity-50 flex items-center gap-2">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <BarChart3 className="w-4 h-4" />}
              开始回测
            </button>
            <button onClick={handleCompare} disabled={!selectedStock || compareLoading}
              className="px-5 py-2.5 border border-base-4 text-ink-secondary rounded-xl font-medium hover:bg-base-3 transition-all disabled:opacity-50 flex items-center gap-2">
              {compareLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Activity className="w-4 h-4" />}
              多策略对比
            </button>
          </div>
        </div>

        {/* 快速提示 */}
        <div className="bg-gradient-to-br from-primary-500/10 to-primary-100/30 rounded-2xl border border-primary-100 p-5">
          <h3 className="font-semibold text-ink-primary mb-3 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-primary-600" /> 回测须知
          </h3>
          <ul className="space-y-3 text-sm text-ink-secondary">
            <li className="flex gap-2">
              <ChevronRight className="w-3.5 h-3.5 text-primary-500 mt-0.5 shrink-0" />
              历史回测不代表未来表现
            </li>
            <li className="flex gap-2">
              <ChevronRight className="w-3.5 h-3.5 text-primary-500 mt-0.5 shrink-0" />
              未包含交易手续费和滑点
            </li>
            <li className="flex gap-2">
              <ChevronRight className="w-3.5 h-3.5 text-primary-500 mt-0.5 shrink-0" />
              基准为买入持有策略收益
            </li>
            <li className="flex gap-2">
              <ChevronRight className="w-3.5 h-3.5 text-primary-500 mt-0.5 shrink-0" />
              最大回撤反映策略风险水平
            </li>
            <li className="flex gap-2">
              <ChevronRight className="w-3.5 h-3.5 text-primary-500 mt-0.5 shrink-0" />
              夏普比率 &gt; 1 表示风险调整收益较好
            </li>
          </ul>
          <button onClick={() => navigate('/strategies')}
            className="mt-4 w-full py-2 border border-primary-200 text-primary-700 rounded-lg text-sm font-medium hover:bg-white transition-colors">
            前往策略超市了解更多
          </button>
        </div>
      </div>

      {/* 回测结果 */}
      {result && !result.error && (
        <div className="space-y-6">
          {/* 指标卡片 */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {[
              { label: '总收益率', value: `${result.total_return > 0 ? '+' : ''}${result.total_return}%`, color: result.total_return >= 0 ? 'text-red-500' : 'text-green-500', icon: result.total_return >= 0 ? TrendingUp : TrendingDown },
              { label: '年化收益', value: `${result.annual_return > 0 ? '+' : ''}${result.annual_return}%`, color: result.annual_return >= 0 ? 'text-red-500' : 'text-green-500' },
              { label: '最大回撤', value: `${result.max_drawdown}%`, color: 'text-amber-500' },
              { label: '夏普比率', value: result.sharpe_ratio.toFixed(2), color: result.sharpe_ratio > 1 ? 'text-emerald-500' : 'text-ink-muted' },
              { label: '胜率', value: `${result.win_rate}%`, color: result.win_rate > 50 ? 'text-primary-500' : 'text-ink-muted' },
            ].map((m, i) => {
              const Icon = m.icon
              return (
                <div key={i} className="bg-base-2 rounded-xl border border-base-4 p-4">
                  <div className="text-xs text-ink-muted mb-1">{m.label}</div>
                  <div className={`text-xl font-bold ${m.color} flex items-center gap-1`}>
                    {Icon && <Icon className="w-4 h-4" />}
                    {m.value}
                  </div>
                </div>
              )
            })}
          </div>

          {/* 评级和对比 */}
          <div className="grid md:grid-cols-2 gap-4">
            <div className="bg-base-2 rounded-xl border border-base-4 p-4 flex items-center justify-between">
              <div>
                <div className="text-xs text-ink-muted mb-1">策略评级</div>
                <div className={`inline-flex px-3 py-1 rounded-lg text-lg font-bold ${ratingColor[result.rating] || 'text-ink-secondary bg-base-2'}`}>
                  {result.rating} 级
                </div>
              </div>
              <div className="text-right">
                <div className="text-xs text-ink-muted mb-1">vs 买入持有</div>
                <div className={`text-lg font-bold ${result.excess_return >= 0 ? 'text-red-500' : 'text-green-500'}`}>
                  {result.excess_return > 0 ? '+' : ''}{result.excess_return}%
                </div>
                <div className="text-xs text-ink-muted">超额收益</div>
              </div>
            </div>
            <div className="bg-base-2 rounded-xl border border-base-4 p-4">
              <div className="text-xs text-ink-muted mb-1">交易统计</div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <div className="text-lg font-bold text-ink-primary">{result.trade_count}</div>
                  <div className="text-xs text-ink-muted">交易次数</div>
                </div>
                <div>
                  <div className="text-lg font-bold text-ink-primary">¥{result.final_value.toLocaleString()}</div>
                  <div className="text-xs text-ink-muted">最终权益</div>
                </div>
                <div>
                  <div className="text-lg font-bold text-ink-primary">
                    {result.benchmark_return > 0 ? '+' : ''}{result.benchmark_return}%
                  </div>
                  <div className="text-xs text-ink-muted">基准收益</div>
                </div>
              </div>
            </div>
          </div>

          {/* 权益曲线 */}
          {chartData && (
            <div className="bg-base-2 rounded-2xl border border-base-4 p-5">
              <h3 className="font-semibold text-ink-primary mb-4">权益曲线</h3>
              <div className="h-64">
                <Line data={chartData} options={chartOptions} />
              </div>
            </div>
          )}

          {/* 交易明细 */}
          {result.trades && result.trades.length > 0 && (
            <div className="bg-base-2 rounded-2xl border border-base-4 overflow-hidden">
              <div className="px-5 py-3 border-b border-base-4">
                <h3 className="font-semibold text-ink-primary">交易明细</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-base-4 bg-base-2">
                      <th className="text-left px-4 py-2 text-xs text-ink-muted">日期</th>
                      <th className="text-center px-4 py-2 text-xs text-ink-muted">方向</th>
                      <th className="text-right px-4 py-2 text-xs text-ink-muted">价格</th>
                      <th className="text-right px-4 py-2 text-xs text-ink-muted">数量</th>
                      <th className="text-right px-4 py-2 text-xs text-ink-muted">金额</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.trades.map((t, i) => (
                      <tr key={i} className="border-b border-gray-50">
                        <td className="px-4 py-2 text-ink-secondary">{t.date}</td>
                        <td className="px-4 py-2 text-center">
                          <span className={`px-2 py-0.5 rounded text-xs font-medium
                            ${t.type === 'buy' ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600'}`}>
                            {t.type === 'buy' ? '买入' : '卖出'}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-right text-ink-primary">¥{t.price}</td>
                        <td className="px-4 py-2 text-right text-ink-secondary">{t.shares}股</td>
                        <td className="px-4 py-2 text-right text-ink-primary">
                          ¥{(t.cost || t.revenue || 0).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 多策略对比图表 */}
          {compareChartData && (
            <div className="bg-base-2 rounded-2xl border border-base-4 p-5">
              <h3 className="font-semibold text-ink-primary mb-4">多策略对比</h3>
              <div className="h-72">
                <Line data={compareChartData} options={chartOptions} />
              </div>
              <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
                {Object.entries(compareResults).map(([k, v]) => (
                  <div key={k} className="p-3 bg-base-2 rounded-lg">
                    <div className="text-xs text-ink-muted">{STRATEGIES.find(s => s.id === k)?.name || k}</div>
                    <div className={`font-bold ${(v.total_return || 0) >= 0 ? 'text-red-500' : 'text-green-500'}`}>
                      {v.total_return > 0 ? '+' : ''}{v.total_return}%
                    </div>
                    <div className="text-xs text-ink-muted">夏普: {v.sharpe_ratio?.toFixed(2)} | 回撤: {v.max_drawdown}%</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {result?.error && (
        <div className="bg-red-50 border border-red-100 text-red-600 rounded-xl p-4 text-sm">
          <AlertTriangle className="w-4 h-4 inline mr-2" />
          {result.error}
        </div>
      )}
    </div>
  )
}
