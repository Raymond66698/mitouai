import { useState, useEffect, useRef } from 'react'
import { useSearchParams, useParams } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import API_BASE from '../api'
import { Search, Loader2, CheckCircle2, XCircle, Download, RefreshCw } from 'lucide-react'

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
  const eventSourceRef = useRef(null)

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
          strategy_id: null,
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
    } catch { }
  }

  const reset = () => {
    setStatus('idle')
    setTaskId(null)
    setReport(null)
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
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
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
            <h2 className="text-lg font-semibold text-gray-900 mb-3">分析摘要</h2>
            <p className="text-gray-600 leading-relaxed mb-6">{report.summary}</p>

            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="bg-gray-50 rounded-xl p-4">
                <span className="text-sm text-gray-500">技术指标</span>
                <div className={`mt-1 font-medium ${report.indicators_available ? 'text-green-600' : 'text-gray-400'}`}>
                  {report.indicators_available ? '✓ 已分析' : '✗ 暂不可用'}
                </div>
              </div>
              <div className="bg-gray-50 rounded-xl p-4">
                <span className="text-sm text-gray-500">基本面</span>
                <div className={`mt-1 font-medium ${report.fundamentals_available ? 'text-green-600' : 'text-gray-400'}`}>
                  {report.fundamentals_available ? '✓ 已分析' : '✗ 暂不可用'}
                </div>
              </div>
              <div className="bg-gray-50 rounded-xl p-4">
                <span className="text-sm text-gray-500">新闻舆情</span>
                <div className={`mt-1 font-medium ${report.news_available ? 'text-green-600' : 'text-gray-400'}`}>
                  {report.news_available ? '✓ 已分析' : '✗ 暂不可用'}
                </div>
              </div>
              <div className="bg-gray-50 rounded-xl p-4">
                <span className="text-sm text-gray-500">宏观环境</span>
                <div className={`mt-1 font-medium ${report.global_news_available ? 'text-green-600' : 'text-gray-400'}`}>
                  {report.global_news_available ? '✓ 已分析' : '✗ 暂不可用'}
                </div>
              </div>
            </div>

            {report.raw_sections?.indicators && (
              <div className="border-t border-gray-100 pt-6">
                <h3 className="font-semibold text-gray-900 mb-3">技术指标详情</h3>
                <pre className="text-sm text-gray-600 bg-gray-50 rounded-xl p-4 overflow-x-auto whitespace-pre-wrap">
                  {report.raw_sections.indicators}
                </pre>
              </div>
            )}

            <div className="flex gap-3 mt-8">
              <button onClick={reset} className="flex items-center gap-2 px-6 py-2.5 bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 transition-all">
                <RefreshCw className="w-4 h-4" />
                新建分析
              </button>
              <button className="flex items-center gap-2 px-6 py-2.5 border-2 border-gray-200 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-all">
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
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-10 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-primary-500 border-t-transparent mx-auto mb-6"></div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">多智能体分析中...</h2>
          <p className="text-gray-500 mb-6">
            {progress.message || `第 ${progress.step}/${progress.total} 步`}
          </p>
          <div className="w-full bg-gray-100 rounded-full h-2 mb-4">
            <div
              className="bg-primary-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${(progress.step / progress.total) * 100}%` }}
            ></div>
          </div>
          <p className="text-xs text-gray-400">
            正在调用 TradingAgents 16角色多Agent分析管道...
          </p>
        </div>
      </div>
    )
  }

  if (status === 'failed') {
    return (
      <div className="max-w-xl mx-auto mt-10">
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-10 text-center">
          <XCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-900 mb-2">分析失败</h2>
          <p className="text-gray-500 mb-6">{error || '未知错误'}</p>
          <button onClick={reset} className="px-6 py-2.5 bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 transition-all">
            重试
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">投研分析</h1>

      {/* Search */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 mb-6">
        <div className="flex gap-3 mb-4">
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && (selectedStock ? startAnalysis() : searchStocks())}
            placeholder="输入股票名称或代码搜索（如：贵州茅台 / 600519）"
            className="flex-1 px-4 py-3 border-2 border-gray-100 rounded-xl focus:border-primary-400 focus:ring-2 focus:ring-primary-100 outline-none"
          />
          <button
            onClick={searchStocks}
            className="px-5 py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-all"
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
                    : 'border-gray-100 hover:border-gray-200 bg-white'
                  }`}
              >
                <div>
                  <span className="font-medium text-gray-900">{s.name}</span>
                  <span className="text-sm text-gray-400 ml-2">{s.code}</span>
                </div>
                <span className="text-xs text-gray-400">{s.exchange}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Options */}
      {selectedStock && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <span className="text-lg font-semibold text-gray-900">{selectedStock.name}</span>
              <span className="text-sm text-gray-400 ml-2">{selectedStock.code}</span>
            </div>
            <span className="text-xs text-gray-400">{selectedStock.exchange}</span>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">多空辩论轮数</label>
            <div className="flex gap-2">
              {[1, 2, 3].map(n => (
                <button
                  key={n}
                  onClick={() => setDebateRounds(n)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all
                    ${debateRounds === n
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                >
                  {n} 轮
                </button>
              ))}
            </div>
          </div>

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
