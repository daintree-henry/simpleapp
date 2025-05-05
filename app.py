from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
from dotenv import load_dotenv
from urllib.parse import quote_plus

# .env 파일 로드
load_dotenv()

app = Flask(__name__)

# PostgreSQL 설정
# Azure App Service 연결 문자열 파싱
conn_str = os.getenv("AZURE_POSTGRESQL_CONNECTIONSTRING")

if conn_str:
    parts = dict(item.split("=", 1) for item in conn_str.split(";") if item)
    user = parts.get("User Id")
    password = quote_plus(parts.get("Password"))  
    host = parts.get("Server")
    db = parts.get("Database")

    uri = f"postgresql://{user}:{password}@{host}:5432/{db}"
    os.environ["SQLALCHEMY_DATABASE_URI"] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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
    # PostgreSQL에서 할 일 목록 조회
    todos = Todo.query.order_by(Todo.created_at.desc()).all()
    todo_list = [todo.to_dict() for todo in todos]
    return jsonify(todo_list)

@app.route('/todos', methods=['POST'])
def create_todo():
    data = request.get_json()
    new_todo = Todo(title=data['title'])
    db.session.add(new_todo)
    db.session.commit()
    return jsonify(new_todo.to_dict()), 201

@app.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    data = request.get_json()
    
    todo.completed = data.get('completed', todo.completed)
    db.session.commit()
    
    return jsonify(todo.to_dict())

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', '0') == '1') 