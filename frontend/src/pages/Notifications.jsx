import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import API_BASE from '../api'
import { Bell, BellOff, Check, ExternalLink } from 'lucide-react'

export default function Notifications() {
  const { token } = useAuth()
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchNotifications()
  }, [])

  const fetchNotifications = async () => {
    try {
      const r = await fetch('/api/notifications/history?limit=30', {
        headers: { Authorization: `Bearer ${token}` }
      })
      const data = await r.json()
      setNotifications(data.data?.notifications || [])
    } catch { }
    setLoading(false)
  }

  const markRead = async (index) => {
    try {
      await fetch(`${API_BASE}/notifications/read/${index}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      })
      setNotifications(prev =>
        prev.map((n, i) => i === index ? { ...n, read: true } : n)
      )
    } catch { }
  }

  const markAllRead = async () => {
    try {
      await fetch('/api/notifications/read-all', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      })
      setNotifications(prev => prev.map(n => ({ ...n, read: true })))
    } catch { }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-10 w-10 border-4 border-primary-500 border-t-transparent"></div>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">消息通知</h1>
          <p className="text-gray-500 text-sm mt-1">分析完成、重要动态通知</p>
        </div>
        {notifications.length > 0 && (
          <button
            onClick={markAllRead}
            className="text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            全部已读
          </button>
        )}
      </div>

      {notifications.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-2xl border border-gray-100">
          <BellOff className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">暂无通知</p>
          <p className="text-sm text-gray-400 mt-1">运行分析后将在此处显示通知</p>
        </div>
      ) : (
        <div className="space-y-3">
          {notifications.map((n, i) => (
            <div
              key={i}
              onClick={() => !n.read && markRead(i)}
              className={`p-4 rounded-xl border transition-all cursor-pointer
                ${n.read
                  ? 'bg-white border-gray-100'
                  : 'bg-primary-50 border-primary-100 hover:bg-primary-100'
                }`}
            >
              <div className="flex items-start gap-3">
                <div className={`w-2 h-2 rounded-full mt-2 shrink-0 ${n.read ? 'bg-gray-300' : 'bg-primary-500'}`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className={`font-medium ${n.read ? 'text-gray-700' : 'text-gray-900'}`}>{n.title}</h3>
                    <span className="text-xs text-gray-400 shrink-0 ml-2">
                      {n.created_at ? new Date(n.created_at).toLocaleString('zh-CN') : ''}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 whitespace-pre-wrap">{n.content}</p>
                  {n.decision && (
                    <span className={`inline-block mt-2 text-xs px-2 py-0.5 rounded-full font-medium
                      ${n.decision === 'BUY' ? 'bg-red-50 text-red-600' :
                        n.decision === 'SELL' ? 'bg-green-50 text-green-600' :
                        'bg-yellow-50 text-yellow-600'}`}
                    >
                      {n.decision === 'BUY' ? '买入' : n.decision === 'SELL' ? '卖出' : '持有'}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
