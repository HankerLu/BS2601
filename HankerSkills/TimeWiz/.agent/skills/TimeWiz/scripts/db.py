
import json
import os
import uuid
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Ensure data directory exists
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

TODO_FILE = os.path.join(DATA_DIR, 'todos.json')
DONE_FILE = os.path.join(DATA_DIR, 'done.json')

def load_todos():
    if not os.path.exists(TODO_FILE):
        return []
    with open(TODO_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_todos(todos):
    with open(TODO_FILE, 'w') as f:
        json.dump(todos, f, indent=4)

def load_done():
    if not os.path.exists(DONE_FILE):
        return []
    with open(DONE_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_done(done_items):
    with open(DONE_FILE, 'w') as f:
        json.dump(done_items, f, indent=4)

def add_todo(description, duration, priority):
    todos = load_todos()
    task = {
        'id': str(uuid.uuid4()),
        'description': description,
        'duration': duration, # duration in minutes
        'priority': priority, # High, Medium, Low
        'created_at': datetime.now().isoformat()
    }
    todos.append(task)
    save_todos(todos)
    return task

def get_todo_by_id(task_id):
    todos = load_todos()
    for task in todos:
        if task['id'] == task_id:
            return task
    return None

def complete_todo(task_id):
    todos = load_todos()
    done_items = load_done()
    
    # Check if task_id matches exactly or is a prefix/substring match if unique
    # Here let's assume exact match or partial if unambiguous for simplicity in CLI usage
    # But for robustness, let's target exact ID or pass in index in a refined version.
    # For now, strict ID matching.
    
    task_to_move = None
    remaining_todos = []
    
    for task in todos:
        if task['id'] == task_id:
            task_to_move = task
        else:
            remaining_todos.append(task)
    
    if task_to_move:
        task_to_move['completed_at'] = datetime.now().isoformat()
        done_items.append(task_to_move)
        save_todos(remaining_todos)
        save_done(done_items)
        return task_to_move
    return None

def clear_todos():
    save_todos([])

def clear_done():
    save_done([])
