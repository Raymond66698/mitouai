import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { Search, TrendingUp, BarChart3, Shield, Zap, ArrowRight, Sparkles, Star, Users, Briefcase, Coins } from 'lucide-react'
import { useState, useEffect, useRef } from 'react'

const FEATURES = [
  {
    icon: Sparkles,
    title: '16 位 AI 分析师',
    desc: '巴菲特、索罗斯等投资大师方法论驱动的多智能体联合研判，多空辩论得出最优结论',
    color: '#C8963E',
    bg: 'rgba(200,150,62,0.08)',
  },
  {
    icon: TrendingUp,
    title: '13+ 大师策略',
    desc: '价值投资、成长猎手、趋势跟踪、均值回归等经典策略一键应用，自动匹配最佳标的',
    color: '#C41E3A',
    bg: 'rgba(196,30,58,0.08)',
  },
  {
    icon: BarChart3,
    title: '量化因子引擎',
    desc: '估值/成长/动量/质量/波动五维因子模型，全市场扫描排名，数据驱动选股决策',
    color: '#2563EB',
    bg: 'rgba(37,99,235,0.08)',
  },
  {
    icon: Shield,
    title: '全市场覆盖',
    desc: 'A股 + 港股 + 美股三市联动，产业链图谱、资金流向、龙虎榜，360° 数据视角',
    color: '#059669',
    bg: 'rgba(5,150,105,0.08)',
  },
]

const STEPS = [
  { num: '01', title: '输入标的', desc: '输入股票名称或代码，AI 自动获取行情、基本面、新闻等全维度数据' },
  { num: '02', title: '智能分析', desc: '16 位 AI 分析师多维度研判，多空辩论，量化评分，生成专业级投研报告' },
  { num: '03', title: '做出决策', desc: '综合评分 + 风险提示 + 操作建议，用数据支撑你的每一次投资决策' },
]

const STATS = [
  { value: '5,000+', label: '覆盖标的', icon: Briefcase, num: 5000 },
  { value: '16', label: 'AI 分析师', icon: Users, num: 16 },
  { value: '13+', label: '大师策略', icon: Star, num: 13 },
  { value: '5', label: '量化因子', icon: BarChart3, num: 5 },
]

const TOKEN_ITEMS = [
  { label: '基础分析', tokens: '300', desc: '一次标准 AI 分析' },
  { label: '深度研报', tokens: '2,000', desc: '多智能体联合研判' },
  { label: '全市场选股', tokens: '500', desc: '量化因子全扫描' },
]

// 生成随机金色粒子
const PARTICLES = Array.from({ length: 28 }, (_, i) => ({
  id: i,
  size: Math.random() * 3 + 1.5,
  left: Math.random() * 100,
  top: Math.random() * 85 + 5,
  delay: Math.random() * 8,
  duration: Math.random() * 8 + 10,
  opacity: Math.random() * 0.5 + 0.2,
}))

function useCountUp(end, duration = 2000, startOnView = true) {
  const [count, setCount] = useState(0)
  const [started, setStarted] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    if (!startOnView) {
      setStarted(true)
      return
    }
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !started) {
          setStarted(true)
        }
      },
      { threshold: 0.3 }
    )
    if (ref.current) observer.observe(ref.current)
    return () => observer.disconnect()
  }, [startOnView, started])

  useEffect(() => {
    if (!started) return
    let startTime = null
    let raf
    const animate = (timestamp) => {
      if (!startTime) startTime = timestamp
      const progress = Math.min((timestamp - startTime) / duration, 1)
      const easeOutQuart = 1 - Math.pow(1 - progress, 4)
      setCount(Math.floor(easeOutQuart * end))
      if (progress < 1) {
        raf = requestAnimationFrame(animate)
      }
    }
    raf = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(raf)
  }, [started, end, duration])

  return [count, ref]
}

function useReveal() {
  const ref = useRef(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true)
          observer.disconnect()
        }
      },
      { threshold: 0.12, rootMargin: '0px 0px -50px 0px' }
    )
    if (ref.current) observer.observe(ref.current)
    return () => observer.disconnect()
  }, [])

  return [ref, visible]
}

export default function Home() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => setLoaded(true), 80)
    return () => clearTimeout(timer)
  }, [])

  const handleSearch = (e) => {
    e.preventDefault()
    if (query.trim()) {
      navigate(user ? `/analysis?q=${encodeURIComponent(query.trim())}` : `/login?redirect=analysis&q=${encodeURIComponent(query.trim())}`)
    }
  }

  // Hero 加载动画延迟
  const heroDelay = (ms) => ({
    opacity: loaded ? 1 : 0,
    transform: loaded ? 'translateY(0)' : 'translateY(24px)',
    transition: `all 0.8s cubic-bezier(0.22, 1, 0.36, 1) ${ms}ms`,
  })

  const [section1Ref, section1Visible] = useReveal()
  const [section2Ref, section2Visible] = useReveal()
  const [section3Ref, section3Visible] = useReveal()

  return (
    <div style={{ background: '#FFF8EE' }}>
      {/* ── Hero ── */}
      <section className="relative overflow-hidden min-h-[92vh] flex items-center" style={{
        background: 'linear-gradient(180deg, #FFF3E0 0%, #FFF8EE 45%, #FFFBF5 100%)',
      }}>
        {/* 背景光晕 */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1100px] h-[700px] rounded-full pointer-events-none hero-glow"
          style={{
            background: 'radial-gradient(ellipse, rgba(232,168,23,0.22) 0%, rgba(196,30,58,0.08) 40%, transparent 70%)',
          }} />

        {/* 金色粒子层 */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          {PARTICLES.map((p) => (
            <div
              key={p.id}
              className="gold-particle"
              style={{
                width: `${p.size}px`,
                height: `${p.size}px`,
                left: `${p.left}%`,
                top: `${p.top}%`,
                animationDelay: `${p.delay}s`,
                animationDuration: `${p.duration}s`,
                opacity: p.opacity,
              }}
            />
          ))}
        </div>

        {/* 流动光线 */}
        <div className="absolute top-0 left-0 right-0 h-px light-beam" style={{ background: 'linear-gradient(90deg, transparent, rgba(200,150,62,0.4), transparent)' }} />

        <div className="relative max-w-7xl mx-auto px-6 pt-24 pb-20 text-center w-full">
          {/* badge */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full mb-8 text-sm font-semibold"
            style={{
              ...heroDelay(0),
              background: 'rgba(200,150,62,0.12)',
              color: '#C8963E',
              border: '1px solid rgba(200,150,62,0.2)',
              boxShadow: '0 2px 20px rgba(200,150,62,0.12)',
            }}>
            <Sparkles className="w-4 h-4 animate-pulse-soft" /> AI 驱动的智能投研平台
          </div>

          {/* 标题 */}
          <h1 className="text-4xl md:text-6xl lg:text-7xl font-extrabold mb-6 leading-tight" style={heroDelay(120)}>
            <span className="text-gradient">洞见财富</span>
            <span className="mx-3" style={{ color: '#3D2A0C' }}>·</span>
            <span style={{ color: '#3D2A0C' }}>智胜投资</span>
          </h1>

          <p className="text-lg md:text-xl max-w-2xl mx-auto mb-4" style={{ ...heroDelay(240), color: '#6B5B4E' }}>
            16位AI分析师多空辩论 · 量化因子扫描 · 大师策略一键应用
          </p>
          <p className="text-sm max-w-xl mx-auto mb-10" style={{ ...heroDelay(340), color: '#A09080' }}>
            从数据到洞察，从策略到决策。觅投AI 帮你洞见财富，让每一次投资都更有底气
          </p>

          {/* 搜索框 */}
          <form onSubmit={handleSearch} className="relative max-w-xl mx-auto mb-8" style={heroDelay(460)}>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="试试输入「宁德时代」或「新能源板块」..."
              className="w-full pl-5 pr-28 py-4 text-base rounded-2xl border-2 transition-all outline-none search-input-glow"
              style={{
                background: '#FFFFFF',
                borderColor: 'rgba(200,150,62,0.3)',
                boxShadow: '0 4px 30px rgba(200,150,62,0.1)',
                color: '#1A1A2E',
              }}
              onFocus={e => { e.target.style.borderColor = '#C8963E'; e.target.style.boxShadow = '0 4px 40px rgba(200,150,62,0.25)'; }}
              onBlur={e => { e.target.style.borderColor = 'rgba(200,150,62,0.3)'; e.target.style.boxShadow = '0 4px 30px rgba(200,150,62,0.1)'; }}
            />
            <button type="submit" className="btn-primary absolute right-2 top-1/2 -translate-y-1/2 text-sm !py-2.5">
              <Search className="w-4 h-4" /> 开始分析
            </button>
          </form>

          <div className="flex items-center justify-center gap-3" style={heroDelay(560)}>
            <Link to="/register" className="btn-primary text-sm !py-3 !px-6 group">
              免费注册 <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
            </Link>
            <Link to="/login" className="btn-outline-gold text-sm !py-3 !px-6">登录</Link>
          </div>

          {/* 数据亮点 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-3xl mx-auto mt-16">
            {STATS.map((item, i) => (
              <StatCard key={i} item={item} index={i} loaded={loaded} />
            ))}
          </div>
        </div>

        {/* 底部波浪过渡 */}
        <div className="absolute bottom-0 left-0 right-0">
          <svg viewBox="0 0 1440 80" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full">
            <path d="M0 80V40C240 80 480 0 720 0C960 0 1200 80 1440 40V80H0Z" fill="#FFFBF5" />
          </svg>
        </div>
      </section>

      {/* ── 三步工作流 ── */}
      <section ref={section1Ref} className="py-24" style={{ background: '#FFFBF5' }}>
        <div className="max-w-5xl mx-auto px-6">
          <div className={`text-center mb-16 transition-all duration-1000 ${section1Visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
            <h2 className="text-3xl md:text-4xl font-extrabold mb-4" style={{ color: '#1A1A2E' }}>
              三步开启智能投资
            </h2>
            <p className="text-base" style={{ color: '#A09080' }}>
              比传统券商快 10 倍的研究效率
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {STEPS.map((step, i) => (
              <div
                key={i}
                className={`text-center group transition-all duration-700 ${section1Visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-12'}`}
                style={{ transitionDelay: `${i * 150}ms` }}>
                <div className="w-16 h-16 mx-auto mb-5 rounded-2xl flex items-center justify-center text-xl font-extrabold text-white transition-all duration-300 group-hover:scale-110 group-hover:rotate-3 group-hover:shadow-lg"
                  style={{ background: 'linear-gradient(135deg, #C8963E, #E8A817)', boxShadow: '0 4px 20px rgba(200,150,62,0.3)' }}>
                  {step.num}
                </div>
                <h3 className="text-lg font-bold mb-2" style={{ color: '#1A1A2E' }}>{step.title}</h3>
                <p className="text-sm leading-relaxed" style={{ color: '#6B5B4E' }}>{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 特性展示 ── */}
      <section ref={section2Ref} className="py-24" style={{ background: '#FFF8EE' }}>
        <div className="max-w-6xl mx-auto px-6">
          <div className={`text-center mb-16 transition-all duration-1000 ${section2Visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
            <h2 className="text-3xl md:text-4xl font-extrabold mb-4" style={{ color: '#1A1A2E' }}>
              为什么选择觅投AI
            </h2>
            <p className="text-base" style={{ color: '#A09080' }}>
              用数据说话，让AI成为你的投资智囊团
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {FEATURES.map((feat, i) => {
              const Icon = feat.icon
              return (
                <div
                  key={i}
                  className={`card card-hover-lift p-6 group transition-all duration-700 ${section2Visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-12'}`}
                  style={{ transitionDelay: `${i * 120}ms` }}>
                  <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-4 transition-all duration-300 group-hover:scale-110 group-hover:rotate-6"
                    style={{ background: feat.bg, boxShadow: `0 4px 20px ${feat.bg}` }}>
                    <Icon className="w-6 h-6" style={{ color: feat.color }} />
                  </div>
                  <h3 className="font-bold text-base mb-2" style={{ color: '#1A1A2E' }}>{feat.title}</h3>
                  <p className="text-sm leading-relaxed" style={{ color: '#6B5B4E' }}>{feat.desc}</p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* ── Token 经济介绍 ── */}
      <section ref={section3Ref} className="py-24" style={{ background: '#FFFBF5' }}>
        <div className="max-w-4xl mx-auto px-6 text-center">
          <div className={`transition-all duration-1000 ${section3Visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full mb-6 text-sm font-semibold"
              style={{ background: 'rgba(200,150,62,0.1)', color: '#C8963E' }}>
              <Coins className="w-4 h-4" /> Token 经济
            </div>
            <h2 className="text-3xl md:text-4xl font-extrabold mb-4" style={{ color: '#1A1A2E' }}>
              用多少付多少，透明可控
            </h2>
            <p className="text-base max-w-2xl mx-auto mb-10" style={{ color: '#6B5B4E' }}>
              抛弃传统按月订阅的限制，Token 消耗制让你按实际使用付费。
              基础分析仅需 300 tokens，深度研报 2,000 tokens。灵活充值，随时使用。
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {TOKEN_ITEMS.map((item, i) => (
              <div
                key={i}
                className={`card p-5 transition-all duration-700 hover:-translate-y-2 hover:shadow-xl ${section3Visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-12'}`}
                style={{ transitionDelay: `${200 + i * 120}ms`, background: '#FFFFFF', borderColor: '#F0E6D3' }}>
                <p className="text-sm mb-1" style={{ color: '#A09080' }}>{item.label}</p>
                <p className="text-3xl font-extrabold text-gradient">{item.tokens}</p>
                <p className="text-xs" style={{ color: '#A09080' }}>tokens / 次</p>
                <p className="text-xs mt-2" style={{ color: '#6B5B4E' }}>{item.desc}</p>
              </div>
            ))}
          </div>
          <div className={`mt-10 transition-all duration-1000 delay-500 ${section3Visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
            <Link to="/register" className="btn-primary group">
              免费注册领取 5,000 tokens <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
            </Link>
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="py-24 relative overflow-hidden" style={{
        background: 'linear-gradient(135deg, #C8963E 0%, #E8A817 50%, #C8963E 100%)',
      }}>
        <div className="absolute inset-0 cta-shine pointer-events-none" />
        <div className="absolute top-0 left-1/4 w-64 h-64 rounded-full opacity-20 pointer-events-none"
          style={{ background: 'radial-gradient(circle, rgba(255,255,255,0.5) 0%, transparent 70%)', filter: 'blur(40px)' }} />
        <div className="absolute bottom-0 right-1/4 w-80 h-80 rounded-full opacity-15 pointer-events-none"
          style={{ background: 'radial-gradient(circle, rgba(255,255,255,0.4) 0%, transparent 70%)', filter: 'blur(50px)' }} />

        <div className="relative max-w-3xl mx-auto px-6 text-center">
          <h2 className="text-3xl md:text-4xl font-extrabold text-white mb-4">
            准备好洞见财富了吗？
          </h2>
          <p className="text-white/80 text-lg mb-8">
            加入觅投AI，让 16 位 AI 分析师助你做出更好的投资决策
          </p>
          <div className="flex items-center justify-center gap-4">
            <Link to="/register" className="px-8 py-3.5 rounded-xl font-bold text-base transition-all hover:-translate-y-1 hover:shadow-xl"
              style={{ background: '#FFFFFF', color: '#C8963E', boxShadow: '0 4px 20px rgba(0,0,0,0.15)' }}>
              免费注册
            </Link>
            <Link to="/login" className="px-8 py-3.5 rounded-xl font-bold text-base border-2 border-white/40 text-white transition-all hover:bg-white/10 hover:-translate-y-1">
              立即登录
            </Link>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="py-10 border-t" style={{ borderColor: '#F0E6D3', background: '#FFFBF5' }}>
        <div className="max-w-7xl mx-auto px-6 text-center">
          <div className="flex items-center justify-center gap-2 mb-3">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center text-white font-bold text-xs"
              style={{ background: 'linear-gradient(135deg, #C8963E, #E8A817)' }}>
              觅
            </div>
            <span className="font-bold" style={{ color: '#3D2A0C' }}>觅投AI</span>
          </div>
          <p className="text-xs" style={{ color: '#A09080' }}>
            &copy; 2026 觅投AI — AI 驱动的智能投研平台
          </p>
        </div>
      </footer>
    </div>
  )
}

function StatCard({ item, index, loaded }) {
  const [count, ref] = useCountUp(item.num, 2000 + index * 300)
  const Icon = item.icon
  const display = item.value.includes('+') ? `${count.toLocaleString()}+` : `${count}${item.value.includes('+') ? '+' : ''}`

  return (
    <div
      ref={ref}
      className="text-center p-4 rounded-2xl transition-all duration-500 hover:bg-white/60 hover:shadow-lg hover:-translate-y-1"
      style={{
        opacity: loaded ? 1 : 0,
        transform: loaded ? 'translateY(0)' : 'translateY(20px)',
        transition: `all 0.8s cubic-bezier(0.22, 1, 0.36, 1) ${600 + index * 120}ms`,
      }}>
      <div className="w-10 h-10 mx-auto mb-2 rounded-xl flex items-center justify-center"
        style={{ background: 'rgba(200,150,62,0.1)' }}>
        <Icon className="w-5 h-5" style={{ color: '#C8963E' }} />
      </div>
      <div className="text-2xl md:text-3xl font-extrabold text-gradient mb-1" style={{ fontFeatureSettings: 'tnum' }}>
        {display}
      </div>
      <div className="text-xs" style={{ color: '#A09080' }}>{item.label}</div>
    </div>
  )
}
