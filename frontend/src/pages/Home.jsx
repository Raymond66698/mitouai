import { Link } from 'react-router-dom'
import { Search, Zap, Shield, TrendingUp, Users, ArrowRight } from 'lucide-react'

export default function Home() {
  const features = [
    { icon: TrendingUp, title: '多智能体分析', desc: '16位AI分析师多空辩论，覆盖基本面、技术面、消息面，给你专业级投资决策' },
    { icon: Zap, title: '策略超市', desc: '巴菲特价值投资、林奇成长投资、T+0日内波段...13+大师策略任你选' },
    { icon: Users, title: '量化因子引擎', desc: '动量、价值、质量、低波动四大因子策略，用数据驱动你的投资' },
    { icon: Shield, title: '安全第一', desc: '支持自带API Key，你的数据你做主，平台不存储任何敏感信息' },
  ]

  return (
    <div>
      {/* Hero */}
      <section className="text-center py-16 md:py-24">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-50 text-primary-700 text-sm font-medium mb-6">
          <Zap className="w-4 h-4" />
          AI驱动的多智能体投资分析平台
        </div>
        <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6 leading-tight">
          让每一位投资者<br />
          <span className="bg-gradient-to-r from-primary-600 to-purple-600 bg-clip-text text-transparent">
            都拥有AI投资团队
          </span>
        </h1>
        <p className="text-lg text-gray-500 max-w-2xl mx-auto mb-10 leading-relaxed">
          融汇全球经典投资理念与前沿量化技术，16位AI分析师多空博弈，
          让每一次决策都有理有据，告别凭感觉买卖。
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            to="/register"
            className="px-8 py-3.5 bg-primary-600 text-white rounded-xl font-semibold text-lg hover:bg-primary-700 transition-all shadow-lg shadow-primary-200 flex items-center gap-2"
          >
            免费开始使用 <ArrowRight className="w-5 h-5" />
          </Link>
          <Link
            to="/login"
            className="px-8 py-3.5 border-2 border-gray-200 text-gray-700 rounded-xl font-semibold text-lg hover:border-gray-300 hover:bg-gray-50 transition-all"
          >
            已有账号，登录
          </Link>
        </div>
      </section>

      {/* Features Grid */}
      <section className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-20">
        {features.map((f, i) => {
          const Icon = f.icon
          return (
            <div key={i} className="bg-white rounded-2xl p-6 border border-gray-100 hover:border-primary-100 hover:shadow-md transition-all">
              <div className="w-12 h-12 bg-primary-50 rounded-xl flex items-center justify-center mb-4">
                <Icon className="w-6 h-6 text-primary-600" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">{f.title}</h3>
              <p className="text-sm text-gray-500 leading-relaxed">{f.desc}</p>
            </div>
          )
        })}
      </section>

      {/* CTA */}
      <section className="bg-gradient-to-r from-primary-600 to-purple-600 rounded-3xl p-10 md:p-16 text-center text-white mb-10">
        <h2 className="text-3xl md:text-4xl font-bold mb-4">现在开始你的AI投资之旅</h2>
        <p className="text-primary-100 text-lg mb-8 max-w-xl mx-auto">
          注册即享每日3次免费分析，覆盖A股全市场5000+标的
        </p>
        <Link
          to="/register"
          className="inline-flex items-center gap-2 px-8 py-3.5 bg-white text-primary-600 rounded-xl font-semibold text-lg hover:bg-gray-50 transition-all"
        >
          立即注册，免费使用 <ArrowRight className="w-5 h-5" />
        </Link>
      </section>

      {/* Footer */}
      <footer className="text-center text-sm text-gray-400 pb-8">
        &copy; 2026 觅投AI (mitouai.com) — AI驱动的多智能体投资分析平台
      </footer>
    </div>
  )
}
