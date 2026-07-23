import { AlertCircle, ShieldAlert } from 'lucide-react'

/**
 * 全站合规风险提示组件
 *
 * 定位：金融知识教育平台
 * 策略：所有AI分析结果为"数据维度的量化展示"，明确标注"不构成投资建议"
 */

// ── 紧凑底部声明栏（全局，所有页面底部） ──
export function RiskBanner() {
  return (
    <div
      className="w-full py-2 px-4 text-center"
      style={{
        background: 'rgba(196, 30, 58, 0.04)',
        borderTop: '1px solid rgba(196, 30, 58, 0.08)',
      }}
    >
      <p className="text-xs" style={{ color: '#A09080' }}>
        <ShieldAlert className="w-3 h-3 inline mr-1 -mt-0.5" style={{ color: '#C41E3A' }} />
        本平台定位为金融知识教育平台，所有内容仅用于信息展示与学习交流，不构成任何投资建议。投资有风险，入市需谨慎。
      </p>
    </div>
  )
}

// ── 完整页脚（含风险声明、备案信息） ──
export function SiteFooter() {
  return (
    <footer style={{ background: '#FFFBF5', borderTop: '1px solid #F0E6D3' }}>
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* 风险提示 */}
        <div
          className="rounded-xl p-4 mb-6"
          style={{
            background: 'rgba(196, 30, 58, 0.03)',
            border: '1px solid rgba(196, 30, 58, 0.1)',
          }}
        >
          <div className="flex items-start gap-2.5">
            <AlertCircle className="w-5 h-5 mt-0.5 shrink-0" style={{ color: '#C41E3A' }} />
            <div>
              <h4 className="text-sm font-bold mb-1.5" style={{ color: '#A3152E' }}>
                风险提示与免责声明
              </h4>
              <div className="space-y-1 text-xs leading-relaxed" style={{ color: '#8B7355' }}>
                <p>
                  1. 本平台定位为<b style={{ color: '#A3152E' }}>金融知识教育平台</b>，所有AI分析、量化因子、策略回测等内容均为数据维度的量化展示，仅用于信息展示与学习交流，<b style={{ color: '#A3152E' }}>不构成任何投资建议或买卖推荐</b>。
                </p>
                <p>
                  2. 量化因子是历史数据的统计特征，不代表未来走势。AI分析结果基于公开数据与算法模型，可能存在偏差或错误，不应当作投资决策的唯一依据。
                </p>
                <p>
                  3. 投资有风险，入市需谨慎。用户应根据自身风险承受能力独立做出投资决策，本平台不对任何投资损失承担责任。
                </p>
                <p>
                  4. 本平台不提供个股买卖点位预测、走势承诺或收益保证。如需专业投资建议，请咨询持牌金融机构。
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* 底部信息 */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <div
              className="w-7 h-7 rounded-lg flex items-center justify-center text-white font-bold text-xs"
              style={{ background: 'linear-gradient(135deg, #C8963E, #E8A817)' }}
            >
              觅
            </div>
            <div>
              <span className="font-bold text-sm" style={{ color: '#3D2A0C' }}>觅投AI</span>
              <span className="text-xs ml-2" style={{ color: '#A09080' }}>金融知识教育平台</span>
            </div>
          </div>
          <div className="text-xs text-center md:text-right" style={{ color: '#A09080' }}>
            <p>&copy; 2026 觅投AI (mitouai.com) — AI 驱动的金融知识教育平台</p>
            <p className="mt-0.5">本平台不提供证券投资咨询业务，不构成投资建议</p>
          </div>
        </div>
      </div>

      {/* 紧凑风险提示栏 */}
      <RiskBanner />
    </footer>
  )
}

// ── 页内风险提示卡片（用于分析结果、选股等页面顶部） ──
export function RiskNotice({ variant = 'default' }) {
  if (variant === 'compact') {
    return (
      <div
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg"
        style={{
          background: 'rgba(196, 30, 58, 0.04)',
          border: '1px solid rgba(196, 30, 58, 0.1)',
        }}
      >
        <AlertCircle className="w-3.5 h-3.5 shrink-0" style={{ color: '#C41E3A' }} />
        <span className="text-xs" style={{ color: '#A3152E' }}>
          以下内容为数据维度的量化展示，仅用于学习交流，不构成投资建议
        </span>
      </div>
    )
  }

  return (
    <div
      className="flex items-start gap-2.5 px-4 py-3 rounded-xl mb-4"
      style={{
        background: 'rgba(196, 30, 58, 0.03)',
        border: '1px solid rgba(196, 30, 58, 0.1)',
      }}
    >
      <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" style={{ color: '#C41E3A' }} />
      <div className="text-xs leading-relaxed" style={{ color: '#8B7355' }}>
        <b style={{ color: '#A3152E' }}>风险提示：</b>
        以下内容为基于公开数据的AI量化分析展示，仅用于金融知识教育与学习交流，<b style={{ color: '#A3152E' }}>不构成投资建议</b>。
        量化因子和AI分析基于历史数据，不代表未来走势。投资有风险，入市需谨慎。
      </div>
    </div>
  )
}

export default SiteFooter
