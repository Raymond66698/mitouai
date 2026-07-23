"""
测试 analysis_service 和 push_service 的 SQLAlchemy ORM 迁移
使用内存 SQLite 进行测试
"""
import os
import sys
import time

# 设置测试环境
os.environ["DATABASE_URL"] = "sqlite:///data/test_migration.db"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime
from database import init_db, get_db_context
from models.analysis import AnalysisTask, AnalysisReport
from services.analysis_service import AnalysisService
from services.push_service import push_service

def test_setup():
    """初始化测试数据库"""
    db_path = "data/test_migration.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    init_db()
    print("✓ 数据库初始化完成")

def test_analysis_task_crud():
    """测试分析任务 CRUD（通过 ORM 模型直接操作，不依赖 TradingAgents 管道）"""
    print("\n--- 分析任务 CRUD 测试 ---")
    now = datetime.now().isoformat()

    # 1. 创建任务
    with get_db_context() as db:
        task = AnalysisTask(
            task_id="test_task_001",
            user_id="user_001",
            ticker="600519.SS",
            trade_date="2026-07-23",
            status="pending",
            model="deepseek",
            debate_rounds=1,
            risk_rounds=1,
        )
        db.add(task)
        db.commit()
        print(f"✓ 任务创建: test_task_001")

    # 2. 查询任务（通过 AnalysisService）
    svc = AnalysisService()
    fetched = svc.get_task("test_task_001")
    assert fetched is not None
    assert fetched["task_id"] == "test_task_001"
    assert fetched["ticker"] == "600519.SS"
    assert fetched["status"] == "pending"
    assert fetched["user_id"] == "user_001"
    print(f"✓ get_task() 查询成功: {fetched['status']}")

    # 3. 更新任务状态
    with get_db_context() as db:
        t = db.query(AnalysisTask).filter(AnalysisTask.task_id == "test_task_001").first()
        t.status = "completed"
        t.completed_at = now
        t.result_summary = "HOLD"
        db.commit()

    fetched = svc.get_task("test_task_001")
    assert fetched["status"] == "completed"
    assert fetched["result_summary"] == "HOLD"
    print(f"✓ 任务状态更新: {fetched['status']}")

    # 4. 创建报告
    with get_db_context() as db:
        report = AnalysisReport(
            task_id="test_task_001",
            ticker="600519.SS",
            trade_date="2026-07-23",
            latest_price=1500.50,
            data_points=200,
            indicators_available=1,
            fundamentals_available=1,
            news_available=0,
            global_news_available=0,
            decision="HOLD",
            confidence="中等",
            summary="测试摘要",
            raw_sections={"indicators": "test", "fundamentals": "test"},
        )
        db.add(report)
        db.commit()
        print("✓ 报告创建")

    # 5. 查询报告
    report = svc.get_report("test_task_001")
    assert report is not None
    assert report["decision"] == "HOLD"
    assert report["confidence"] == "中等"
    assert report["latest_price"] == 1500.50
    assert report["data_points"] == 200
    print(f"✓ get_report() 查询成功: {report['decision']}")

    # 6. 查询用户任务历史
    with get_db_context() as db:
        # 再创建几条任务
        for i in range(3):
            task = AnalysisTask(
                task_id=f"task_user_{i}",
                user_id="user_001",
                ticker=f"00000{i}.SZ",
                status="completed",
            )
            db.add(task)
        db.commit()

    user_tasks = svc.get_user_tasks("user_001", limit=10)
    assert len(user_tasks) >= 4
    print(f"✓ 用户任务历史: {len(user_tasks)} 条")

    # 7. 查询不存在的任务/报告
    assert svc.get_task("nonexistent") is None
    assert svc.get_report("nonexistent") is None
    assert svc.get_user_tasks("no_such_user") == []
    print("✓ 不存在的任务/报告返回 None/空列表")

def test_push_service_crud():
    """测试推送通知 CRUD（DB 持久化）"""
    print("\n--- 推送通知 CRUD 测试 ---")
    user_id = "user_push_001"

    # 1. 记录通知
    nid1 = push_service._record_notification(user_id, {
        "type": "analysis_complete",
        "title": "🟢 600519.SS 分析完成",
        "content": "决策: BUY, 置信度: 高",
        "task_id": "task_abc",
        "ticker": "600519.SS",
        "decision": "BUY",
    })
    assert nid1 is not None
    print(f"✓ 通知已记录: id={nid1}")

    nid2 = push_service._record_notification(user_id, {
        "type": "system",
        "title": "系统通知",
        "content": "欢迎使用觅投AI",
    })
    assert nid2 is not None
    print(f"✓ 通知已记录: id={nid2}")

    nid3 = push_service._record_notification(user_id, {
        "type": "breaking_news",
        "title": "📰 重要新闻",
        "content": "某重要新闻内容",
    })
    print(f"✓ 通知已记录: id={nid3}")

    # 2. 获取通知列表
    notifications = push_service.get_notifications(user_id, limit=10)
    assert len(notifications) >= 3
    # 最新的在前
    assert notifications[0]["id"] == nid3
    assert notifications[2]["id"] == nid1
    print(f"✓ 通知列表: {len(notifications)} 条（按时间倒序）")

    # 3. 获取未读通知
    unread = push_service.get_notifications(user_id, limit=10, unread_only=True)
    assert len(unread) >= 3
    print(f"✓ 未读通知: {len(unread)} 条")

    # 4. 标记单条已读
    success = push_service.mark_read(user_id, nid1)
    assert success is True
    print(f"✓ 标记已读: id={nid1}")

    # 验证
    after = push_service.get_notifications(user_id, limit=10)
    n1 = [n for n in after if n["id"] == nid1][0]
    assert n1["read"] is True
    # 其他的仍然未读
    n2 = [n for n in after if n["id"] == nid2][0]
    assert n2["read"] is False
    print("✓ 已读状态确认（局部已读不影响其他）")

    # 5. 未读计数
    count = push_service.get_unread_count(user_id)
    assert count == 2  # nid2 and nid3
    print(f"✓ 未读计数: {count}")

    # 6. 全部标记已读
    push_service.mark_all_read(user_id)
    count = push_service.get_unread_count(user_id)
    assert count == 0
    print(f"✓ 全部已读后未读计数: {count}")

    # 7. 标记不存在的通知
    assert push_service.mark_read(user_id, 99999) is False
    print("✓ 不存在的通知标记返回 False")

    # 8. 空用户
    assert push_service.get_notifications("nonexistent") == []
    assert push_service.get_unread_count("nonexistent") == 0
    print("✓ 空用户处理正常")

def test_notification_trim():
    """测试通知数量裁剪（最多 50 条）"""
    print("\n--- 通知裁剪测试 ---")
    user_id = "user_trim_001"

    # 插入 60 条通知
    for i in range(60):
        push_service._record_notification(user_id, {
            "type": "system",
            "title": f"通知 {i}",
            "content": f"内容 {i}",
        })

    notifications = push_service.get_notifications(user_id, limit=100)
    assert len(notifications) == 50, f"Expected 50, got {len(notifications)}"
    print(f"✓ 通知裁剪: 60 条 → {len(notifications)} 条（保留最新 50）")

def test_report_update():
    """测试报告更新（upsert 逻辑）"""
    print("\n--- 报告更新测试 ---")

    # 先创建任务
    with get_db_context() as db:
        task = AnalysisTask(
            task_id="report_update_001",
            user_id="user_rpt",
            ticker="000001.SZ",
            status="completed",
        )
        db.add(task)
        db.commit()

    svc = AnalysisService()

    # 第一次保存报告
    svc._save_report("report_update_001", {
        "ticker": "000001.SZ",
        "trade_date": "2026-07-23",
        "latest_price": 10.0,
        "data_points": 100,
        "indicators_available": 1,
        "fundamentals_available": 0,
        "news_available": 0,
        "global_news_available": 0,
        "decision": "HOLD",
        "confidence": "低",
        "summary": "版本1",
        "raw_sections": {"indicators": "data1"},
    })

    report = svc.get_report("report_update_001")
    assert report["summary"] == "版本1"
    print("✓ 首次报告创建成功")

    # 第二次保存（更新）
    svc._save_report("report_update_001", {
        "ticker": "000001.SZ",
        "trade_date": "2026-07-23",
        "latest_price": 12.5,
        "data_points": 150,
        "indicators_available": 1,
        "fundamentals_available": 1,
        "news_available": 1,
        "global_news_available": 0,
        "decision": "BUY",
        "confidence": "高",
        "summary": "版本2-更新",
        "raw_sections": {"indicators": "data2", "news": "news_data"},
    })

    report = svc.get_report("report_update_001")
    assert report["summary"] == "版本2-更新"
    assert report["decision"] == "BUY"
    assert report["confidence"] == "高"
    assert report["latest_price"] == 12.5
    print("✓ 报告更新成功（upsert）")

def main():
    print("=" * 60)
    print("  analysis_service + push_service ORM 迁移测试")
    print("=" * 60)

    test_setup()
    test_analysis_task_crud()
    test_report_update()
    test_push_service_crud()
    test_notification_trim()

    # 清理测试数据库
    db_path = "data/test_migration.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    print("\n" + "=" * 60)
    print("  全部 4 组测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    main()
