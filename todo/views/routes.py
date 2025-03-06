from flask import Blueprint, jsonify, request 
from todo.models import db 
from todo.models.todo import Todo 
from datetime import datetime, timedelta
 
api = Blueprint('api', __name__, url_prefix='/api/v1') 

TEST_ITEM = {
    "id": 1,
    "title": "Watch CSSE6400 Lecture",
    "description": "Watch the CSSE6400 lecture on ECHO360 for week 1",
    "completed": True,
    "deadline_at": "2023-02-27T00:00:00",
    "created_at": "2023-02-20T00:00:00",
    "updated_at": "2023-02-20T00:00:00"
}
 
@api.route('/health') 
def health():
    """Return a status of 'ok' if the server is running and listening to request"""
    return jsonify({"status": "ok"})


@api.route('/todos', methods=['GET'])
def get_todos():
    # Start with all todos
    query = Todo.query

    # Filter by completion status if 'completed' parameter is present
    completed_param = request.args.get('completed')
    if completed_param is not None:
        completed = completed_param.lower() == 'true'
        query = query.filter(Todo.completed == completed)

    # Filter by time window if 'window' parameter is present
    window_param = request.args.get('window')
    if window_param is not None:
        try:
            window_days = int(window_param)
            now = datetime.now()
            query = query.filter(Todo.deadline_at <= now + timedelta(days=window_days))
        except ValueError:
            return jsonify({'error': 'Invalid window parameter'}), 400

    todos = query.all()
    result = [todo.to_dict() for todo in todos]
    return jsonify(result)

@api.route('/todos/<int:todo_id>', methods=['GET'])
def get_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404
    return jsonify(todo.to_dict())

@api.route('/todos', methods=['POST'])
def create_todo():    # Check for unexpected fields
    allowed_fields = {'title', 'description', 'completed', 'deadline_at'}
    if not set(request.json.keys()).issubset(allowed_fields):
        return jsonify({'error': 'Unexpected fields in request'}), 400
    
    if request.json.get('title') is None:
        return jsonify({'error': 'Missing required fields'}), 400
    
    todo = Todo(
        title=request.json.get('title'),
        description=request.json.get('description'),
        completed=request.json.get('completed', False),
    )
    
    if 'deadline_at' in request.json and request.json.get('deadline_at') is not None:
        todo.deadline_at = datetime.fromisoformat(request.json.get('deadline_at'))
    db.session.add(todo)
    db.session.commit()
    return jsonify(todo.to_dict()), 201

@api.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404
    # Prevent ID changes
    if 'id' in request.json:
        return jsonify({'error': 'ID cannot be changed'}), 400
    # Check for unexpected fields
    allowed_fields = {'title', 'description', 'completed', 'deadline_at'}
    if not set(request.json.keys()).issubset(allowed_fields):
        return jsonify({'error': 'Unexpected fields in request'}), 400
    
    todo.title = request.json.get('title', todo.title)
    todo.description = request.json.get('description', todo.description)
    todo.completed = request.json.get('completed', todo.completed)
    todo.deadline_at = request.json.get('deadline_at', todo.deadline_at)
    db.session.commit()
    return jsonify(todo.to_dict())

@api.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({}), 200
    db.session.delete(todo)
    db.session.commit()
    return jsonify(todo.to_dict()), 200
 
