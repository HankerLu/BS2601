
import json
import os
import sys

# Setup paths
base_dir = os.getcwd()
sys.path.append(os.path.join(base_dir, '.agent/skills/TimeWiz/scripts'))

# Mock data
todos = [
    {"id": "low-id", "description": "Low Priority Task", "duration": 30, "priority": "Low", "created_at": "2023-01-01T10:00:00"},
    {"id": "high-id", "description": "High Priority Task", "duration": 30, "priority": "High", "created_at": "2023-01-01T10:05:00"}
]
todo_file = '.agent/skills/TimeWiz/data/todos.json'
done_file = '.agent/skills/TimeWiz/data/done.json'

# Ensure directory
os.makedirs(os.path.dirname(todo_file), exist_ok=True)

# Write mock data
with open(todo_file, 'w') as f:
    json.dump(todos, f)
with open(done_file, 'w') as f:
    json.dump([], f)

print("--- Initial State (Storage Order) ---")
print(f"Index 0: {todos[0]['description']} ({todos[0]['priority']})")
print(f"Index 1: {todos[1]['description']} ({todos[1]['priority']})")

print("\n--- Running 'list' command (Display Order) ---")
# Import valid modules to run list
from main import handle_list, handle_done
import argparse

# Mock args for list
class Args:
    pass

print("Capturing output of list...")
# We can't easily capture stdout without redirecting, but let's just run it to see.
# Ideally scheduler.py generates string, we can verify that.
from scheduler import generate_schedule
print(generate_schedule()) 
# Expected: High task first.

print("\n--- Executing 'done 1' ---")
# User sees High task as #1 (first item in schedule output)
# User runs 'done 1'
args_done = Args()
args_done.task_id = "1"
handle_done(args_done)

print("\n--- Checking what was completed ---")
with open(done_file, 'r') as f:
    dones = json.load(f)

if dones:
    completed_task = dones[0]
    print(f"Completed Task: {completed_task['description']}")
    if completed_task['priority'] == "High":
        print("RESULT: CORRECT (High task completed)")
    else:
        print("RESULT: BUG CONFIRMED (Wrong task completed!)")
else:
    print("RESULT: No tasks completed?")
