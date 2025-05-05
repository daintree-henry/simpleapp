
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

    create_db_sql_path = Path("sqls/01_create_db.sql")
    init_schema_sql_path = Path("sqls/02_init_schema.sql")

    try:
        # Step 1: postgres DB에 접속해서 db 존재 확인 및 생성
        conn1 = psycopg2.connect(
            dbname="postgres",
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        conn1.autocommit = True
        with conn1.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            if cur.fetchone():
                logger.info(f"✅ '{db_name}' 데이터베이스 이미 존재")
            else:
                if create_db_sql_path.exists():
                    with open(create_db_sql_path, "r", encoding="utf-8") as f:
                        cur.execute(f.read())
                    logger.info(f"🆕 '{db_name}' 데이터베이스 생성 완료")
                else:
                    logger.warning(f"🚫 DB 생성 SQL 파일이 존재하지 않음: {create_db_sql_path}")
        conn1.close()

        # Step 2: 생성된 todo_db에 접속해 초기 스키마 실행
        if init_schema_sql_path.exists():
            conn2 = psycopg2.connect(
                dbname=db_name,
                user=db_user,
                password=db_password,
                host=db_host,
                port=db_port
            )
            with conn2.cursor() as cur2, open(init_schema_sql_path, "r", encoding="utf-8") as f:
                cur2.execute(f.read())
            conn2.commit()
            conn2.close()
            logger.info("📥 초기 스키마 실행 완료")
        else:
            logger.warning(f"🚫 초기 스키마 파일이 존재하지 않음: {init_schema_sql_path}")

    except Exception as e:
        logger.exception("❌ 데이터베이스 초기화 중 오류 발생")
        raise
