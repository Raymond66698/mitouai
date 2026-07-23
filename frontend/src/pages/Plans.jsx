import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { Check, Zap, Crown, Star } from 'lucide-react'

export default function Plans() {
  const { user, token, refreshUser } = useAuth()
  const [plans, setPlans] = useState([])
  const [loading, setLoading] = useState(true)
  const [upgrading, setUpgrading] = useState(null)

  useEffect(() => {
    fetchPlans()
  }, [])

  const fetchPlans = async () => {
    try {
      const r = await fetch('/api/subscriptions/plans', {
        headers: { Authorization: `Bearer ${token}` }
      })
      const data = await r.json()
      setPlans(data.plans || [])
    } catch { }
    setLoading(false)
  }

  const upgrade = async (planId) => {
    setUpgrading(planId)
    try {
      const r = await fetch('/api/subscriptions/upgrade', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ plan: planId })
      })
      const data = await r.json()
      if (r.ok) {
        alert(data.message)
        refreshUser?.()
      } else {
        alert(data.detail || '升级失败')
      }
    } catch { }
    setUpgrading(null)
  }

  const planIcons = {
    free: { icon: Star, color: 'text-ink-muted', bg: 'bg-base-2', border: 'border-base-4' },
    pro: { icon: Zap, color: 'text-primary-500', bg: 'bg-primary-50', border: 'border-primary-200' },
    max: { icon: Crown, color: 'text-amber-500', bg: 'bg-primary-50', border: 'border-primary-200' },
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-10 w-10 border-4 border-primary-500 border-t-transparent"></div>
      </div>
    )
  }

  return (
    <div>
      <div className="text-center mb-10">
        <h1 className="text-2xl font-bold text-ink-primary mb-2">选择适合你的套餐</h1>
        <p className="text-ink-muted">
          当前：<span className="font-semibold text-primary-600">{user?.plan_name || '免费版'}</span>
          {' · '}剩余 {user?.remaining || 0} 次分析
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
        {plans.map(plan => {
          const isCurrent = user?.plan === plan.id
          const { icon: Icon, color, bg, border } = planIcons[plan.id] || planIcons.free
          return (
            <div
              key={plan.id}
              className={`bg-white rounded-2xl border-2 p-6 relative transition-all
                ${isCurrent ? 'border-primary-400 shadow-lg shadow-primary-100' : 'border-base-4 hover:border-base-4'}`}
            >
              {isCurrent && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 bg-primary-600 text-white text-xs font-medium rounded-full">
                  当前套餐
                </div>
              )}

              <div className="text-center mb-6">
                <div className={`w-14 h-14 ${bg} rounded-2xl flex items-center justify-center mx-auto mb-4`}>
                  <Icon className={`w-7 h-7 ${color}`} />
                </div>
                <h3 className="text-xl font-bold text-ink-primary">{plan.name}</h3>
                <div className="mt-2">
                  {plan.price > 0 ? (
                    <span className="text-3xl font-bold text-ink-primary">
                      ¥{plan.price}
                      <span className="text-sm font-normal text-ink-muted">/{plan.price_unit}</span>
                    </span>
                  ) : (
                    <span className="text-3xl font-bold text-ink-primary">免费</span>
                  )}
                </div>
              </div>

              <ul className="space-y-3 mb-6">
                <li className="flex items-center gap-2 text-sm">
                  <Check className="w-4 h-4 text-green-500 shrink-0" />
                  <span className="font-medium">每日 {plan.daily_analyses} 次分析</span>
                </li>
                {plan.features.map((f, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm text-ink-secondary">
                    <Check className="w-4 h-4 text-green-500 shrink-0" />
                    {f}
                  </li>
                ))}
              </ul>

              {isCurrent ? (
                <button
                  disabled
                  className="w-full py-2.5 bg-base-3 text-ink-muted rounded-xl font-medium cursor-not-allowed"
                >
                  当前套餐
                </button>
              ) : (
                <button
                  onClick={() => upgrade(plan.id)}
                  disabled={upgrading === plan.id}
                  className="w-full py-2.5 bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 disabled:opacity-50 transition-all"
                >
                  {upgrading === plan.id ? '处理中...' : `升级到 ${plan.name}`}
                </button>
              )}
            </div>
          )
        })}
      </div>
      <p className="text-center text-sm text-ink-muted mt-8">
        * MVP阶段套餐切换即时生效，后续将接入微信支付/支付宝
      </p>
    </div>
  )
}
