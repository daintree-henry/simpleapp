# Todo 애플리케이션

PostgreSQL을 사용하는 간단한 할 일 관리 애플리케이션입니다.

## 기능

- 할 일 추가
- 할 일 완료/미완료 상태 변경
- PostgreSQL을 이용한 영구 저장

## 아키텍처

### 시스템 구성도

```
[Client] <-> [Flask Application] <-> [PostgreSQL DB]
```

### 컴포넌트 설명

1. **Client (Frontend)**

   - HTML, JavaScript, Bootstrap으로 구현된 웹 인터페이스
   - RESTful API를 통한 백엔드 통신
   - 실시간 데이터 업데이트

2. **Flask Application (Backend)**

   - RESTful API 엔드포인트 제공
   - 비즈니스 로직 처리
   - 데이터베이스 연동 관리

3. **PostgreSQL DB**
   - 영구 데이터 저장
   - 관계형 데이터베이스
   - 데이터 정합성 보장

### 데이터베이스 스키마

```sql
CREATE TABLE todos (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### 인덱스

- `idx_todos_created_at`: 생성일 기준 내림차순 정렬을 위한 인덱스
- `idx_todos_completed`: 완료 상태 조회를 위한 인덱스

#### 자동 업데이트

- `updated_at` 컬럼은 레코드 수정 시 자동으로 현재 시간으로 업데이트

### 데이터 흐름

1. **할 일 목록 조회 (GET /todos)**

   ```
   Client -> Flask -> Client
   Client -> Flask -> PostgreSQL -> Client (없으면)
   ```

2. **할 일 추가 (POST /todos)**

   ```
   Client -> Flask -> PostgreSQL -> Client
   ```

3. **할 일 상태 변경 (PUT /todos/<id>)**
   ```
   Client -> Flask -> PostgreSQL -> Client
   ```

## 설치 방법

1. PostgreSQL 설치 및 데이터베이스 초기화:

```bash
# PostgreSQL 접속
psql -U postgres

# sqls/01_init.sql 실행
\i sqls/01_init.sql
```

2. Python 패키지 설치:

```bash
pip install -r requirements.txt
```

3. 환경 변수 설정:
   프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 다음 내용을 설정합니다:

```env
# PostgreSQL 설정
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=todo_db

# Flask 설정
FLASK_ENV=development
FLASK_DEBUG=1
```

5. 애플리케이션 실행:

```bash
python app.py
```

## 기술 스택

- Backend: Flask
- Database: PostgreSQL
- Frontend: HTML, JavaScript, Bootstrap

## API 엔드포인트

- GET /todos: 할 일 목록 조회
- POST /todos: 새로운 할 일 추가
- PUT /todos/<id>: 할 일 상태 업데이트

## 환경 변수

애플리케이션은 다음 환경 변수들을 사용합니다:

### PostgreSQL 설정

- POSTGRES_USER: PostgreSQL 사용자 이름
- POSTGRES_PASSWORD: PostgreSQL 비밀번호
- POSTGRES_HOST: PostgreSQL 호스트
- POSTGRES_PORT: PostgreSQL 포트
- POSTGRES_DB: PostgreSQL 데이터베이스 이름

### Flask 설정

- FLASK_ENV: Flask 실행 환경 (development/production)
- FLASK_DEBUG: 디버그 모드 활성화 여부 (0/1)
