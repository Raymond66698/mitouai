import { useState, useEffect } from 'react'
import API_BASE from '../api'
import { GitBranch, Layers, ArrowRight, TrendingUp } from 'lucide-react'

const LAYER_COLORS = {
  '上游': 'bg-primary-50 text-primary-700 border-primary-200',
  '中游': 'bg-purple-50 text-purple-700 border-purple-200',
  '下游': 'bg-emerald-50 text-emerald-700 border-emerald-200',
  '品牌': 'bg-primary-50 text-primary-700 border-primary-200',
}

export default function IndustryChain() {
  const [chains, setChains] = useState([])
  const [selectedChain, setSelectedChain] = useState(null)
  const [chainData, setChainData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API_BASE}/chain/chains`)
      .then(r => r.json())
      .then(d => { setChains(d.chains || []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const loadChain = async (chainId) => {
    setSelectedChain(chainId)
    setChainData(null)
    const r = await fetch(`${API_BASE}/chain/chains/${chainId}`)
    const d = await r.json()
    setChainData(d)
  }

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-ink-primary mb-6">产业链图谱</h1>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 animate-pulse">
          {[1, 2, 3, 4].map(i => <div key={i} className="h-24 bg-base-3 rounded-xl" />)}
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-ink-primary mb-2">产业链图谱</h1>
      <p className="text-ink-muted mb-6">穿透产业链上下游，洞悉竞争格局</p>

      {/* 产业链卡片选择 */}
      {!selectedChain && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          {chains.map(c => (
            <button
              key={c.id}
              onClick={() => loadChain(c.id)}
              className="bg-base-2 rounded-xl border border-base-4 p-5 text-left hover:border-primary-200 hover:shadow-md transition-all group"
            >
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 bg-gradient-to-br from-primary-100 to-purple-100 rounded-lg flex items-center justify-center">
                  <GitBranch className="w-5 h-5 text-primary-600" />
                </div>
                <span className="font-semibold text-ink-primary">{c.name}</span>
              </div>
              <p className="text-sm text-ink-muted mb-3">{c.description}</p>
              <div className="flex gap-3 text-xs text-ink-muted">
                <span>{c.node_count} 个节点</span>
                <span>{c.layer_count} 层结构</span>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* 产业链详情 */}
      {selectedChain && chainData && (
        <div>
          <button
            onClick={() => { setSelectedChain(null); setChainData(null) }}
            className="text-sm text-primary-600 hover:underline mb-4 inline-block"
          >
            ← 返回全部产业链
          </button>

          <div className="bg-base-2 rounded-xl border border-base-4 p-6 mb-6">
            <h2 className="text-xl font-bold text-ink-primary mb-2">{chainData.name}</h2>
            <p className="text-ink-muted">{chainData.description}</p>
          </div>

          {/* 图谱可视化 — 分层展示 */}
          <div className="space-y-8">
            {(() => {
              // 按 layer_idx 分层
              const layers = {}
              ;(chainData.nodes || []).forEach(n => {
                const idx = n.layer_idx
                if (!layers[idx]) layers[idx] = { name: n.layer, nodes: [] }
                layers[idx].nodes.push(n)
              })
              return Object.entries(layers).sort(([a], [b]) => Number(a) - Number(b)).map(([idx, layer], i, arr) => (
                <div key={idx}>
                  {/* 层标签 */}
                  <div className="flex items-center gap-3 mb-3">
                    <div className={`px-3 py-1 rounded-full text-xs font-medium border ${LAYER_COLORS[layer.name] || 'bg-base-2 text-ink-secondary border-base-4'}`}>
                      {layer.name}
                    </div>
                    {i < arr.length - 1 && (
                      <div className="flex-1 flex items-center">
                        <ArrowRight className="w-4 h-4 text-ink-muted" />
                        <div className="flex-1 border-t border-dashed border-base-4" />
                      </div>
                    )}
                  </div>

                  {/* 该层节点 */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {layer.nodes.map(node => (
                      <div key={node.id} className="bg-base-2 rounded-xl border border-base-4 p-4 hover:shadow-sm transition-all">
                        <div className="flex items-center justify-between mb-3">
                          <span className="font-semibold text-ink-primary">{node.name}</span>
                          <span className="text-xs text-ink-muted">{node.stocks?.length || 0} 家公司</span>
                        </div>
                        <div className="space-y-1.5">
                          {(node.stocks || []).slice(0, 6).map((s, si) => (
                            <div key={si} className="flex items-center justify-between text-sm">
                              <div>
                                <span className="text-ink-secondary">{s.name}</span>
                                <span className="text-xs text-ink-muted ml-1.5">{s.code?.replace('.SH','').replace('.SZ','')}</span>
                              </div>
                              <span className="text-xs text-ink-muted bg-base-2 px-2 py-0.5 rounded">{s.role}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))
            })()}
          </div>
        </div>
      )}
    </div>
  )
}
