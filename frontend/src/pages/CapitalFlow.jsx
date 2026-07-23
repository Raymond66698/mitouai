import { useState, useEffect } from 'react'
import { API_BASE } from '../api'
import { TrendingUp, TrendingDown, ArrowUpRight, BarChart3 } from 'lucide-react'

export default function CapitalFlow() {
  const [northFlow, setNorthFlow] = useState(null)
  const [northStocks, setNorthStocks] = useState([])
  const [majorFlow, setMajorFlow] = useState(null)
  const [dragonTiger, setDragonTiger] = useState([])
  const [tab, setTab] = useState('north')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAll()
  }, [])

  const fetchAll = async () => {
    setLoading(true)
    const [nf, ns, mf, dt] = await Promise.allSettled([
      fetch(`${API_BASE}/capital/north-flow`).then(r => r.json()),
      fetch(`${API_BASE}/capital/north-flow/detail`).then(r => r.json()),
      fetch(`${API_BASE}/capital/major-flow`).then(r => r.json()),
      fetch(`${API_BASE}/capital/dragon-tiger`).then(r => r.json()),
    ])
    if (nf.status === 'fulfilled') setNorthFlow(nf.value)
    if (ns.status === 'fulfilled') setNorthStocks(ns.value.stocks || [])
    if (mf.status === 'fulfilled') setMajorFlow(mf.value)
    if (dt.status === 'fulfilled') setDragonTiger(dt.value.list || [])
    setLoading(false)
  }

  const tabs = [
    { key: 'north', label: '北向资金' },
    { key: 'major', label: '主力资金' },
    { key: 'dragon', label: '龙虎榜' },
  ]

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-ink-primary mb-6">资金流向</h1>
        <div className="grid grid-cols-3 gap-4 animate-pulse">
          {[1, 2, 3].map(i => <div key={i} className="h-32 bg-base-3 rounded-xl" />)}
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-ink-primary mb-6">资金流向</h1>

      {/* 北向资金概览 */}
      {northFlow && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-base-2 rounded-xl border border-base-4 p-5">
            <div className="text-sm text-ink-muted mb-1">今日北向资金</div>
            <div className={`text-2xl font-bold ${northFlow.net_flow >= 0 ? 'text-red-600' : 'text-green-600'}`}>
              {northFlow.net_flow >= 0 ? '+' : ''}{northFlow.net_flow} 亿
            </div>
            <div className="text-xs text-ink-muted mt-1">{northFlow.date}</div>
          </div>
          <div className="bg-base-2 rounded-xl border border-base-4 p-5">
            <div className="text-sm text-ink-muted mb-1">近20日累计</div>
            <div className={`text-2xl font-bold ${(northFlow.cumulative_20d || 0) >= 0 ? 'text-red-600' : 'text-green-600'}`}>
              {(northFlow.cumulative_20d || 0) >= 0 ? '+' : ''}{northFlow.cumulative_20d || 0} 亿
            </div>
            <div className="text-xs text-ink-muted mt-1">滚动20日</div>
          </div>
          <div className="bg-base-2 rounded-xl border border-base-4 p-5">
            <div className="text-sm text-ink-muted mb-1">近5日趋势</div>
            <div className="flex items-end gap-1 h-12 mt-1">
              {(northFlow.recent_5days || []).map((d, i) => {
                const h = Math.min(40, Math.abs(d.net_flow || 0) / 2)
                return (
                  <div key={i} className="flex-1 flex flex-col items-center">
                    <div
                      className={`w-full rounded-t ${(d.net_flow || 0) >= 0 ? 'bg-red-400' : 'bg-green-400'}`}
                      style={{ height: `${Math.max(4, h)}px` }}
                    />
                    <span className="text-[10px] text-ink-muted mt-1">{(d.date || '').slice(-5)}</span>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* Tab 切换 */}
      <div className="flex gap-1 bg-base-3 rounded-lg p-1 mb-6 w-fit">
        {tabs.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
              tab === t.key ? 'bg-base-2 text-primary-600 shadow-card' : 'text-ink-muted hover:text-ink-secondary'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* 北向资金明细 */}
      {tab === 'north' && (
        <div className="bg-base-2 rounded-xl border border-base-4 overflow-hidden">
          <div className="px-5 py-3 border-b border-gray-50">
            <h3 className="font-semibold text-ink-primary">北向资金个股净买入排行</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-xs text-ink-muted border-b border-gray-50">
                  <th className="text-left px-5 py-3">股票</th>
                  <th className="text-right px-5 py-3">净买入</th>
                  <th className="text-left px-5 py-3">通道</th>
                </tr>
              </thead>
              <tbody>
                {northStocks.map((s, i) => (
                  <tr key={i} className="border-b border-gray-50 hover:bg-base-3">
                    <td className="px-5 py-3">
                      <span className="font-medium text-ink-primary">{s.name}</span>
                      <span className="text-xs text-ink-muted ml-2">{s.code}</span>
                    </td>
                    <td className={`px-5 py-3 text-right font-medium ${(s.net_flow || 0) >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                      {(s.net_flow || 0) >= 0 ? '+' : ''}{(s.net_flow || 0).toFixed(0)} 万
                    </td>
                    <td className="px-5 py-3 text-ink-muted text-sm">{s.market}</td>
                  </tr>
                ))}
                {northStocks.length === 0 && (
                  <tr><td colSpan={3} className="text-center py-8 text-ink-muted">暂无数据</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 主力资金 */}
      {tab === 'major' && majorFlow && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-base-2 rounded-xl border border-base-4 p-4">
              <div className="text-xs text-ink-muted">主力净流入</div>
              <div className={`text-xl font-bold ${(majorFlow.summary?.main_net_inflow || 0) >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                {(majorFlow.summary?.main_net_inflow || 0) >= 0 ? '+' : ''}
                {(majorFlow.summary?.main_net_inflow || 0).toFixed(1)} 亿
              </div>
            </div>
            <div className="bg-base-2 rounded-xl border border-base-4 p-4">
              <div className="text-xs text-ink-muted">超大单净流入</div>
              <div className={`text-xl font-bold ${(majorFlow.summary?.super_large_net || 0) >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                {(majorFlow.summary?.super_large_net || 0).toFixed(1)} 亿
              </div>
            </div>
            <div className="bg-base-2 rounded-xl border border-base-4 p-4">
              <div className="text-xs text-ink-muted">大单净流入</div>
              <div className={`text-xl font-bold ${(majorFlow.summary?.large_net || 0) >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                {(majorFlow.summary?.large_net || 0).toFixed(1)} 亿
              </div>
            </div>
            <div className="bg-base-2 rounded-xl border border-base-4 p-4">
              <div className="text-xs text-ink-muted">交易日</div>
              <div className="text-xl font-bold text-ink-secondary">{majorFlow.summary?.date || '-'}</div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-base-2 rounded-xl border border-base-4 p-5">
              <h3 className="font-semibold text-ink-primary mb-4">个股主力净流入 TOP10</h3>
              <div className="space-y-2">
                {(majorFlow.top_stocks || []).map((s, i) => (
                  <div key={i} className="flex justify-between items-center py-2 border-b border-gray-50 last:border-0">
                    <div>
                      <span className="text-xs text-ink-muted w-6 inline-block">{i + 1}</span>
                      <span className="font-medium text-ink-primary">{s.name}</span>
                      <span className="text-xs text-ink-muted ml-2">{s.code}</span>
                    </div>
                    <span className={`font-medium ${(s.main_net || 0) >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                      {(s.main_net || 0).toFixed(2)} 亿
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-base-2 rounded-xl border border-base-4 p-5">
              <h3 className="font-semibold text-ink-primary mb-4">行业主力资金排行</h3>
              <div className="space-y-2">
                {(majorFlow.sectors || []).slice(0, 10).map((s, i) => (
                  <div key={i} className="flex justify-between items-center py-2 border-b border-gray-50 last:border-0">
                    <div>
                      <span className="text-xs text-ink-muted w-6 inline-block">{i + 1}</span>
                      <span className="font-medium text-ink-primary">{s.name}</span>
                    </div>
                    <span className={`font-medium ${(s.main_net || 0) >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                      {(s.main_net || 0).toFixed(2)} 亿
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 龙虎榜 */}
      {tab === 'dragon' && (
        <div className="bg-base-2 rounded-xl border border-base-4 overflow-hidden">
          <div className="px-5 py-3 border-b border-gray-50">
            <h3 className="font-semibold text-ink-primary">今日龙虎榜</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-xs text-ink-muted border-b border-gray-50">
                  <th className="text-left px-5 py-3">股票</th>
                  <th className="text-right px-5 py-3">涨跌幅</th>
                  <th className="text-left px-5 py-3">上榜原因</th>
                  <th className="text-right px-5 py-3">买入(亿)</th>
                  <th className="text-right px-5 py-3">卖出(亿)</th>
                </tr>
              </thead>
              <tbody>
                {dragonTiger.map((s, i) => (
                  <tr key={i} className="border-b border-gray-50 hover:bg-base-3">
                    <td className="px-5 py-3">
                      <span className="font-medium text-ink-primary">{s.name}</span>
                      <span className="text-xs text-ink-muted ml-2">{s.code}</span>
                    </td>
                    <td className={`px-5 py-3 text-right font-medium ${(s.change_pct || 0) >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                      {(s.change_pct || 0) >= 0 ? '+' : ''}{(s.change_pct || 0).toFixed(2)}%
                    </td>
                    <td className="px-5 py-3 text-sm text-ink-muted">{s.reason}</td>
                    <td className="px-5 py-3 text-right text-red-600">{(s.buy_amount || 0).toFixed(2)}</td>
                    <td className="px-5 py-3 text-right text-green-600">{(s.sell_amount || 0).toFixed(2)}</td>
                  </tr>
                ))}
                {dragonTiger.length === 0 && (
                  <tr><td colSpan={5} className="text-center py-8 text-ink-muted">今日暂无龙虎榜数据（非交易日或数据未更新）</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
