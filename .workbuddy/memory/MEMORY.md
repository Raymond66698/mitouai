# 覓投AI (mitouai) 项目记忆

## 项目定位
AI驱动的多智能体投资分析SaaS平台，集成大师方法论、量化因子、牛散技术。

## 技术栈
- 后端：FastAPI + Python 3.13 (D:\mitouai\backend\)
- 前端：React 18 + Vite 5 + Tailwind CSS 3 (D:\mitouai\frontend\)
- AI：DeepSeek API + TradingAgents 多Agent分析管道
- 数据：akshare (A股数据)
- 认证：JWT (python-jose + passlib/bcrypt)

## 商业模式（混合模式C）
- 免费版：3次/天，平台token
- 专业版：50次/天，¥39/月
- 大师版：无限次，¥99/月，支持自带Key

## 部署目标
- 后端：Railway (railway.app)
- 前端：Vercel (vercel.com)
- 推送：PushPlus (pushplus.plus)
- 域名：mitouai.com（已购买，审核中）

## 项目路径
- D:\mitouai\ — 覓投AI SaaS 平台
- D:\TradingAgents\ — TradingAgents 开源引擎（依赖）
