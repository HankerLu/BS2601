
import argparse
import sys
import os
from datetime import datetime

# Allow importing sibling modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import add_todo, load_todos, complete_todo, load_done
from scheduler import generate_schedule
from visualizer import generate_wordcloud

def handle_add(args):
    try:
        duration = int(args.duration)
        if duration <= 0:
            raise ValueError
    except ValueError:
        print("Error: Duration must be a positive integer (minutes).")
        return

    priority = args.priority.capitalize()
    
    add_todo(args.description, duration, priority)
    print(f"Added: {args.description} ({duration}m, {priority})")

def handle_list(args):
    schedule_text = generate_schedule()
    print(schedule_text)

def handle_done(args):
    task_id = args.task_id
    
    # Try by exact ID
    result = complete_todo(task_id)
    if not result:
        # Try by 1-based index
        try:
            todos = load_todos()
            idx = int(task_id) - 1
            if 0 <= idx < len(todos):
                real_id = todos[idx]['id']
                result = complete_todo(real_id)
        except ValueError:
            pass

    if result:
        print(f"Completed: {result['description']}")
        print("\nUpdated Schedule:")
        print(generate_schedule())
    else:
        print(f"Error: Task '{task_id}' not found.")

def handle_report(args):
    done_items = load_done()
    if not done_items:
        print("No completed tasks.")
        return
        
    print(f"Completed Tasks ({len(done_items)}):")
    for i, item in enumerate(done_items, 1):
        completed_at = item.get('completed_at', '')
        if completed_at:
             dt = datetime.fromisoformat(completed_at)
             time_str = dt.strftime('%H:%M')
        else:
             time_str = "Unknown"
        print(f"{i}. {item['description']} ({item['duration']}m) - At {time_str}")

def handle_cloud(args):
    output_path = generate_wordcloud()
    print(f"Word cloud saved to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="TimeWiz Task Manager")
    subparsers = parser.add_subparsers(dest='command', help='Command')

    # Add
    p_add = subparsers.add_parser('add', help='Add task')
    p_add.add_argument('description')
    p_add.add_argument('duration', type=int)
    p_add.add_argument('priority', choices=['High', 'Medium', 'Low', 'high', 'medium', 'low'])

    # List
    subparsers.add_parser('list', help='Show schedule')

    # Done
    p_done = subparsers.add_parser('done', help='Complete task')
    p_done.add_argument('task_id', help='ID or Index')

    # Report
    subparsers.add_parser('report', help='Show completed')

    # Cloud
    subparsers.add_parser('cloud', help='Word cloud')

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    
    if args.command == 'add': handle_add(args)
    elif args.command == 'list': handle_list(args)
    elif args.command == 'done': handle_done(args)
    elif args.command == 'report': handle_report(args)
    elif args.command == 'cloud': handle_cloud(args)

if __name__ == "__main__":
    main()
