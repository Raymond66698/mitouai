import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { Settings, Save, Key, Bell, ExternalLink, Info } from 'lucide-react'

export default function SettingsPage() {
  const { user, token, refreshUser } = useAuth()
  const [displayName, setDisplayName] = useState(user?.display_name || '')
  const [saving, setSaving] = useState(false)
  const [pushSettings, setPushSettings] = useState({
    pushplus_token: '',
    analysis_complete: true,
    breaking_news: false,
  })
  const [keyStatus, setKeyStatus] = useState({})
  const [provider, setProvider] = useState('deepseek')
  const [apiKey, setApiKey] = useState('')

  useEffect(() => {
    fetchSettings()
  }, [])

  const fetchSettings = async () => {
    try {
      const [settingsR, keysR] = await Promise.all([
        fetch('/api/notifications/settings', { headers: { Authorization: `Bearer ${token}` } }),
        fetch('/api/users/me/keys', { headers: { Authorization: `Bearer ${token}` } }),
      ])
      const settings = await settingsR.json()
      const keys = await keysR.json()
      if (settings.data?.settings) setPushSettings(prev => ({ ...prev, ...settings.data.settings }))
      if (keys.data?.keys) setKeyStatus(keys.data.keys)
    } catch { }
  }

  const saveProfile = async () => {
    setSaving(true)
    try {
      await fetch('/api/users/me', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ display_name: displayName })
      })
      refreshUser?.()
    } catch { }
    setSaving(false)
  }

  const savePushSettings = async () => {
    try {
      await fetch('/api/notifications/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(pushSettings)
      })
      alert('推送设置已保存')
    } catch { }
  }

  const setKey = async () => {
    if (!apiKey.trim()) return
    try {
      const r = await fetch('/api/users/me/key', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ provider, api_key: apiKey })
      })
      const data = await r.json()
      if (r.ok) {
        alert(`${provider} Key 已设置`)
        setApiKey('')
        fetchSettings()
      } else {
        alert(data.detail || '设置失败')
      }
    } catch { }
  }

  const removeKey = async (p) => {
    try {
      await fetch(`/api/users/me/key/${p}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      })
      fetchSettings()
    } catch { }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">账户设置</h1>

      {/* Profile */}
      <div className="bg-white rounded-2xl border border-gray-100 p-6 mb-6">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-900 mb-4">
          <Settings className="w-5 h-5" />
          个人信息
        </h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
            <input type="email" value={user?.email || ''} disabled className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-gray-500 cursor-not-allowed" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">显示名称</label>
            <input
              type="text"
              value={displayName}
              onChange={e => setDisplayName(e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 outline-none"
            />
          </div>
          <button
            onClick={saveProfile}
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2.5 bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 transition-all"
          >
            <Save className="w-4 h-4" />
            保存
          </button>
        </div>
      </div>

      {/* Push Notifications */}
      <div className="bg-white rounded-2xl border border-gray-100 p-6 mb-6">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-900 mb-4">
          <Bell className="w-5 h-5" />
          推送通知
        </h2>
        <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 mb-4">
          <div className="flex items-start gap-2">
            <Info className="w-4 h-4 text-blue-500 mt-0.5 shrink-0" />
            <p className="text-sm text-blue-700">
              使用 PushPlus（pushplus.plus）免费微信推送服务，分析完成后即时通知到你的手机微信。
              <a href="https://pushplus.plus" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-blue-600 underline ml-1">
                前往获取 Token <ExternalLink className="w-3 h-3" />
              </a>
            </p>
          </div>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">PushPlus Token</label>
            <input
              type="text"
              value={pushSettings.pushplus_token || ''}
              onChange={e => setPushSettings(prev => ({ ...prev, pushplus_token: e.target.value }))}
              placeholder="填入 pushplus.plus 的 Token"
              className="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 outline-none"
            />
          </div>
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={pushSettings.analysis_complete}
                onChange={e => setPushSettings(prev => ({ ...prev, analysis_complete: e.target.checked }))}
                className="rounded text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm text-gray-700">分析完成通知</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={pushSettings.breaking_news}
                onChange={e => setPushSettings(prev => ({ ...prev, breaking_news: e.target.checked }))}
                className="rounded text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm text-gray-700">重大新闻推送</span>
            </label>
          </div>
          <button
            onClick={savePushSettings}
            className="flex items-center gap-2 px-4 py-2.5 bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 transition-all"
          >
            <Save className="w-4 h-4" />
            保存推送设置
          </button>
        </div>
      </div>

      {/* BYOK */}
      <div className="bg-white rounded-2xl border border-gray-100 p-6">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-900 mb-4">
          <Key className="w-5 h-5" />
          自带 API Key（大师版专属）
        </h2>
        {user?.plan !== 'max' ? (
          <p className="text-sm text-gray-500 bg-gray-50 rounded-xl p-4">
            此功能仅限大师版用户使用。升级后可设置自己的 DeepSeek/OpenAI API Key，分析费用由你自行承担。
          </p>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <select
                value={provider}
                onChange={e => setProvider(e.target.value)}
                className="px-4 py-2.5 border border-gray-200 rounded-xl text-sm"
              >
                <option value="deepseek">DeepSeek</option>
                <option value="openai">OpenAI</option>
              </select>
              <input
                type="password"
                value={apiKey}
                onChange={e => setApiKey(e.target.value)}
                placeholder={`输入 ${provider} API Key`}
                className="flex-1 px-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 outline-none"
              />
              <button
                onClick={setKey}
                className="px-4 py-2.5 bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 transition-all shrink-0"
              >
                设置
              </button>
            </div>
            {Object.entries(keyStatus).map(([k, v]) => (
              <div key={k} className="flex items-center justify-between bg-gray-50 rounded-xl px-4 py-2.5">
                <span className="text-sm text-gray-700 capitalize">{k}</span>
                <div className="flex items-center gap-3">
                  <span className={`text-xs ${v === '已设置' ? 'text-green-600' : 'text-gray-400'}`}>{v}</span>
                  {v === '已设置' && (
                    <button onClick={() => removeKey(k)} className="text-xs text-red-500 hover:text-red-600">删除</button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
