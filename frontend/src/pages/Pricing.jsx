import { useState, useEffect } from 'react'
import { Check, Zap, Crown, Sparkles } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { useNavigate } from 'react-router-dom'

const plans_data = [
  {
    id: 'free',
    name: '免费版',
    price: '0',
    icon: Zap,
    color: 'gray',
    description: '适合初次体验AI投研',
    features: [
      '每日 3 次投研分析',
      'DeepSeek 默认模型',
      '基础选股筛选',
      '策略回测（每日3次）',
      '查看策略广场',
    ],
    notIncluded: [
      'GPT-4o 高级模型',
      '五维雷达图满额度',
      '港股/美股数据',
      '产业链图谱',
      '自定义策略分享',
    ],
  },
  {
    id: 'pro',
    name: 'Pro 专业版',
    price: '39',
    icon: Sparkles,
    color: 'primary',
    popular: true,
    description: '适合进阶个人投资者',
    features: [
      '每日 50 次投研分析',
      'GPT-4o + DeepSeek 双模型',
      '无限选股筛选',
      '策略回测（每日20次）',
      '五维雷达图满额度',
      '产业链图谱（每日10次）',
      'AI研报聚合',
      '条件预警（20条）',
      '港股/美股数据',
    ],
    notIncluded: [
      'API接口',
      '策略社区分享',
      '机构级数据导出',
    ],
  },
  {
    id: 'max',
    name: 'Max 旗舰版',
    price: '99',
    icon: Crown,
    color: 'amber',
    description: '适合专业投资者和机构',
    features: [
      '无限次投研分析 ✅',
      'GPT-4o + DeepSeek + 自选模型',
      '无限选股 + 全市场扫描',
      '无限策略回测',
      '产业链图谱无限使用',
      '自定义策略分享到社区',
      'API 数据接口',
      'BYOK（自带API Key）',
      '机构级数据导出（Excel/CSV）',
      '优先客服支持',
      '港股 + 美股 + A股全覆盖',
    ],
    notIncluded: [],
  },
]

export default function Pricing() {
  const { user } = useAuth()
  const navigate = useNavigate()

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold text-ink-primary mb-3">选择适合你的方案</h1>
        <p className="text-ink-muted text-lg">解锁AI驱动的智能投研能力，让每一笔投资都有据可依</p>
      </div>

      {/* 当前方案 */}
      {user && (
        <div className="bg-gradient-to-r from-primary-500/10 to-primary-100/30 rounded-xl border border-primary-100 p-4 mb-8 text-center">
          <span className="text-sm text-primary-700">
            当前方案：<strong>{user.plan || '免费版'}</strong>
            {(user.plan || 'free') === 'free' && (
              <span className="ml-2 text-ink-muted">— 升级解锁更多功能</span>
            )}
          </span>
        </div>
      )}

      {/* 功能对比 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {plans_data.map(plan => {
          const Icon = plan.icon
          const isCurrent = user?.plan === plan.id || (!user?.plan && plan.id === 'free')
          const borderColor = plan.popular
            ? 'border-primary-300 ring-2 ring-primary-100'
            : 'border-base-4'
          const btnStyle = plan.popular
            ? 'bg-primary-600 text-white hover:bg-primary-700'
            : plan.id === 'max'
            ? 'bg-primary-500 text-white hover:bg-amber-600'
            : 'bg-base-3 text-ink-secondary hover:bg-gray-200'

          return (
            <div
              key={plan.id}
              className={`bg-white rounded-2xl border ${borderColor} p-6 relative flex flex-col`}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-primary-600 text-white text-xs font-bold px-4 py-1 rounded-full">
                  最受欢迎
                </div>
              )}

              <div className="flex items-center gap-3 mb-4">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                  plan.color === 'primary' ? 'bg-primary-100 text-primary-600' :
                  plan.color === 'amber' ? 'bg-amber-100 text-primary-600' :
                  'bg-base-3 text-ink-muted'
                }`}>
                  <Icon className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-ink-primary">{plan.name}</h3>
                  <p className="text-xs text-ink-muted">{plan.description}</p>
                </div>
              </div>

              <div className="mb-6">
                <span className="text-4xl font-bold text-ink-primary">¥{plan.price}</span>
                <span className="text-ink-muted text-sm">/月</span>
              </div>

              <div className="flex-1 space-y-3 mb-6">
                {plan.features.map((f, i) => (
                  <div key={i} className="flex items-start gap-2">
                    <Check className="w-4 h-4 text-green-500 mt-0.5 shrink-0" />
                    <span className="text-sm text-ink-secondary">{f}</span>
                  </div>
                ))}
                {plan.notIncluded.map((f, i) => (
                  <div key={`ni-${i}`} className="flex items-start gap-2 opacity-40">
                    <div className="w-4 h-4 rounded-full border border-base-4 mt-0.5 shrink-0" />
                    <span className="text-sm text-ink-muted line-through">{f}</span>
                  </div>
                ))}
              </div>

              <button
                onClick={() => {
                  if (isCurrent) return
                  if (!user) { navigate('/login'); return }
                  alert('支付功能即将上线！敬请期待。')
                }}
                className={`w-full py-2.5 rounded-xl font-medium text-sm transition-all ${
                  isCurrent ? 'bg-base-2 text-ink-muted cursor-default' : btnStyle
                }`}
              >
                {isCurrent ? '当前方案' : plan.id === 'free' ? '免费使用' : `升级到 ${plan.name}`}
              </button>
            </div>
          )
        })}
      </div>

      {/* FAQ */}
      <div className="mt-16">
        <h3 className="text-xl font-bold text-ink-primary text-center mb-8">常见问题</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
          {[
            { q: '免费版可以用多久？', a: '免费版永久可用，每日3次分析额度每日0点刷新。' },
            { q: '支持哪些支付方式？', a: '即将接入微信支付和支付宝，目前请联系客服开通Pro/Max。' },
            { q: '能否随时取消订阅？', a: '支持随时取消，取消后当前周期内仍可继续使用至到期。' },
            { q: '数据安全如何保障？', a: '所有数据存储于阿里云私有服务器，使用SSL加密传输，不会与第三方共享。' },
          ].map((faq, i) => (
            <div key={i} className="bg-base-2 rounded-xl border border-base-4 p-5">
              <h4 className="font-semibold text-ink-primary mb-2">{faq.q}</h4>
              <p className="text-sm text-ink-muted">{faq.a}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
