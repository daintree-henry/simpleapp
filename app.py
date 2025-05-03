from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import redis
import os
from datetime import datetime
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

app = Flask(__name__)

# PostgreSQL 설정
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Redis 설정
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST'),
    port=int(os.getenv('REDIS_PORT')),
    db=int(os.getenv('REDIS_DB'))
)

# Todo 모델 정의
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

# 데이터베이스 초기화
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/todos', methods=['GET'])
def get_todos():
    # Redis에서 캐시된 할 일 목록 확인
    cached_todos = redis_client.get('todos')
    if cached_todos:
        return jsonify(eval(cached_todos))
    
    # PostgreSQL에서 할 일 목록 조회
    todos = Todo.query.order_by(Todo.created_at.desc()).all()
    todo_list = [todo.to_dict() for todo in todos]
    
    # Redis에 캐시 저장 (1시간)
    redis_client.setex('todos', 3600, str(todo_list))
    
    return jsonify(todo_list)

@app.route('/todos', methods=['POST'])
def create_todo():
    data = request.get_json()
    new_todo = Todo(title=data['title'])
    db.session.add(new_todo)
    db.session.commit()
    
    # Redis 캐시 삭제
    redis_client.delete('todos')
    
    return jsonify(new_todo.to_dict()), 201

@app.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    data = request.get_json()
    
    todo.completed = data.get('completed', todo.completed)
    db.session.commit()
    
    # Redis 캐시 삭제
    redis_client.delete('todos')
    
    return jsonify(todo.to_dict())

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', '0') == '1') 