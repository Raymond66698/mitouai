import { useState, useEffect, useCallback } from 'react'
import {
  Star, Plus, Trash2, TrendingUp, TrendingDown, Loader2, RefreshCw,
  Briefcase, List, DollarSign, ShoppingCart, ArrowUpDown, ChevronRight,
  AlertCircle, BarChart3, Clock, Search, X, CheckCircle, Edit3,
} from 'lucide-react'

export default function Watchlist() {
  const [tab, setTab] = useState('watchlist')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const token = localStorage.getItem('mitouai_token')
  const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }

  // 自选股
  const [quotes, setQuotes] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [searching, setSearching] = useState(false)
  const [showAdd, setShowAdd] = useState(false)

  // 组合
  const [portfolios, setPortfolios] = useState([])
  const [activePf, setActivePf] = useState(null)
  const [pfSummary, setPfSummary] = useState(null)
  const [showTradeForm, setShowTradeForm] = useState(false)
  const [tradeForm, setTradeForm] = useState({ action: 'buy', ticker: '', name: '', quantity: 100, price: 0 })
  const [showNewPf, setShowNewPf] = useState(false)
  const [newPfName, setNewPfName] = useState('')

  // 自选股数据
  const fetchQuotes = useCallback(async () => {
    try {
      const res = await fetch('/api/watchlist/watchlists/quotes', { headers })
      const data = await res.json()
      setQuotes(data.quotes || [])
    } catch (e) {
      console.error('fetchQuotes error:', e)
    }
  }, [])

  // 组合列表
  const fetchPortfolios = useCallback(async () => {
    try {
      const res = await fetch('/api/watchlist/portfolios', { headers })
      const data = await res.json()
      setPortfolios(data.portfolios || [])
      if (data.portfolios?.length && !activePf) {
        setActivePf(data.portfolios[0].id)
      }
    } catch (e) {
      console.error('fetchPortfolios error:', e)
    }
  }, [])

  // 组合详情
  const fetchPfDetail = useCallback(async (pfId) => {
    if (!pfId) return
    try {
      const res = await fetch(`/api/watchlist/portfolios/${pfId}`, { headers })
      const data = await res.json()
      setPfSummary(data)
    } catch (e) {
      console.error('fetchPfDetail error:', e)
    }
  }, [])

  useEffect(() => {
    const init = async () => {
      setLoading(true)
      await Promise.all([fetchQuotes(), fetchPortfolios()])
      setLoading(false)
    }
    init()
  }, [fetchQuotes, fetchPortfolios])

  useEffect(() => {
    if (activePf) fetchPfDetail(activePf)
  }, [activePf, fetchPfDetail])

  // 搜索股票
  const searchStocks = async (q) => {
    setSearchQuery(q)
    if (q.length < 1) { setSearchResults([]); return }
    setSearching(true)
    try {
      const res = await fetch(`/api/market/search?q=${encodeURIComponent(q)}`, { headers })
      const data = await res.json()
      setSearchResults(data.results || [])
    } catch (e) {}
    setSearching(false)
  }

  // 添加自选
  const addStock = async (ticker, name) => {
    try {
      await fetch('/api/watchlist/watchlists/add', {
        method: 'POST', headers,
        body: JSON.stringify({ ticker, name }),
      })
      await fetchQuotes()
      setShowAdd(false)
      setSearchQuery('')
      setSearchResults([])
    } catch (e) {
      alert('添加失败：' + e.message)
    }
  }

  // 移除自选
  const removeStock = async (ticker) => {
    try {
      await fetch('/api/watchlist/watchlists/remove', {
        method: 'POST', headers,
        body: JSON.stringify({ list_id: '', ticker }),
      })
      await fetchQuotes()
    } catch (e) {
      alert('移除失败：' + e.message)
    }
  }

  // 创建组合
  const createPortfolio = async () => {
    if (!newPfName.trim()) return
    try {
      await fetch('/api/watchlist/portfolios', {
        method: 'POST', headers,
        body: JSON.stringify({ name: newPfName.trim(), initial_cash: 100000 }),
      })
      setShowNewPf(false)
      setNewPfName('')
      await fetchPortfolios()
    } catch (e) {
      alert('创建失败：' + e.message)
    }
  }

  // 交易
  const executeTrade = async () => {
    if (!tradeForm.ticker || !tradeForm.price || !tradeForm.quantity) {
      alert('请填写完整信息')
      return
    }
    try {
      const res = await fetch('/api/watchlist/portfolios/trade', {
        method: 'POST', headers,
        body: JSON.stringify({
          portfolio_id: activePf,
          ticker: tradeForm.ticker,
          name: tradeForm.name || tradeForm.ticker,
          action: tradeForm.action,
          quantity: tradeForm.quantity,
          price: tradeForm.price,
        }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || '交易失败')
      }
      setShowTradeForm(false)
      await fetchPfDetail(activePf)
    } catch (e) {
      alert('交易失败：' + e.message)
    }
  }

  // 填充交易表单（从搜索选股）
  const fillTradeForm = (ticker, name) => {
    setTradeForm(prev => ({ ...prev, ticker, name }))
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto">
      {/* 头部 */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-ink-primary">我的投资</h1>
        <div className="flex gap-1 bg-base-3 rounded-xl p-1">
          <button
            onClick={() => setTab('watchlist')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all
              ${tab === 'watchlist' ? 'bg-base-2 text-primary-700 shadow-card' : 'text-ink-muted hover:text-ink-secondary'}`}
          >
            <Star className="w-4 h-4" /> 自选股
          </button>
          <button
            onClick={() => setTab('portfolio')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all
              ${tab === 'portfolio' ? 'bg-base-2 text-primary-700 shadow-card' : 'text-ink-muted hover:text-ink-secondary'}`}
          >
            <Briefcase className="w-4 h-4" /> 模拟组合
          </button>
        </div>
      </div>

      {/* ═══════════════ 自选股 ═══════════════ */}
      {tab === 'watchlist' && (
        <>
          <div className="flex items-center gap-3 mb-4">
            <button
              onClick={() => setShowAdd(true)}
              className="flex items-center gap-1.5 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors"
            >
              <Plus className="w-4 h-4" /> 添加自选
            </button>
            <button onClick={fetchQuotes} className="p-2 text-ink-muted hover:text-ink-secondary rounded-lg hover:bg-base-3">
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>

          {/* 添加弹窗 */}
          {showAdd && (
            <div className="bg-base-2 rounded-2xl border border-base-4 shadow-lg p-4 mb-4">
              <div className="flex items-center gap-2 mb-3">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-muted" />
                  <input
                    type="text" value={searchQuery}
                    onChange={e => searchStocks(e.target.value)}
                    placeholder="搜索股票名称或代码..."
                    className="w-full pl-10 pr-4 py-2.5 border border-base-4 rounded-xl focus:border-primary-400 focus:ring-2 focus:ring-primary-100 outline-none text-sm"
                    autoFocus
                  />
                </div>
                <button onClick={() => { setShowAdd(false); setSearchQuery(''); setSearchResults([]) }}
                  className="p-2 text-ink-muted hover:text-ink-secondary rounded-lg hover:bg-base-3">
                  <X className="w-4 h-4" />
                </button>
              </div>
              {searching && <Loader2 className="w-5 h-5 animate-spin text-primary-500 mx-auto my-3" />}
              {searchResults.length > 0 && (
                <div className="max-h-60 overflow-y-auto space-y-1">
                  {searchResults.map((r, i) => (
                    <button
                      key={i} onClick={() => addStock(r.code, r.name)}
                      className="w-full flex items-center justify-between px-3 py-2 rounded-lg hover:bg-base-3 transition-colors text-left"
                    >
                      <div>
                        <span className="text-sm font-medium text-ink-primary">{r.name}</span>
                        <span className="text-xs text-ink-muted ml-2">{r.code}</span>
                      </div>
                      <Plus className="w-4 h-4 text-primary-500" />
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 自选列表 */}
          <div className="bg-base-2 rounded-2xl border border-base-4 shadow-card overflow-hidden">
            {quotes.length === 0 ? (
              <div className="p-12 text-center text-ink-muted">
                <Star className="w-12 h-12 mx-auto mb-3" />
                <p className="text-sm">还没有添加自选股票</p>
                <button onClick={() => setShowAdd(true)}
                  className="mt-3 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700">
                  添加自选
                </button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="bg-base-2 text-xs text-ink-muted">
                      <th className="text-left px-4 py-3 font-medium">股票</th>
                      <th className="text-right px-4 py-3 font-medium">最新价</th>
                      <th className="text-right px-4 py-3 font-medium">涨跌幅</th>
                      <th className="text-right px-4 py-3 font-medium hidden md:table-cell">成交额</th>
                      <th className="text-right px-4 py-3 font-medium hidden md:table-cell">市盈率</th>
                      <th className="text-right px-4 py-3 font-medium hidden sm:table-cell">总市值</th>
                      <th className="text-center px-4 py-3 font-medium w-16"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-base-4">
                    {quotes.map((q, i) => (
                      <tr key={i} className="hover:bg-base-3 transition-colors">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <div className="w-8 h-8 bg-gradient-to-br from-primary-100 to-purple-100 rounded-lg flex items-center justify-center text-xs font-bold text-primary-600">
                              {q.ticker?.split('.')[0]?.slice(-2)}
                            </div>
                            <div>
                              <div className="text-sm font-medium text-ink-primary">{q.name}</div>
                              <div className="text-xs text-ink-muted">{q.ticker}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-right text-sm font-semibold text-ink-primary">
                          {q.price ? q.price.toFixed(2) : '--'}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <span className={`inline-flex items-center gap-0.5 text-sm font-semibold
                            ${q.change_pct >= 0 ? 'text-red-500' : 'text-green-500'}`}>
                            {q.change_pct >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                            {q.change_pct > 0 ? '+' : ''}{q.change_pct?.toFixed(2)}%
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right text-sm text-ink-secondary hidden md:table-cell">
                          {q.amount ? (q.amount / 1e8).toFixed(2) + '亿' : '--'}
                        </td>
                        <td className="px-4 py-3 text-right text-sm text-ink-secondary hidden md:table-cell">
                          {q.pe ? q.pe.toFixed(1) : '--'}
                        </td>
                        <td className="px-4 py-3 text-right text-sm text-ink-secondary hidden sm:table-cell">
                          {q.total_mv ? (q.total_mv / 1e8).toFixed(0) + '亿' : '--'}
                        </td>
                        <td className="px-2 py-3 text-center">
                          <button onClick={() => removeStock(q.ticker)}
                            className="p-1.5 text-ink-muted hover:text-red-500 rounded-lg hover:bg-red-50 transition-all">
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}

      {/* ═══════════════ 模拟组合 ═══════════════ */}
      {tab === 'portfolio' && (
        <div className="grid lg:grid-cols-4 gap-6">
          {/* 左侧：组合列表 */}
          <div className="lg:col-span-1 space-y-3">
            <button onClick={() => setShowNewPf(true)}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 border-2 border-dashed border-base-4 rounded-xl text-sm text-ink-muted hover:border-primary-300 hover:text-primary-600 transition-all">
              <Plus className="w-4 h-4" /> 新建组合
            </button>

            {showNewPf && (
              <div className="bg-base-2 rounded-xl border border-base-4 p-3 flex gap-2">
                <input
                  type="text" value={newPfName}
                  onChange={e => setNewPfName(e.target.value)}
                  placeholder="组合名称"
                  className="flex-1 px-3 py-2 border border-base-4 rounded-lg text-sm outline-none focus:border-primary-400"
                  onKeyDown={e => e.key === 'Enter' && createPortfolio()}
                  autoFocus
                />
                <button onClick={createPortfolio}
                  className="px-3 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700">
                  创建
                </button>
              </div>
            )}

            {portfolios.map(pf => (
              <button
                key={pf.id}
                onClick={() => setActivePf(pf.id)}
                className={`w-full text-left p-3 rounded-xl border transition-all
                  ${activePf === pf.id
                    ? 'border-primary-300 bg-primary-50'
                    : 'border-base-4 bg-base-2 hover:border-base-4'}`}
              >
                <div className="font-semibold text-sm text-ink-primary">{pf.name}</div>
                <div className="text-xs text-ink-muted mt-0.5">创建于 {pf.created_at?.slice(0, 10)}</div>
              </button>
            ))}
          </div>

          {/* 右侧：组合详情 */}
          <div className="lg:col-span-3 space-y-6">
            {!activePf || !pfSummary ? (
              <div className="bg-base-2 rounded-2xl border border-base-4 p-12 text-center text-ink-muted">
                <Briefcase className="w-12 h-12 mx-auto mb-3" />
                <p>选择一个组合或新建组合开始</p>
              </div>
            ) : (
              <>
                {/* 组合总览 */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="bg-base-2 rounded-xl border border-base-4 p-4">
                    <div className="text-xs text-ink-muted mb-1">总资产</div>
                    <div className="text-xl font-bold text-ink-primary">
                      ¥{pfSummary.total_assets?.toLocaleString('zh-CN')}
                    </div>
                  </div>
                  <div className="bg-base-2 rounded-xl border border-base-4 p-4">
                    <div className="text-xs text-ink-muted mb-1">持仓市值</div>
                    <div className="text-xl font-bold text-ink-primary">
                      ¥{pfSummary.total_market_value?.toLocaleString('zh-CN')}
                    </div>
                  </div>
                  <div className="bg-base-2 rounded-xl border border-base-4 p-4">
                    <div className="text-xs text-ink-muted mb-1">可用资金</div>
                    <div className="text-xl font-bold text-ink-primary">
                      ¥{pfSummary.cash?.toLocaleString('zh-CN')}
                    </div>
                  </div>
                  <div className="bg-base-2 rounded-xl border border-base-4 p-4">
                    <div className="text-xs text-ink-muted mb-1">总盈亏</div>
                    <div className={`text-xl font-bold ${pfSummary.total_pnl >= 0 ? 'text-red-500' : 'text-green-500'}`}>
                      {pfSummary.total_pnl > 0 ? '+' : ''}¥{pfSummary.total_pnl?.toLocaleString('zh-CN')}
                      <span className="text-sm ml-1">
                        ({pfSummary.total_pnl_pct > 0 ? '+' : ''}{pfSummary.total_pnl_pct?.toFixed(2)}%)
                      </span>
                    </div>
                  </div>
                </div>

                {/* 交易按钮 */}
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => { setShowTradeForm(true); setTradeForm({ action: 'buy', ticker: '', name: '', quantity: 100, price: 0 }) }}
                    className="flex items-center gap-2 px-4 py-2 bg-red-500 text-white rounded-lg text-sm font-medium hover:bg-red-600 transition-colors"
                  >
                    <ShoppingCart className="w-4 h-4" /> 买入
                  </button>
                  <button
                    onClick={() => { setShowTradeForm(true); setTradeForm({ action: 'sell', ticker: '', name: '', quantity: 100, price: 0 }) }}
                    className="flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded-lg text-sm font-medium hover:bg-green-600 transition-colors"
                  >
                    <ArrowUpDown className="w-4 h-4" /> 卖出
                  </button>
                  <button onClick={() => fetchPfDetail(activePf)}
                    className="p-2 text-ink-muted hover:text-ink-secondary rounded-lg hover:bg-base-3">
                    <RefreshCw className="w-4 h-4" />
                  </button>
                </div>

                {/* 交易弹窗 */}
                {showTradeForm && (
                  <div className="bg-base-2 rounded-2xl border border-base-4 shadow-lg p-5">
                    <h3 className="font-semibold text-ink-primary mb-3 flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded text-xs font-bold text-white
                        ${tradeForm.action === 'buy' ? 'bg-red-500' : 'bg-green-500'}`}>
                        {tradeForm.action === 'buy' ? '买入' : '卖出'}
                      </span>
                      记录交易
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
                      <div>
                        <label className="block text-xs text-ink-muted mb-1">股票代码</label>
                        <input type="text" value={tradeForm.ticker}
                          onChange={e => setTradeForm(p => ({ ...p, ticker: e.target.value }))}
                          className="w-full px-3 py-2 border border-base-4 rounded-lg text-sm outline-none focus:border-primary-400"
                          placeholder="如 600519.SS" />
                      </div>
                      <div>
                        <label className="block text-xs text-ink-muted mb-1">股票名称</label>
                        <input type="text" value={tradeForm.name}
                          onChange={e => setTradeForm(p => ({ ...p, name: e.target.value }))}
                          className="w-full px-3 py-2 border border-base-4 rounded-lg text-sm outline-none focus:border-primary-400"
                          placeholder="可选" />
                      </div>
                      <div>
                        <label className="block text-xs text-ink-muted mb-1">数量（股）</label>
                        <input type="number" value={tradeForm.quantity}
                          onChange={e => setTradeForm(p => ({ ...p, quantity: parseInt(e.target.value) || 0 }))}
                          className="w-full px-3 py-2 border border-base-4 rounded-lg text-sm outline-none focus:border-primary-400" />
                      </div>
                      <div>
                        <label className="block text-xs text-ink-muted mb-1">成交价格</label>
                        <input type="number" step="0.01" value={tradeForm.price}
                          onChange={e => setTradeForm(p => ({ ...p, price: parseFloat(e.target.value) || 0 }))}
                          className="w-full px-3 py-2 border border-base-4 rounded-lg text-sm outline-none focus:border-primary-400" />
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button onClick={executeTrade}
                        className={`px-6 py-2 rounded-lg text-sm font-medium text-white transition-colors
                          ${tradeForm.action === 'buy' ? 'bg-red-500 hover:bg-red-600' : 'bg-green-500 hover:bg-green-600'}`}>
                        确认{tradeForm.action === 'buy' ? '买入' : '卖出'}
                      </button>
                      <button onClick={() => setShowTradeForm(false)}
                        className="px-4 py-2 text-sm text-ink-muted hover:text-ink-secondary rounded-lg hover:bg-base-3">
                        取消
                      </button>
                    </div>
                  </div>
                )}

                {/* 持仓列表 */}
                <div className="bg-base-2 rounded-2xl border border-base-4 shadow-card overflow-hidden">
                  <div className="px-5 py-3 border-b border-base-4 font-semibold text-sm text-ink-primary">
                    当前持仓 ({pfSummary.holdings?.length || 0})
                  </div>
                  {!pfSummary.holdings?.length ? (
                    <div className="p-8 text-center text-ink-muted text-sm">暂无持仓，记录一笔交易开始吧</div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="bg-base-2 text-xs text-ink-muted">
                            <th className="text-left px-4 py-2 font-medium">股票</th>
                            <th className="text-right px-4 py-2 font-medium">持仓</th>
                            <th className="text-right px-4 py-2 font-medium">成本价</th>
                            <th className="text-right px-4 py-2 font-medium">现价</th>
                            <th className="text-right px-4 py-2 font-medium">市值</th>
                            <th className="text-right px-4 py-2 font-medium">盈亏</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-base-4">
                          {pfSummary.holdings.map((h, i) => (
                            <tr key={i} className="hover:bg-base-3 transition-colors">
                              <td className="px-4 py-3">
                                <div className="flex items-center gap-2">
                                  <div className="w-7 h-7 bg-gradient-to-br from-primary-100 to-purple-100 rounded-lg flex items-center justify-center text-xs font-bold text-primary-600">
                                    {h.ticker?.split('.')[0]?.slice(-2)}
                                  </div>
                                  <div>
                                    <div className="text-sm font-medium text-ink-primary">{h.name}</div>
                                    <div className="text-xs text-ink-muted">{h.ticker}</div>
                                  </div>
                                </div>
                              </td>
                              <td className="px-4 py-3 text-right text-sm text-ink-primary">{h.quantity}股</td>
                              <td className="px-4 py-3 text-right text-sm text-ink-secondary">¥{h.avg_price?.toFixed(2)}</td>
                              <td className="px-4 py-3 text-right text-sm text-ink-primary">¥{h.current_price?.toFixed(2)}</td>
                              <td className="px-4 py-3 text-right text-sm text-ink-primary">¥{h.current_value?.toLocaleString('zh-CN')}</td>
                              <td className="px-4 py-3 text-right">
                                <span className={`text-sm font-semibold ${h.pnl >= 0 ? 'text-red-500' : 'text-green-500'}`}>
                                  {h.pnl > 0 ? '+' : ''}¥{h.pnl?.toLocaleString('zh-CN')}
                                </span>
                                <div className={`text-xs ${h.pnl_pct >= 0 ? 'text-red-500' : 'text-green-500'}`}>
                                  {h.pnl_pct > 0 ? '+' : ''}{h.pnl_pct?.toFixed(2)}%
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
