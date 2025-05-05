from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from db_initializer import ensure_database_and_initialize
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from urllib.parse import quote_plus
import logging

# .env 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Flask 앱 설정
app = Flask(__name__)

# 환경변수 기반 설정
db_user = os.getenv("DB_USER")
db_password = quote_plus(os.getenv("DB_PASSWORD", ""))
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT", "5432")
db_name = os.getenv("DB_NAME", "todo_db")

ensure_database_and_initialize()

if all([db_user, db_password, db_host, db_port, db_name]):
    db_uri = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    logger.info("✅ SQLALCHEMY_DATABASE_URI 설정 완료")
else:
    logger.error("❌ 데이터베이스 환경변수가 일부 누락되었습니다.")
    raise RuntimeError("DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME 환경변수를 모두 설정해주세요.")

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# 모델 정의
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'completed': self.completed,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# 개발 시에만 테이블 자동 생성
if os.getenv('FLASK_DEBUG', '0') == '1':
    with app.app_context():
        db.create_all()
        logger.info("✅ 개발 환경에서 DB 테이블 자동 생성됨")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/todos', methods=['GET'])
def get_todos():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    completed = request.args.get('completed', type=str)

    logger.debug(f"GET /todos?page={page}&per_page={per_page}&completed={completed}")

    try:
        query = Todo.query
        if completed is not None:
            completed_bool = completed.lower() == 'true'
            query = query.filter(Todo.completed == completed_bool)
            logger.info(f"Filtering completed={completed_bool}")

        pagination = query.order_by(Todo.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        todos = [todo.to_dict() for todo in pagination.items]

        logger.info(f"Returned {len(todos)} todos")

        return jsonify({
            'todos': todos,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        })
    except Exception as e:
        logger.exception("Error fetching todos")
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/todos', methods=['POST'])
def create_todo():
    data = request.get_json()
    title = data.get('title', '').strip()

    if not title:
        logger.warning("Empty title submitted")
        return jsonify({'error': 'Title is required'}), 400

    title = title[:100]  # DB 제한 보호

    try:
        new_todo = Todo(title=title)
        db.session.add(new_todo)
        db.session.commit()
        logger.info(f"Created todo: {title}")
        return jsonify(new_todo.to_dict()), 201
    except Exception as e:
        logger.exception("Error creating todo")
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    data = request.get_json()
    completed = data.get('completed')

    if not isinstance(completed, bool):
        logger.warning(f"Invalid 'completed' value: {completed}")
        return jsonify({'error': 'completed must be a boolean'}), 400

    logger.debug(f"Update request for id={todo_id}, completed={completed}")

    try:
        todo.completed = completed
        db.session.commit()
        logger.info(f"Updated todo {todo_id} to completed={completed}")
        return jsonify(todo.to_dict())
    except Exception as e:
        logger.exception("Error updating todo")
        return jsonify({'error': 'Internal Server Error'}), 500

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', '0') == '1')
