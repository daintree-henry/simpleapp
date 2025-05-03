-- 기존 데이터베이스 삭제 (있는 경우)
DROP DATABASE IF EXISTS todo_db;

-- 데이터베이스 생성
CREATE DATABASE todo_db;

-- 데이터베이스 연결
\c todo_db;

-- 할 일 테이블 생성
CREATE TABLE todos (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX idx_todos_created_at ON todos(created_at DESC);
CREATE INDEX idx_todos_completed ON todos(completed);

-- updated_at 자동 업데이트를 위한 트리거 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 트리거 생성
CREATE TRIGGER update_todos_updated_at
    BEFORE UPDATE ON todos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 테스트 데이터 삽입
INSERT INTO todos (title, completed) VALUES
    ('Flask 애플리케이션 개발하기', false),
    ('PostgreSQL 설정하기', true),
    ('Redis 캐시 구현하기', false); 