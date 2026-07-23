import { useState, useEffect, useMemo, useCallback } from 'react'
import {
  BookMarked, Plus, Search, Tag, Pin, Trash2, Edit3, X,
  Loader2, FileText, TrendingUp, AlertCircle, Lightbulb,
  FolderOpen, Clock, Save, BookOpen, ChevronRight
} from 'lucide-react'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

const CATEGORY_ICONS = {
  general: FileText,
  stocks: TrendingUp,
  macro: BookOpen,
  strategy: Lightbulb,
  factors: BookMarked,
  risk: AlertCircle,
  lesson: BookOpen,
}

const CATEGORY_COLORS = {
  general: '#6B7280',
  stocks: '#C41E3A',
  macro: '#2563EB',
  strategy: '#C8963E',
  factors: '#7C3AED',
  risk: '#DC2626',
  lesson: '#059669',
}

const CATEGORY_LABELS = {
  general: '通用笔记',
  stocks: '个股研究',
  macro: '宏观经济',
  strategy: '策略方法',
  factors: '量化因子',
  risk: '风险管控',
  lesson: '学习心得',
}

export default function KnowledgeNotes() {
  // ── 状态 ──
  const [notes, setNotes] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeCategory, setActiveCategory] = useState('')
  const [keyword, setKeyword] = useState('')
  const [activeTag, setActiveTag] = useState('')
  const [showPinnedOnly, setShowPinnedOnly] = useState(false)

  // 编辑/创建
  const [editing, setEditing] = useState(false)
  const [editNote, setEditNote] = useState(null)
  const [formData, setFormData] = useState({
    title: '', content: '', category: 'general',
    tags: [], is_pinned: false,
  })
  const [tagInput, setTagInput] = useState('')
  const [saving, setSaving] = useState(false)

  // ── 加载笔记 ──
  const fetchNotes = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (activeCategory) params.set('category', activeCategory)
      if (keyword) params.set('keyword', keyword)
      if (showPinnedOnly) params.set('pinned', 'true')
      const r = await fetch(`${API_BASE}/notes/?${params}`)
      const data = await r.json()
      let filtered = data.notes || []
      if (activeTag) {
        filtered = filtered.filter(n => n.tags?.includes(activeTag))
      }
      setNotes(filtered)
    } catch (e) {
      console.error('Failed to fetch notes:', e)
    }
    setLoading(false)
  }, [activeCategory, keyword, activeTag, showPinnedOnly])

  const fetchStats = async () => {
    try {
      const r = await fetch(`${API_BASE}/notes/stats`)
      const data = await r.json()
      setStats(data)
    } catch (e) { console.error('Failed to fetch stats:', e) }
  }

  useEffect(() => { fetchNotes() }, [fetchNotes])
  useEffect(() => { fetchStats() }, [])

  // ── 创建/编辑 ──
  const startCreate = () => {
    setEditing(true)
    setEditNote(null)
    setFormData({
      title: '', content: '', category: 'general',
      tags: [], is_pinned: false,
    })
    setTagInput('')
  }

  const startEdit = (note) => {
    setEditing(true)
    setEditNote(note)
    setFormData({
      title: note.title,
      content: note.content,
      category: note.category,
      tags: note.tags || [],
      is_pinned: note.is_pinned,
    })
    setTagInput('')
  }

  const handleSave = async () => {
    if (!formData.title.trim()) return
    setSaving(true)
    try {
      const payload = { ...formData }
      if (editNote) {
        await fetch(`${API_BASE}/notes/${editNote.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })
      } else {
        await fetch(`${API_BASE}/notes/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })
      }
      setEditing(false)
      fetchNotes()
      fetchStats()
    } catch (e) {
      console.error('Save failed:', e)
    }
    setSaving(false)
  }

  const handleDelete = async (noteId) => {
    if (!confirm('确定删除这条笔记吗？')) return
    try {
      await fetch(`${API_BASE}/notes/${noteId}`, { method: 'DELETE' })
      fetchNotes()
      fetchStats()
    } catch (e) { console.error('Delete failed:', e) }
  }

  const togglePin = async (note) => {
    try {
      await fetch(`${API_BASE}/notes/${note.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_pinned: !note.is_pinned }),
      })
      fetchNotes()
    } catch (e) { console.error('Pin failed:', e) }
  }

  const addTag = () => {
    const t = tagInput.trim()
    if (t && !formData.tags.includes(t)) {
      setFormData({ ...formData, tags: [...formData.tags, t] })
    }
    setTagInput('')
  }

  const removeTag = (t) => {
    setFormData({ ...formData, tags: formData.tags.filter(x => x !== t) })
  }

  // ── 所有标签（从 stats） ──
  const allTags = useMemo(() => stats?.top_tags || [], [stats])

  return (
    <div className="animate-in">
      {/* ── 页头 ── */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center text-white shadow-lg"
            style={{ background: 'linear-gradient(135deg, #C8963E, #E8A817)', boxShadow: '0 4px 12px rgba(200,150,62,0.3)' }}>
            <BookMarked className="w-5 h-5" />
          </div>
          <div className="flex-1">
            <h1 className="text-2xl font-bold" style={{ color: '#1A1A2E' }}>知识笔记</h1>
            <p className="text-sm" style={{ color: '#A09080' }}>
              记录投研心得 · 积累金融知识 · 构建个人知识库
            </p>
          </div>
          <button onClick={startCreate} className="btn-primary text-sm">
            <Plus className="w-4 h-4" /> 新建笔记
          </button>
        </div>
        {/* 合规声明 */}
        <div className="flex items-start gap-2 px-4 py-2.5 rounded-lg" style={{ background: 'rgba(196,30,58,0.04)', border: '1px solid rgba(196,30,58,0.1)' }}>
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" style={{ color: '#C41E3A' }} />
          <span className="text-xs" style={{ color: '#A3152E' }}>
            笔记内容为用户个人学习记录，本平台不对其中的投资观点负责。请独立思考，理性投资。
          </span>
        </div>
      </div>

      {/* ── 统计概览 ── */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          <StatCard icon={FileText} label="笔记总数" value={stats.total} color="#C8963E" />
          <StatCard icon={Pin} label="置顶笔记" value={stats.pinned} color="#C41E3A" />
          <StatCard icon={FolderOpen} label="分类数" value={Object.keys(stats.by_category || {}).length} color="#2563EB" />
          <StatCard icon={Tag} label="标签数" value={allTags.length} color="#059669" />
        </div>
      )}

      {/* ── 搜索 + 筛选 ── */}
      <div className="card p-4 mb-4">
        <div className="flex flex-wrap items-center gap-3">
          {/* 搜索 */}
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5" style={{ color: '#A09080' }} />
            <input
              type="text"
              placeholder="搜索标题或内容..."
              value={keyword}
              onChange={e => setKeyword(e.target.value)}
              className="input-light !py-2 !pl-9 !pr-3 text-sm w-full"
            />
          </div>
          {/* 置顶筛选 */}
          <button
            onClick={() => setShowPinnedOnly(!showPinnedOnly)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all"
            style={showPinnedOnly
              ? { background: 'rgba(196,30,58,0.1)', color: '#C41E3A', border: '1px solid rgba(196,30,58,0.2)' }
              : { background: '#FFF8EE', color: '#6B5B4E', border: '1px solid #F0E6D3' }}
          >
            <Pin className="w-3.5 h-3.5" /> 置顶
          </button>
        </div>

        {/* 分类标签 */}
        <div className="flex flex-wrap gap-2 mt-3">
          <CategoryChip
            label="全部" active={!activeCategory}
            onClick={() => setActiveCategory('')}
            count={stats?.total}
          />
          {Object.entries(CATEGORY_LABELS).map(([key, label]) => (
            <CategoryChip
              key={key}
              label={label}
              active={activeCategory === key}
              onClick={() => setActiveCategory(activeCategory === key ? '' : key)}
              count={stats?.by_category?.[key] || 0}
              color={CATEGORY_COLORS[key]}
            />
          ))}
        </div>

        {/* 热门标签 */}
        {allTags.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5 mt-3 pt-3" style={{ borderTop: '1px solid #F0E6D3' }}>
            <span className="text-xs font-semibold" style={{ color: '#A09080' }}>
              <Tag className="w-3 h-3 inline mr-1" /> 热门标签:
            </span>
            {allTags.map(t => (
              <button
                key={t.name}
                onClick={() => setActiveTag(activeTag === t.name ? '' : t.name)}
                className="text-xs px-2 py-0.5 rounded-full transition-all"
                style={activeTag === t.name
                  ? { background: 'rgba(200,150,62,0.15)', color: '#C8963E', border: '1px solid rgba(200,150,62,0.3)' }
                  : { background: '#FFF8EE', color: '#8B7355', border: '1px solid #F0E6D3' }}
              >
                {t.name} ({t.count})
              </button>
            ))}
          </div>
        )}
      </div>

      {/* ── 笔记列表 ── */}
      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="w-8 h-8 animate-spin" style={{ color: '#C8963E' }} />
        </div>
      ) : notes.length === 0 ? (
        <div className="card p-12 text-center">
          <BookMarked className="w-12 h-12 mx-auto mb-3 opacity-20" style={{ color: '#C8963E' }} />
          <p className="text-sm font-medium mb-1" style={{ color: '#6B5B4E' }}>
            {keyword || activeCategory || activeTag ? '未找到匹配的笔记' : '还没有笔记'}
          </p>
          <p className="text-xs mb-4" style={{ color: '#A09080' }}>
            {keyword || activeCategory || activeTag ? '试试调整筛选条件' : '创建你的第一条知识笔记，记录投研心得'}
          </p>
          {!keyword && !activeCategory && !activeTag && (
            <button onClick={startCreate} className="btn-primary text-sm">
              <Plus className="w-4 h-4" /> 新建笔记
            </button>
          )}
        </div>
      ) : (
        <div className="grid md:grid-cols-2 gap-3">
          {notes.map(note => {
            const color = CATEGORY_COLORS[note.category] || '#C8963E'
            const Icon = CATEGORY_ICONS[note.category] || FileText
            return (
              <div
                key={note.id}
                className="card p-4 group transition-all hover:shadow-lg"
                style={note.is_pinned ? { borderColor: 'rgba(196,30,58,0.2)', background: 'rgba(196,30,58,0.01)' } : {}}
              >
                {/* 头部 */}
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0"
                      style={{ background: `${color}15` }}>
                      <Icon className="w-3.5 h-3.5" style={{ color }} />
                    </div>
                    <span className="text-xs font-medium px-2 py-0.5 rounded-full"
                      style={{ background: `${color}10`, color }}>
                      {CATEGORY_LABELS[note.category] || note.category}
                    </span>
                    {note.is_pinned && (
                      <Pin className="w-3 h-3" style={{ color: '#C41E3A', fill: '#C41E3A' }} />
                    )}
                  </div>
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onClick={() => togglePin(note)} className="p-1 rounded hover:bg-base-1 transition-colors"
                      title={note.is_pinned ? '取消置顶' : '置顶'}>
                      <Pin className="w-3.5 h-3.5" style={{ color: note.is_pinned ? '#C41E3A' : '#A09080' }} />
                    </button>
                    <button onClick={() => startEdit(note)} className="p-1 rounded hover:bg-base-1 transition-colors"
                      title="编辑">
                      <Edit3 className="w-3.5 h-3.5" style={{ color: '#A09080' }} />
                    </button>
                    <button onClick={() => handleDelete(note.id)} className="p-1 rounded hover:bg-base-1 transition-colors"
                      title="删除">
                      <Trash2 className="w-3.5 h-3.5" style={{ color: '#A09080' }} />
                    </button>
                  </div>
                </div>

                {/* 标题 */}
                <h3 className="text-sm font-bold mb-1.5 line-clamp-1" style={{ color: '#1A1A2E' }}>
                  {note.title}
                </h3>

                {/* 内容预览 */}
                <p className="text-xs leading-relaxed mb-2 line-clamp-3" style={{ color: '#6B5B4E' }}>
                  {note.content || '（无内容）'}
                </p>

                {/* 标签 */}
                {note.tags?.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-2">
                    {note.tags.map(t => (
                      <span key={t} className="text-2xs px-1.5 py-0.5 rounded"
                        style={{ background: '#FFF8EE', color: '#8B7355' }}>
                        #{t}
                      </span>
                    ))}
                  </div>
                )}

                {/* 时间 */}
                <div className="flex items-center gap-1 text-2xs" style={{ color: '#A09080' }}>
                  <Clock className="w-3 h-3" />
                  {note.updated_at}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* ── 编辑弹窗 ── */}
      {editing && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: 'rgba(26,26,46,0.4)', backdropFilter: 'blur(4px)' }}
          onClick={() => setEditing(false)}
        >
          <div
            className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[85vh] overflow-y-auto animate-scale-in"
            onClick={e => e.stopPropagation()}
            style={{ boxShadow: '0 24px 64px rgba(139,115,85,0.2)' }}
          >
            {/* 弹窗头 */}
            <div className="flex items-center justify-between p-5 sticky top-0 bg-white z-10"
              style={{ borderBottom: '1px solid #F0E6D3' }}>
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg flex items-center justify-center"
                  style={{ background: 'rgba(200,150,62,0.1)' }}>
                  <Edit3 className="w-4 h-4" style={{ color: '#C8963E' }} />
                </div>
                <h3 className="text-lg font-bold" style={{ color: '#1A1A2E' }}>
                  {editNote ? '编辑笔记' : '新建笔记'}
                </h3>
              </div>
              <button onClick={() => setEditing(false)} className="p-2 rounded-lg transition-all" style={{ color: '#A09080' }}>
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* 表单 */}
            <div className="p-5 space-y-4">
              {/* 标题 */}
              <div>
                <label className="text-xs font-semibold mb-1.5 block" style={{ color: '#6B5B4E' }}>标题</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={e => setFormData({ ...formData, title: e.target.value })}
                  placeholder="输入笔记标题..."
                  className="input-light text-sm w-full"
                  autoFocus
                />
              </div>

              {/* 分类 */}
              <div>
                <label className="text-xs font-semibold mb-1.5 block" style={{ color: '#6B5B4E' }}>分类</label>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(CATEGORY_LABELS).map(([key, label]) => (
                    <button
                      key={key}
                      onClick={() => setFormData({ ...formData, category: key })}
                      className="text-xs px-3 py-1.5 rounded-lg transition-all"
                      style={formData.category === key
                        ? { background: `${CATEGORY_COLORS[key]}15`, color: CATEGORY_COLORS[key], border: `1px solid ${CATEGORY_COLORS[key]}40` }
                        : { background: '#FFF8EE', color: '#8B7355', border: '1px solid #F0E6D3' }}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              {/* 标签 */}
              <div>
                <label className="text-xs font-semibold mb-1.5 block" style={{ color: '#6B5B4E' }}>标签</label>
                <div className="flex gap-2 mb-2">
                  <input
                    type="text"
                    value={tagInput}
                    onChange={e => setTagInput(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addTag())}
                    placeholder="输入标签后回车..."
                    className="input-light text-sm flex-1"
                  />
                  <button onClick={addTag} className="btn-secondary text-sm">
                    <Plus className="w-3.5 h-3.5" /> 添加
                  </button>
                </div>
                {formData.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {formData.tags.map(t => (
                      <span key={t} className="flex items-center gap-1 text-xs px-2 py-1 rounded-full"
                        style={{ background: 'rgba(200,150,62,0.1)', color: '#C8963E' }}>
                        #{t}
                        <button onClick={() => removeTag(t)}>
                          <X className="w-3 h-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* 内容 */}
              <div>
                <label className="text-xs font-semibold mb-1.5 block" style={{ color: '#6B5B4E' }}>内容</label>
                <textarea
                  value={formData.content}
                  onChange={e => setFormData({ ...formData, content: e.target.value })}
                  placeholder="记录你的投研心得、学习笔记、策略思考..."
                  rows={10}
                  className="input-light text-sm w-full resize-y"
                  style={{ minHeight: '200px' }}
                />
              </div>

              {/* 置顶 */}
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.is_pinned}
                  onChange={e => setFormData({ ...formData, is_pinned: e.target.checked })}
                  className="w-4 h-4 rounded"
                />
                <span className="text-sm" style={{ color: '#6B5B4E' }}>
                  <Pin className="w-3.5 h-3.5 inline mr-1" /> 置顶此笔记
                </span>
              </label>
            </div>

            {/* 底部按钮 */}
            <div className="flex items-center justify-end gap-2 p-5 sticky bottom-0 bg-white"
              style={{ borderTop: '1px solid #F0E6D3' }}>
              <button onClick={() => setEditing(false)} className="btn-ghost text-sm">取消</button>
              <button
                onClick={handleSave}
                disabled={saving || !formData.title.trim()}
                className="btn-primary text-sm"
              >
                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                {editNote ? '保存修改' : '创建笔记'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ── 统计卡片 ──
function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div className="card p-3 flex items-center gap-3">
      <div className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0"
        style={{ background: `${color}15` }}>
        <Icon className="w-4 h-4" style={{ color }} />
      </div>
      <div>
        <div className="text-xl font-bold num" style={{ color: '#1A1A2E' }}>{value}</div>
        <div className="text-2xs" style={{ color: '#A09080' }}>{label}</div>
      </div>
    </div>
  )
}

// ── 分类筛选 chip ──
function CategoryChip({ label, active, onClick, count, color }) {
  return (
    <button
      onClick={onClick}
      className="text-xs px-3 py-1.5 rounded-lg font-medium transition-all"
      style={active
        ? { background: (color || '#C8963E') + '15', color: color || '#C8963E', border: `1px solid ${(color || '#C8963E')}40` }
        : { background: '#FFF8EE', color: '#6B5B4E', border: '1px solid #F0E6D3' }}
    >
      {label} {count != null && count > 0 && `(${count})`}
    </button>
  )
}
