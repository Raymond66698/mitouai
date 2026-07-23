import { useState, useEffect } from 'react'
import API_BASE from '../api'
import { Heart, MessageCircle, TrendingUp, Share2, Copy, ArrowUpRight } from 'lucide-react'

export default function Community() {
  const [strategies, setStrategies] = useState([])
  const [sort, setSort] = useState('likes')
  const [loading, setLoading] = useState(true)
  const [detail, setDetail] = useState(null)
  const [comment, setComment] = useState('')

  useEffect(() => {
    fetchStrategies()
  }, [sort])

  const fetchStrategies = async () => {
    setLoading(true)
    try {
      const r = await fetch(`${API_BASE}/community/strategies?sort=${sort}&limit=30`)
      const d = await r.json()
      setStrategies(d.items || [])
    } catch {}
    setLoading(false)
  }

  const fetchDetail = async (id) => {
    try {
      const r = await fetch(`${API_BASE}/community/strategies/${id}`)
      const d = await r.json()
      setDetail(d)
    } catch {}
  }

  const toggleLike = async (id) => {
    await fetch(`${API_BASE}/community/strategies/${id}/like`, { method: 'POST' })
    fetchStrategies()
  }

  const addComment = async () => {
    if (!comment.trim() || !detail) return
    await fetch(`${API_BASE}/community/strategies/${detail.id}/comments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: comment }),
    })
    setComment('')
    fetchDetail(detail.id)
  }

  const copyConditions = (conditions) => {
    const text = JSON.stringify(conditions, null, 2)
    navigator.clipboard?.writeText(text)
  }

  const sortOptions = [
    { key: 'likes', label: '最多点赞' },
    { key: 'newest', label: '最新发布' },
    { key: 'usage', label: '最多使用' },
  ]

  if (detail) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <button onClick={() => setDetail(null)} className="text-sm text-primary-600 hover:underline mb-4 inline-block">
          ← 返回策略广场
        </button>

        <div className="bg-base-2 rounded-xl border border-base-4 p-6 mb-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="text-xl font-bold text-ink-primary mb-1">{detail.name}</h2>
              <p className="text-ink-muted">{detail.description}</p>
            </div>
            <div className="flex items-center gap-3">
              <button onClick={() => toggleLike(detail.id)} className="flex items-center gap-1 px-3 py-2 rounded-lg hover:bg-red-50 transition-colors">
                <Heart className={`w-5 h-5 ${detail.likes > 0 ? 'fill-red-500 text-red-500' : 'text-ink-muted'}`} />
                <span className="text-sm text-ink-secondary">{detail.likes || 0}</span>
              </button>
              <button onClick={() => copyConditions(detail.conditions)} className="flex items-center gap-1 px-3 py-2 rounded-lg hover:bg-primary-50 transition-colors text-sm text-ink-muted">
                <Copy className="w-4 h-4" /> 复制条件
              </button>
            </div>
          </div>

          {/* 回测结果 */}
          {detail.backtest_result && Object.keys(detail.backtest_result).length > 0 && (
            <div className="grid grid-cols-4 gap-3 mb-6 bg-base-2 rounded-lg p-4">
              {[
                { label: '年化收益', value: detail.backtest_result.annual_return, fmt: v => `${v?.toFixed?.(1) || '-'}%`, color: 'text-red-600' },
                { label: '最大回撤', value: detail.backtest_result.max_drawdown, fmt: v => `${v?.toFixed?.(1) || '-'}%`, color: 'text-green-600' },
                { label: '夏普比率', value: detail.backtest_result.sharpe_ratio, fmt: v => v?.toFixed?.(2) || '-', color: 'text-ink-secondary' },
                { label: '胜率', value: detail.backtest_result.win_rate, fmt: v => `${v?.toFixed?.(1) || '-'}%`, color: 'text-ink-secondary' },
              ].map(item => (
                <div key={item.label} className="text-center">
                  <div className="text-xs text-ink-muted mb-1">{item.label}</div>
                  <div className={`text-lg font-bold ${item.color}`}>{item.fmt(item.value)}</div>
                </div>
              ))}
            </div>
          )}

          {/* 筛选条件 */}
          {detail.conditions && Object.keys(detail.conditions).length > 0 && (
            <div className="mb-6">
              <h4 className="text-sm font-medium text-ink-secondary mb-2">筛选条件</h4>
              <div className="flex flex-wrap gap-2">
                {Object.entries(detail.conditions).map(([k, v]) => (
                  <span key={k} className="px-3 py-1 bg-primary-50 text-primary-700 rounded-full text-xs">
                    {k}: {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 评论 */}
        <div className="bg-base-2 rounded-xl border border-base-4 p-6">
          <h3 className="font-semibold text-ink-primary mb-4">讨论 ({detail.comments?.length || 0})</h3>
          <div className="flex gap-3 mb-6">
            <input
              value={comment}
              onChange={e => setComment(e.target.value)}
              placeholder="写下你的想法..."
              className="flex-1 px-4 py-2 border border-base-4 rounded-lg text-sm focus:outline-none focus:border-primary-300"
              onKeyDown={e => e.key === 'Enter' && addComment()}
            />
            <button onClick={addComment} className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700">
              发送
            </button>
          </div>
          <div className="space-y-3">
            {(detail.comments || []).map((c, i) => (
              <div key={i} className="flex gap-3 py-2 border-b border-gray-50 last:border-0">
                <div className="w-8 h-8 bg-base-3 rounded-full flex items-center justify-center text-xs font-bold text-ink-muted shrink-0">
                  {(c.user_name || '用')[0]}
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-sm font-medium text-ink-secondary">{c.user_name}</span>
                    <span className="text-xs text-ink-muted">{c.created_at?.slice(0, 10)}</span>
                  </div>
                  <p className="text-sm text-ink-secondary">{c.content}</p>
                </div>
              </div>
            ))}
            {(detail.comments || []).length === 0 && (
              <p className="text-center text-ink-muted py-6">暂无评论，快来发表第一条</p>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-ink-primary mb-1">策略广场</h1>
          <p className="text-ink-muted">发现和分享优质投资策略，向高手学习</p>
        </div>
        <div className="flex gap-1 bg-base-3 rounded-lg p-1">
          {sortOptions.map(o => (
            <button
              key={o.key}
              onClick={() => setSort(o.key)}
              className={`px-3 py-1.5 rounded-md text-sm transition-all ${
                sort === o.key ? 'bg-base-2 text-primary-600 shadow-card' : 'text-ink-muted hover:text-ink-secondary'
              }`}
            >
              {o.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map(i => <div key={i} className="h-40 bg-base-3 rounded-xl animate-pulse" />)}
        </div>
      ) : strategies.length === 0 ? (
        <div className="text-center py-20">
          <Share2 className="w-12 h-12 text-ink-muted mx-auto mb-4" />
          <p className="text-ink-muted mb-2">还没有人分享策略</p>
          <p className="text-ink-muted text-sm">成为第一个分享大师策略的开拓者吧！</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {strategies.map(s => (
            <div
              key={s.id}
              onClick={() => fetchDetail(s.id)}
              className="bg-base-2 rounded-xl border border-base-4 p-5 hover:border-primary-200 hover:shadow-md transition-all cursor-pointer group"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h3 className="font-semibold text-ink-primary group-hover:text-primary-600 transition-colors">{s.name}</h3>
                  <p className="text-sm text-ink-muted mt-1 line-clamp-2">{s.description || '暂无描述'}</p>
                </div>
              </div>

              {/* 条件标签 */}
              {s.conditions && Object.keys(s.conditions).length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-3">
                  {Object.entries(s.conditions).slice(0, 4).map(([k, v]) => (
                    <span key={k} className="px-2 py-0.5 bg-base-2 text-ink-muted rounded text-xs">
                      {k}: {typeof v === 'object' ? '...' : String(v)}
                    </span>
                  ))}
                  {Object.keys(s.conditions).length > 4 && (
                    <span className="text-xs text-ink-muted">+{Object.keys(s.conditions).length - 4}</span>
                  )}
                </div>
              )}

              <div className="flex items-center gap-4 text-xs text-ink-muted">
                <button onClick={(e) => { e.stopPropagation(); toggleLike(s.id) }} className="flex items-center gap-1 hover:text-red-500 transition-colors">
                  <Heart className={`w-3.5 h-3.5 ${s.likes > 0 ? 'fill-red-400 text-red-400' : ''}`} />
                  {s.likes || 0}
                </button>
                <span className="flex items-center gap-1">
                  <TrendingUp className="w-3.5 h-3.5" />
                  {s.usage_count || 0} 次使用
                </span>
                <span className="ml-auto">{s.created_at?.slice(0, 10)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
