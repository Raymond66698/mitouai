# 覓投AI (mitouai) — 部署指南

## 本地开发

双击 `start.bat` 一键启动前后端。

## 上云部署（免费）

### 第一步：注册云服务

| 服务 | 网址 | 用途 | 免费额度 |
|------|------|------|---------|
| Railway | railway.app | 后端 Python 服务器 | 每月 $5 额度 |
| Vercel | vercel.com | 前端网页托管 | 免费 |
| PushPlus | pushplus.plus | 微信推送通知 | 免费 |

每个服务用你的 Google/GitHub 账号登录即可。

### 第二步：Railway 部署后端

1. 打开 railway.app，点击 "Start a New Project"
2. 选择 "Deploy from GitHub repo"
3. 连接你的 GitHub，选择 mitouai 仓库
4. Railway 会自动检测 `railway.toml` 并部署
5. 在 Dashboard → Variables 中添加环境变量：
   - `DEEPSEEK_API_KEY` = sk-你的key
   - `JWT_SECRET` = 随机字符串（随便打一串英文）
6. 等待部署完成，你会获得一个域名：`xxx.railway.app`

### 第三步：Vercel 部署前端

1. 打开 vercel.com，点击 "New Project"
2. 导入 mitouai 仓库
3. 框架选 Vite，不用改任何设置
4. 部署完成，获得域名：`mitouai.vercel.app`

### 第四步：绑定域名 mitouai.com

1. Railway：Settings → Domains → 添加 `api.mitouai.com`
2. Vercel：Settings → Domains → 添加 `mitouai.com`
3. 在你的域名 DNS 中添加对应的 CNAME 记录

### 第五步：配置推送通知

1. 打开 pushplus.plus，微信扫码
2. 复制 Token
3. 在覓投AI网站 → 设置 → 推送通知中填入 Token
4. 分析完成后微信会收到推送

---

## 一键部署命令（高级用户）

```bash
# Railway
railway up

# Vercel
vercel --prod
```
