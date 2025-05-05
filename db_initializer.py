
import os
import psycopg2
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def ensure_database_and_initialize():
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "todo_db")
    init_sql_path = Path("sqls/01_init.sql")

    try:
        # Step 1: connect to postgres DB
        conn = psycopg2.connect(
            dbname="postgres",
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        conn.autocommit = True
        cur = conn.cursor()

        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        if cur.fetchone():
            logger.info(f"✅ '{db_name}' 데이터베이스 이미 존재")
        else:
            cur.execute(f"CREATE DATABASE {db_name}")
            logger.info(f"🆕 '{db_name}' 데이터베이스 생성 완료")

        cur.close()
        conn.close()

        # Step 2: 초기 SQL 실행 (있다면)
        if init_sql_path.exists():
            conn2 = psycopg2.connect(
                dbname=db_name,
                user=db_user,
                password=db_password,
                host=db_host,
                port=db_port
            )
            with conn2.cursor() as cur2, open(init_sql_path, "r", encoding="utf-8") as f:
                cur2.execute(f.read())
            conn2.commit()
            conn2.close()
            logger.info("📥 초기 SQL 실행 완료")
        else:
            logger.warning("🚫 초기 SQL 파일이 존재하지 않습니다: sqls/01_init.sql")

    except Exception as e:
        logger.exception("❌ 데이터베이스 초기화 중 오류 발생")
        raise