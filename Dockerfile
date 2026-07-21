# 觅投AI 后端 Docker 镜像
FROM python:3.13-slim

WORKDIR /app

# 复制后端代码
COPY backend /app/backend

# 安装依赖
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# 工作目录切到 backend
WORKDIR /app/backend

# Railway 会自动注入 PORT 环境变量
CMD gunicorn main:app -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT
