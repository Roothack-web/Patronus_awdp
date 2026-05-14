from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Ensure all tables exist for current models (creates tables if missing).
    try:
        db.create_all()
        print('已执行 create_all()，数据库表已创建或已存在（含 score 字段）。')
    except Exception as e:
        print('create_all 失败：', e)
