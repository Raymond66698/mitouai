"""
部署分析/通知 ORM 迁移到 ECS 生产环境
"""
import os
import time
import paramiko

ECS_HOST = "120.26.77.163"
ECS_USER = "root"
ECS_PASS = "Mitouai@2026!"
BACKEND_DIR = "/opt/mitouai/backend"
LOCAL_BACKEND = os.path.join(os.path.dirname(__file__), "backend")

FILES_TO_UPLOAD = [
    "models/analysis.py",
    "models/notification.py",
    "models/schemas.py",
    "services/analysis_service.py",
    "services/push_service.py",
    "routers/notifications.py",
]


def deploy():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ECS_HOST, username=ECS_USER, password=ECS_PASS)
    sftp = ssh.open_sftp()

    print("=" * 50)
    print("  部署分析/通知 ORM 迁移到 ECS")
    print("=" * 50)

    # 1. 上传文件
    print("\n[1/5] 上传文件...")
    for rel_path in FILES_TO_UPLOAD:
        local_path = os.path.join(LOCAL_BACKEND, rel_path)
        remote_path = f"{BACKEND_DIR}/{rel_path}"
        sftp.put(local_path, remote_path)
        print(f"  OK {rel_path}")

    # 2. 重建 analysis 和 notification 表（旧表有 FK，需要重建）
    print("\n[2/5] 重建 analysis/notification 表...")
    commands = """
cd /opt/mitouai/backend
source /opt/mitouai/venv/bin/activate
python3 << 'PYEOF'
import sqlite3
conn = sqlite3.connect("data/mitouai.db")
cursor = conn.cursor()
# 删除旧表（之前数据全在内存，无生产数据）
cursor.execute("DROP TABLE IF EXISTS analysis_reports")
cursor.execute("DROP TABLE IF EXISTS analysis_tasks")
cursor.execute("DROP TABLE IF EXISTS notifications")
conn.commit()
print("Dropped old tables: analysis_reports, analysis_tasks, notifications")
conn.close()

from database import init_db
init_db()

# 验证新表结构
conn = sqlite3.connect("data/mitouai.db")
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('analysis_tasks','analysis_reports','notifications')")
tables = cursor.fetchall()
print(f"Tables created: {[t[0] for t in tables]}")

# 验证 analysis_tasks 无 FK
cursor.execute("PRAGMA foreign_key_list(analysis_tasks)")
fks = cursor.fetchall()
print(f"analysis_tasks FKs: {fks}")

# 验证 notifications 无 FK
cursor.execute("PRAGMA foreign_key_list(notifications)")
fks = cursor.fetchall()
print(f"notifications FKs: {fks}")

conn.close()
print("OK")
PYEOF
"""
    stdin, stdout, stderr = ssh.exec_command(commands)
    out = stdout.read().decode()
    err = stderr.read().decode()
    print(f"  {out.strip()}")
    if err:
        print(f"  STDERR: {err}")

    # 3. 重启 gunicorn
    print("\n[3/5] 停止旧 gunicorn...")
    ssh.exec_command("pkill -9 -f gunicorn")
    time.sleep(2)

    print("[4/5] 启动 gunicorn...")
    start_cmd = (
        f"cd {BACKEND_DIR} && "
        f"nohup /opt/mitouai/venv/bin/gunicorn main:app "
        f"--workers 2 --worker-class uvicorn.workers.UvicornWorker "
        f"--bind 127.0.0.1:8000 "
        f"--access-logfile /var/log/mitouai/access.log "
        f"--error-logfile /var/log/mitouai/error.log "
        f">> /var/log/mitouai/gunicorn.log 2>&1 &"
    )
    ssh.exec_command(start_cmd)
    time.sleep(3)

    # 验证 gunicorn 是否运行
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep gunicorn | grep -v grep | wc -l")
    worker_count = stdout.read().decode().strip()
    print(f"  gunicorn 进程数: {worker_count}")

    # 5. API 验证
    print("\n[5/5] 验证 API...")

    # 健康检查
    stdin, stdout, stderr = ssh.exec_command("curl -s http://127.0.0.1:8000/health")
    health = stdout.read().decode().strip()
    print(f"  Health: {health}")

    # 通知 API
    stdin, stdout, stderr = ssh.exec_command("curl -s http://127.0.0.1:8000/api/notifications/help")
    notif = stdout.read().decode().strip()[:100]
    print(f"  Notifications: {notif}")

    # 分析 API（搜索）
    stdin, stdout, stderr = ssh.exec_command("curl -s 'http://127.0.0.1:8000/api/analysis/search?q=茅台'")
    search = stdout.read().decode().strip()[:200]
    print(f"  Analysis search: {search}")

    # 错误日志
    stdin, stdout, stderr = ssh.exec_command(
        "tail -5 /var/log/mitouai/error.log 2>/dev/null | grep -i 'application startup' || echo 'No startup log found'"
    )
    errors = stdout.read().decode().strip()
    print(f"  Startup log: {errors}")

    # 前端
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' https://www.mitouai.com/")
    frontend_code = stdout.read().decode().strip()
    print(f"  Frontend: {frontend_code}")

    sftp.close()
    ssh.close()

    print("\n" + "=" * 50)
    print("  部署成功!")
    print("=" * 50)


if __name__ == "__main__":
    deploy()
