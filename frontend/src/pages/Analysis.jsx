import { useState, useEffect, useRef } from 'react'
import { useSearchParams, useParams } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import API_BASE from '../api'
import { Radar } from 'react-chartjs-2'
import {
  Chart as ChartJS, RadialLinearScale, PointElement, LineElement,
  Filler, Tooltip, Legend
} from 'chart.js'
import { Search, Loader2, CheckCircle2, XCircle, Download, RefreshCw, TrendingUp } from 'lucide-react'

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend)

export default function Analysis() {
  const { token, user, refreshUser } = useAuth()
  const [searchParams] = useSearchParams()
  const { taskId: urlTaskId } = useParams()
  const [query, setQuery] = useState(searchParams.get('q') || '')
  const [results, setResults] = useState([])
  const [selectedStock, setSelectedStock] = useState(null)
  const [taskId, setTaskId] = useState(urlTaskId || null)
  const [status, setStatus] = useState('idle')
  const [progress, setProgress] = useState({ step: 0, total: 8, message: '' })
  const [report, setReport] = useState(null)
  const [error, setError] = useState('')
  const [debateRounds, setDebateRounds] = useState(1)
  const [strategyId, setStrategyId] = useState(searchParams.get('strategy_id') || null)
  const [selectedStrategy, setSelectedStrategy] = useState(null)
  const [snowflake, setSnowflake] = useState(null)
  const eventSourceRef = useRef(null)

  // 加载 URL 中指定的策略信息
  useEffect(() => {
    const sid = searchParams.get('strategy_id')
    if (sid) {
      setStrategyId(sid)
      fetch(`/api/strategies`)
        .then(r => r.json())
        .then(data => {
          const found = (data.strategies || []).find(s => s.id === sid)
          if (found) setSelectedStrategy(found)
        })
        .catch(() => {})
    }
  }, [searchParams])

  useEffect(() => {
    if (urlTaskId) {
      loadExistingTask(urlTaskId)
    }
  }, [urlTaskId])

  const loadExistingTask = async (tid) => {
    try {
      const r = await fetch(`${API_BASE}/analysis/status/${tid}`)
      const task = await r.json()
      if (task.status === 'completed') {
        setStatus('completed')
        const rr = await fetch(`${API_BASE}/analysis/report/${tid}`)
        setReport((await rr.json()).report)
      } else if (task.status === 'failed') {
        setStatus('failed')
        setError(task.error)
      } else {
        setStatus('running')
        streamProgress(tid)
      }
    } catch { setStatus('failed') }
  }

  const searchStocks = async () => {
    if (!query.trim()) return
    try {
      const r = await fetch(`${API_BASE}/analysis/search?q=${encodeURIComponent(query.trim())}`)
      const data = await r.json()
      setResults(data.results || [])
    } catch { setResults([]) }
  }

  const startAnalysis = async () => {
    if (!selectedStock) return
    setStatus('starting')
    setError('')
    try {
      const r = await fetch('/api/analysis/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          ticker: selectedStock.code,
          trade_date: null,
          debate_rounds: debateRounds,
          risk_rounds: 1,
          strategy_id: strategyId,
          model: 'default',
        })
      })
      const task = await r.json()
      if (!r.ok) throw new Error(task.detail || '启动失败')
      setTaskId(task.task_id)
      setStatus('running')
      refreshUser?.()
      streamProgress(task.task_id)
    } catch (err) {
      setError(err.message)
      setStatus('idle')
    }
  }

  const streamProgress = (tid) => {
    if (eventSourceRef.current) eventSourceRef.current.close()
    const es = new EventSource(`${API_BASE}/analysis/stream/${tid}`)
    eventSourceRef.current = es

    es.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        const d = msg.data || {}

        if (msg.event === 'progress') {
          setProgress(d)
        } else if (msg.event === 'complete') {
          setStatus('completed')
          fetchReport(tid)
          es.close()
        } else if (msg.event === 'error') {
          setStatus('failed')
          setError(d.message || '分析失败')
          es.close()
        }
      } catch { }
    }

    es.onerror = () => {
      es.close()
      if (status !== 'completed' && status !== 'failed') {
        setError('连接中断，请刷新页面')
        setStatus('failed')
      }
    }
  }

  const fetchReport = async (tid) => {
    try {
      const r = await fetch(`${API_BASE}/analysis/report/${tid}`)
      const data = await r.json()
      setReport(data.report)
      // 获取五维分析数据
      if (data.report?.ticker) {
        fetch(`${API_BASE}/market/snowflake/${data.report.ticker}`)
          .then(r => r.json())
          .then(d => { if (!d.error) setSnowflake(d) })
          .catch(() => {})
      }
    } catch { }
  }

  const reset = () => {
    setStatus('idle')
    setTaskId(null)
    setReport(null)
    setSnowflake(null)
    setError('')
    setProgress({ step: 0, total: 8, message: '' })
    setSelectedStock(null)
    setResults([])
    if (eventSourceRef.current) eventSourceRef.current.close()
  }

  const getDecisionColor = (d) => {
    if (d === 'BUY') return 'text-red-600 bg-red-50 border-red-200'
    if (d === 'SELL') return 'text-green-600 bg-green-50 border-green-200'
    return 'text-yellow-600 bg-yellow-50 border-yellow-200'
  }

  const getDecisionText = (d) => {
    if (d === 'BUY') return '买入'
    if (d === 'SELL') return '卖出'
    return '持有'
  }

  if (status === 'completed' && report) {
    return (
      <div className="max-w-3xl mx-auto">
        <div className="bg-base-2 rounded-2xl border border-base-4 shadow-card overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-primary-600 to-purple-600 text-white p-8">
            <div className="flex items-center justify-between mb-4">
              <h1 className="text-2xl font-bold">{report.ticker}</h1>
              <span className={`px-4 py-1.5 rounded-full font-bold text-lg border ${getDecisionColor(report.decision)}`}>
                {getDecisionText(report.decision)}
              </span>
            </div>
            <div className="flex items-center gap-6 text-primary-100 text-sm">
              <span>分析日期：{report.trade_date}</span>
              <span>最新价：{report.latest_price}</span>
              <span>数据点：{report.data_points}</span>
            </div>
          </div>

          {/* Summary */}
          <div className="p-8">
            <h2 className="text-lg font-semibold text-ink-primary mb-3">分析摘要</h2>
            <p className="text-ink-secondary leading-relaxed mb-6">{report.summary}</p>

            {/* 五维雷达图 */}
            {snowflake?.dimensions && (
              <div className="mb-6 bg-gradient-to-br from-gray-50 to-white rounded-xl border border-base-4 p-5">
                <h3 className="text-sm font-semibold text-ink-secondary mb-3 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-primary-500" />
                  五维综合评价
                  <span className="ml-auto text-lg font-bold text-primary-600">
                    综合评分：{snowflake.composite_score}
                  </span>
                </h3>
                <div className="h-56">
                  <Radar
                    data={{
                      labels: Object.values(snowflake.dimensions).map(d => d.label),
                      datasets: [{
                        label: '得分',
                        data: Object.values(snowflake.dimensions).map(d => d.score),
                        backgroundColor: 'rgba(124, 58, 237, 0.15)',
                        borderColor: 'rgba(124, 58, 237, 0.8)',
                        pointBackgroundColor: '#C8963E',
                        pointBorderColor: '#fff',
                        pointHoverRadius: 6,
                        borderWidth: 2,
                      }],
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      scales: {
                        r: {
                          beginAtZero: true,
                          max: 100,
                          ticks: { stepSize: 20, font: { size: 9 }, backdropColor: 'transparent' },
                          pointLabels: { font: { size: 11, weight: '500' } },
                          grid: { color: '#F0E6D3' },
                        },
                      },
                      plugins: {
                        legend: { display: false },
                        tooltip: { callbacks: { label: ctx => `得分: ${ctx.raw}` } },
                      },
                    }}
                  />
                </div>
                <div className="grid grid-cols-5 gap-1 mt-2">
                  {Object.entries(snowflake.dimensions).map(([key, dim]) => (
                    <div key={key} className="text-center">
                      <div className={`text-xs font-bold ${dim.score >= 70 ? 'text-emerald-500' : dim.score >= 40 ? 'text-amber-500' : 'text-red-400'}`}>
                        {dim.score}
                      </div>
                      <div className="text-[10px] text-ink-muted">{dim.label}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="bg-base-2 rounded-xl p-4">
                <span className="text-sm text-ink-muted">技术指标</span>
                <div className={`mt-1 font-medium ${report.indicators_available ? 'text-green-600' : 'text-ink-muted'}`}>
                  {report.indicators_available ? '✓ 已分析' : '✗ 暂不可用'}
                </div>
              </div>
              <div className="bg-base-2 rounded-xl p-4">
                <span className="text-sm text-ink-muted">基本面</span>
                <div className={`mt-1 font-medium ${report.fundamentals_available ? 'text-green-600' : 'text-ink-muted'}`}>
                  {report.fundamentals_available ? '✓ 已分析' : '✗ 暂不可用'}
                </div>
              </div>
              <div className="bg-base-2 rounded-xl p-4">
                <span className="text-sm text-ink-muted">新闻舆情</span>
                <div className={`mt-1 font-medium ${report.news_available ? 'text-green-600' : 'text-ink-muted'}`}>
                  {report.news_available ? '✓ 已分析' : '✗ 暂不可用'}
                </div>
              </div>
              <div className="bg-base-2 rounded-xl p-4">
                <span className="text-sm text-ink-muted">宏观环境</span>
                <div className={`mt-1 font-medium ${report.global_news_available ? 'text-green-600' : 'text-ink-muted'}`}>
                  {report.global_news_available ? '✓ 已分析' : '✗ 暂不可用'}
                </div>
              </div>
            </div>

            {report.raw_sections?.indicators && (
              <div className="border-t border-base-4 pt-6">
                <h3 className="font-semibold text-ink-primary mb-3">技术指标详情</h3>
                <pre className="text-sm text-ink-secondary bg-base-2 rounded-xl p-4 overflow-x-auto whitespace-pre-wrap">
                  {report.raw_sections.indicators}
                </pre>
              </div>
            )}

            <div className="flex gap-3 mt-8">
              <button onClick={reset} className="flex items-center gap-2 px-6 py-2.5 bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 transition-all">
                <RefreshCw className="w-4 h-4" />
                新建分析
              </button>
              <button className="flex items-center gap-2 px-6 py-2.5 border-2 border-base-4 text-ink-secondary rounded-xl font-medium hover:bg-base-3 transition-all">
                <Download className="w-4 h-4" />
                导出报告
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (status === 'running' || status === 'starting') {
    return (
      <div className="max-w-xl mx-auto mt-10">
        <div className="bg-base-2 rounded-2xl border border-base-4 shadow-card p-10 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-primary-500 border-t-transparent mx-auto mb-6"></div>
          <h2 className="text-xl font-bold text-ink-primary mb-2">多智能体分析中...</h2>
          <p className="text-ink-muted mb-6">
            {progress.message || `第 ${progress.step}/${progress.total} 步`}
          </p>
          <div className="w-full bg-base-3 rounded-full h-2 mb-4">
            <div
              className="bg-primary-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${(progress.step / progress.total) * 100}%` }}
            ></div>
          </div>
          <p className="text-xs text-ink-muted">
            正在调用 TradingAgents 16角色多Agent分析管道...
          </p>
        </div>
      </div>
    )
  }

  if (status === 'failed') {
    return (
      <div className="max-w-xl mx-auto mt-10">
        <div className="bg-base-2 rounded-2xl border border-base-4 shadow-card p-10 text-center">
          <XCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-ink-primary mb-2">分析失败</h2>
          <p className="text-ink-muted mb-6">{error || '未知错误'}</p>
          <button onClick={reset} className="px-6 py-2.5 bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 transition-all">
            重试
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-ink-primary mb-2">投研分析</h1>
      {selectedStrategy && (
        <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-indigo-50 border border-indigo-200 rounded-lg text-sm text-indigo-700 mb-6">
          <span className="text-lg leading-none">{selectedStrategy.icon}</span>
          <span className="font-medium">{selectedStrategy.name}</span>
          <button onClick={() => { setStrategyId(null); setSelectedStrategy(null) }} className="ml-2 text-indigo-400 hover:text-indigo-600">&times;</button>
        </div>
      )}

      {/* Search */}
      <div className="bg-base-2 rounded-2xl border border-base-4 shadow-card p-6 mb-6">
        <div className="flex gap-3 mb-4">
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && (selectedStock ? startAnalysis() : searchStocks())}
            placeholder="输入股票名称或代码搜索（如：贵州茅台 / 600519）"
            className="flex-1 px-4 py-3 border-2 border-base-4 rounded-xl focus:border-primary-400 focus:ring-2 focus:ring-primary-100 outline-none"
          />
          <button
            onClick={searchStocks}
            className="px-5 py-3 bg-base-3 text-ink-secondary rounded-xl font-medium hover:bg-gray-200 transition-all"
          >
            搜索
          </button>
        </div>

        {results.length > 0 && (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {results.map(s => (
              <button
                key={s.code}
                onClick={() => setSelectedStock(s)}
                className={`w-full text-left px-4 py-3 rounded-xl border transition-all flex items-center justify-between
                  ${selectedStock?.code === s.code
                    ? 'border-primary-400 bg-primary-50'
                    : 'border-base-4 hover:border-base-4 bg-base-2'
                  }`}
              >
                <div>
                  <span className="font-medium text-ink-primary">{s.name}</span>
                  <span className="text-sm text-ink-muted ml-2">{s.code}</span>
                </div>
                <span className="text-xs text-ink-muted">{s.exchange}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Options */}
      {selectedStock && (
        <div className="bg-base-2 rounded-2xl border border-base-4 shadow-card p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <span className="text-lg font-semibold text-ink-primary">{selectedStock.name}</span>
              <span className="text-sm text-ink-muted ml-2">{selectedStock.code}</span>
            </div>
            <span className="text-xs text-ink-muted">{selectedStock.exchange}</span>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-ink-secondary mb-2">多空辩论轮数</label>
            <div className="flex gap-2">
              {[1, 2, 3].map(n => (
                <button
                  key={n}
                  onClick={() => setDebateRounds(n)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all
                    ${debateRounds === n
                      ? 'bg-primary-600 text-white'
                      : 'bg-base-3 text-ink-secondary hover:bg-gray-200'
                    }`}
                >
                  {n} 轮
                </button>
              ))}
            </div>
          </div>

          {selectedStrategy && (
            <div className="mb-4 p-3 bg-indigo-50 border border-indigo-100 rounded-lg text-sm text-indigo-700">
              使用策略：<span className="font-semibold">{selectedStrategy.icon} {selectedStrategy.name}</span>
              <span className="text-indigo-400 ml-1">— {selectedStrategy.author}</span>
            </div>
          )}

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-100 text-red-600 rounded-lg text-sm">
              {error}
            </div>
          )}

          <button
            onClick={startAnalysis}
            className="w-full flex items-center justify-center gap-2 py-3 bg-primary-600 text-white rounded-xl font-semibold hover:bg-primary-700 transition-all"
          >
            <Search className="w-5 h-5" />
            启动多智能体分析（消耗 1 次配额）
          </button>
        </div>
      )}
    </div>
  )
}
