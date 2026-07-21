@echo off
chcp 65001 >nul
echo ========================================
echo   覓投AI (mitouai) — 本地开发启动
echo ========================================
echo.

cd /d %~dp0

echo [1/2] 启动后端 (FastAPI)...
start "覓投AI-后端" cmd /c "cd backend && ..\.venv\Scripts\python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload"
echo       后端: http://localhost:8001
echo       API文档: http://localhost:8001/docs
echo.

echo [2/2] 启动前端 (React + Vite)...
start "覓投AI-前端" cmd /c "cd frontend && npx vite --port 5173"
echo       前端: http://localhost:5173
echo.

echo ========================================
echo   启动完成！浏览器访问 http://localhost:5173
echo   关闭窗口不会停止服务，手动关闭两个命令行窗口即可
echo ========================================
pause
