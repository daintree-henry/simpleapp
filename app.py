from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
from dotenv import load_dotenv
from urllib.parse import quote_plus
import logging

# .env 로드
load_dotenv()

# Flask 앱 설정
app = Flask(__name__)

# PostgreSQL 연결 문자열 파싱 (.env에 AZURE_POSTGRESQL_CONNECTIONSTRING 포함 필요)
conn_str = os.getenv("AZURE_POSTGRESQL_CONNECTIONSTRING")
if conn_str:
    parts = dict(item.split("=", 1) for item in conn_str.split(";") if item)
    user = parts.get("User Id")
    password = quote_plus(parts.get("Password"))  
    host = parts.get("Server")
    db = parts.get("Database")
    uri = f"postgresql://{user}:{password}@{host}:5432/{db}"
    os.environ["SQLALCHEMY_DATABASE_URI"] = uri

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["SQLALCHEMY_DATABASE_URI"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# DB 초기화
db = SQLAlchemy(app)

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)
logger = logging.getLogger(__name__)

# 모델 정의
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'completed': self.completed,
            'created_at': self.created_at.isoformat()
        }

# DB 테이블 생성
with app.app_context():
    db.create_all()

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
