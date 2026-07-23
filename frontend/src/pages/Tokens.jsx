import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

const ACTION_LABELS = {
  analysis_basic: '基础分析',
  analysis_deep: '深度分析',
  analysis_report: '深度研报',
  screener_scan: '选股扫描',
  backtest: '策略回测',
  daily_brief: '每日播报',
  research_summary: '研报聚合',
};

const PACKAGE_COLORS = {
  gold: {
    card: 'border-primary-300 bg-gradient-to-br from-primary-50 to-white',
    badge: 'bg-primary-100 text-primary-700',
    btn: 'btn-primary',
  },
  red: {
    card: 'border-accent-300 bg-gradient-to-br from-accent-50 to-white',
    badge: 'bg-accent-100 text-accent-600',
    btn: 'btn-red',
  },
};

export default function Tokens() {
  const navigate = useNavigate();
  const [balance, setBalance] = useState(null);
  const [packages, setPackages] = useState([]);
  const [history, setHistory] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [purchasing, setPurchasing] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    loadAll();
  }, []);

  const loadAll = async () => {
    try {
      setLoading(true);
      const [balRes, pkgRes, histRes, statsRes] = await Promise.all([
        api.get('/tokens/balance'),
        api.get('/tokens/packages'),
        api.get('/tokens/history?limit=20'),
        api.get('/tokens/stats'),
      ]);
      setBalance(balRes.data);
      setPackages(pkgRes.data.packages);
      setHistory(histRes.data.history);
      setStats(statsRes.data);
    } catch (err) {
      if (err.response?.status === 401) {
        navigate('/login');
        return;
      }
      setError('加载失败，请刷新重试');
    } finally {
      setLoading(false);
    }
  };

  const handlePurchase = async (packageId) => {
    try {
      setPurchasing(packageId);
      setError('');
      setSuccess('');
      const res = await api.post('/tokens/purchase', { package_id: packageId });
      setBalance(res.data);
      setSuccess(`领取成功！获得 ${res.data.total_purchased > 0 ? 'tokens' : ''}`);
      // 重新加载
      const [pkgRes, histRes] = await Promise.all([
        api.get('/tokens/packages'),
        api.get('/tokens/history?limit=20'),
      ]);
      setPackages(pkgRes.data.packages);
      setHistory(histRes.data.history);
    } catch (err) {
      setError(err.response?.data?.detail || '购买失败，请重试');
    } finally {
      setPurchasing(null);
    }
  };

  const formatTokens = (n) => {
    if (n >= 10000) return (n / 10000).toFixed(1) + '万';
    return n.toLocaleString();
  };

  const formatDate = (s) => {
    if (!s) return '';
    return s.slice(0, 16).replace('T', ' ');
  };

  if (loading) {
    return (
      <div className="min-h-screen pt-20 pb-12" style={{ background: '#FFF8EE' }}>
        <div className="max-w-5xl mx-auto px-6">
          <div className="space-y-6">
            <div className="skeleton h-12 w-48 rounded-xl" />
            <div className="skeleton h-40 rounded-2xl" />
            <div className="skeleton h-64 rounded-2xl" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-20 pb-16" style={{ background: '#FFF8EE' }}>
      <div className="max-w-5xl mx-auto px-6 space-y-8 animate-in">
        {/* ── Header ── */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-ink-primary">
              <span className="text-gradient">💎 Token 中心</span>
            </h1>
            <p className="text-ink-muted text-sm mt-1">管理你的 Token 余额，购买套餐，查看使用记录</p>
          </div>
        </div>

        {/* ── 消息提示 ── */}
        {error && (
          <div className="bg-accent-50 border border-accent-200 text-accent-600 px-5 py-3 rounded-xl text-sm flex items-center gap-2">
            <span>⚠️</span> {error}
            <button onClick={() => setError('')} className="ml-auto text-accent-400 hover:text-accent-600">✕</button>
          </div>
        )}
        {success && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-5 py-3 rounded-xl text-sm flex items-center gap-2">
            <span>🎉</span> {success}
            <button onClick={() => setSuccess('')} className="ml-auto text-green-400 hover:text-green-600">✕</button>
          </div>
        )}

        {/* ── 余额卡片 ── */}
        <div className="relative overflow-hidden rounded-2xl" style={{
          background: 'linear-gradient(135deg, #FFF8EE 0%, #FFF3E0 40%, #FEF0D0 100%)',
          border: '1px solid rgba(200, 150, 62, 0.2)',
        }}>
          {/* 装饰粒子 */}
          <div className="gold-particle" style={{ left: '15%', top: '60%', animationDelay: '0s' }} />
          <div className="gold-particle" style={{ left: '35%', top: '30%', animationDelay: '1s' }} />
          <div className="gold-particle" style={{ left: '75%', top: '50%', animationDelay: '2s' }} />
          <div className="gold-particle" style={{ left: '88%', top: '25%', animationDelay: '0.5s' }} />

          <div className="relative p-8">
            <div className="flex items-start justify-between flex-wrap gap-6">
              <div>
                <p className="text-ink-muted text-sm mb-2">可用余额</p>
                <div className="flex items-baseline gap-2">
                  <span className="text-5xl font-bold text-gradient" style={{ fontFeatureSettings: 'tnum' }}>
                    {balance ? formatTokens(balance.balance) : '0'}
                  </span>
                  <span className="text-ink-muted text-lg">tokens</span>
                </div>
                <p className="text-ink-muted text-xs mt-2">
                  累计获得 {balance ? formatTokens(balance.total_purchased) : '0'} tokens
                  · 已消耗 {balance ? formatTokens(balance.total_consumed) : '0'} tokens
                </p>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => document.getElementById('packages-section')?.scrollIntoView({ behavior: 'smooth' })}
                  className="btn-primary text-sm"
                >
                  💰 购买 Token
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* ── 使用统计 ── */}
        {stats && stats.by_action && Object.keys(stats.by_action).length > 0 && (
          <div className="card p-6">
            <h2 className="text-lg font-bold text-ink-primary mb-4">📊 使用概览</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="text-center p-4 rounded-xl" style={{ background: '#FFF8EE' }}>
                <p className="text-3xl font-bold text-gradient">{formatTokens(stats.total_consumed)}</p>
                <p className="text-ink-muted text-xs mt-1">累计消耗</p>
              </div>
              <div className="text-center p-4 rounded-xl" style={{ background: '#FFF8EE' }}>
                <p className="text-3xl font-bold" style={{ color: '#C8963E' }}>{history.length}</p>
                <p className="text-ink-muted text-xs mt-1">操作次数</p>
              </div>
              <div className="text-center p-4 rounded-xl" style={{ background: '#FFF8EE' }}>
                <p className="text-3xl font-bold" style={{ color: '#059669' }}>
                  {balance ? formatTokens(balance.balance) : '0'}
                </p>
                <p className="text-ink-muted text-xs mt-1">当前余额</p>
              </div>
              <div className="text-center p-4 rounded-xl" style={{ background: '#FFF8EE' }}>
                <p className="text-3xl font-bold" style={{ color: '#C41E3A' }}>
                  {history.filter(h => h.created_at?.slice(0, 10) === new Date().toISOString().slice(0, 10)).length}
                </p>
                <p className="text-ink-muted text-xs mt-1">今日操作</p>
              </div>
            </div>

            {/* 按类型分布 */}
            <div className="space-y-3">
              <p className="text-sm font-semibold text-ink-secondary">消耗分布</p>
              {Object.entries(stats.by_action)
                .sort(([, a], [, b]) => b - a)
                .map(([action, tokens]) => {
                  const pct = stats.total_consumed > 0 ? Math.round((tokens / stats.total_consumed) * 100) : 0;
                  return (
                    <div key={action} className="flex items-center gap-3">
                      <span className="text-xs text-ink-muted w-20 shrink-0">
                        {ACTION_LABELS[action] || action}
                      </span>
                      <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: '#F0E6D3' }}>
                        <div className="h-full rounded-full transition-all duration-500"
                          style={{
                            width: `${pct}%`,
                            background: 'linear-gradient(90deg, #C8963E, #E8A817)',
                          }}
                        />
                      </div>
                      <span className="text-xs text-ink-muted w-16 text-right">{formatTokens(tokens)}</span>
                      <span className="text-xs font-semibold w-8 text-right" style={{ color: '#C8963E' }}>{pct}%</span>
                    </div>
                  );
                })}
            </div>
          </div>
        )}

        {/* ── Token 套餐 ── */}
        <div id="packages-section" className="card p-6">
          <h2 className="text-lg font-bold text-ink-primary mb-1">🛒 Token 套餐</h2>
          <p className="text-ink-muted text-sm mb-6">选择合适的套餐，解锁更多 AI 分析能力</p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {packages.map((pkg) => {
              const colors = PACKAGE_COLORS[pkg.color] || PACKAGE_COLORS.gold;
              return (
                <div
                  key={pkg.id}
                  className={`relative rounded-2xl border-2 p-5 transition-all duration-200 ${
                    pkg.disabled
                      ? 'opacity-50 cursor-not-allowed border-base-4'
                      : colors.card + ' hover:shadow-card-gold cursor-pointer hover:-translate-y-1'
                  }`}
                >
                  {pkg.tag && (
                    <span className={`absolute -top-2.5 right-4 text-xs font-bold px-3 py-0.5 rounded-full ${colors.badge}`}>
                      {pkg.tag}
                    </span>
                  )}
                  <h3 className={`font-bold text-base mb-2 ${pkg.disabled ? 'text-ink-muted' : 'text-ink-primary'}`}>
                    {pkg.name}
                  </h3>
                  <div className="mb-2">
                    <span className="text-3xl font-extrabold text-gradient">{formatTokens(pkg.tokens)}</span>
                    <span className="text-ink-muted text-sm ml-1">tokens</span>
                  </div>
                  <div className="mb-4">
                    {pkg.price === 0 ? (
                      <span className="text-2xl font-bold text-accent-500">免费</span>
                    ) : (
                      <div className="flex items-baseline gap-1">
                        <span className="text-xs text-ink-muted">¥</span>
                        <span className="text-2xl font-bold text-ink-primary">{pkg.price}</span>
                        {pkg.original_price && pkg.original_price > pkg.price && (
                          <span className="text-xs text-ink-muted line-through">¥{pkg.original_price}</span>
                        )}
                      </div>
                    )}
                  </div>
                  <p className="text-xs text-ink-muted mb-4">{pkg.description}</p>
                  <button
                    disabled={pkg.disabled || purchasing === pkg.id}
                    onClick={() => !pkg.disabled && handlePurchase(pkg.id)}
                    className={`w-full text-sm py-2.5 rounded-xl font-semibold transition-all ${
                      pkg.disabled
                        ? 'bg-base-4 text-ink-muted cursor-not-allowed'
                        : colors.btn
                    }`}
                  >
                    {purchasing === pkg.id ? '处理中...' : pkg.disabled ? '已领取' : pkg.price === 0 ? '🎁 免费领取' : `¥${pkg.price} 购买`}
                  </button>
                </div>
              );
            })}
          </div>
        </div>

        {/* ── 使用记录 ── */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-ink-primary">📋 使用记录</h2>
            <span className="text-xs text-ink-muted">最近 20 条</span>
          </div>
          {history.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-4xl mb-3">📭</p>
              <p className="text-ink-muted">暂无使用记录</p>
              <p className="text-ink-muted text-xs mt-1">开始使用觅投AI分析股票吧</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-ink-muted text-xs border-b border-base-4">
                    <th className="pb-3 font-medium">时间</th>
                    <th className="pb-3 font-medium">类型</th>
                    <th className="pb-3 font-medium">详情</th>
                    <th className="pb-3 font-medium text-right">Token 变动</th>
                    <th className="pb-3 font-medium text-right">余额</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((tx) => (
                    <tr key={tx.id} className="border-b border-base-4/50 hover:bg-base-1/50 transition-colors">
                      <td className="py-3 text-ink-muted text-xs">{formatDate(tx.created_at)}</td>
                      <td className="py-3">
                        <span className={`badge ${tx.type === 'purchase' ? 'badge-gold' : 'badge-up'}`}>
                          {tx.type === 'purchase' ? '获取' : '消耗'}
                        </span>
                      </td>
                      <td className="py-3 text-ink-primary text-xs max-w-48 truncate">
                        {tx.type === 'purchase'
                          ? tx.package_name || '套餐购买'
                          : ACTION_LABELS[tx.action] || tx.action || '其他'}
                      </td>
                      <td className="py-3 text-right">
                        <span className={`font-semibold num ${tx.tokens > 0 ? 'text-up-DEFAULT' : 'text-up-DEFAULT'}`}>
                          {tx.tokens > 0 ? '+' : ''}{formatTokens(Math.abs(tx.tokens))}
                        </span>
                      </td>
                      <td className="py-3 text-right">
                        <span className="num" style={{ color: '#C8963E' }}>
                          {formatTokens(tx.balance_after)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
