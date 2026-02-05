
from datetime import datetime, timedelta
from db import load_todos

def _get_priority_value(priority):
    p = str(priority).lower()
    if p == 'high': return 3
    if p == 'medium': return 2
    if p == 'low': return 1
    return 0

def generate_schedule():
    todos = load_todos()
    if not todos:
        return "No tasks scheduled for today."
    
    # Sort by priority (descending)
    sorted_todos = sorted(todos, key=lambda x: _get_priority_value(x.get('priority', 'low')), reverse=True)
    
    current_time = datetime.now()
    schedule_lines = []
    
    header = f"📅 Today's Schedule (Generated at {current_time.strftime('%H:%M')})"
    schedule_lines.append(header)
    schedule_lines.append("-" * len(header))
    
    for task in sorted_todos:
        start_time = current_time
        duration_minutes = int(task.get('duration', 30))
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        time_range = f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
        line = f"[{time_range}] {task.get('description', 'Task')} ({duration_minutes}m) [{task.get('priority', 'Low')}]"
        schedule_lines.append(line)
        
        current_time = end_time
        
    schedule_lines.append("-" * len(header))
    schedule_lines.append(f"Estimated Finish Time: {current_time.strftime('%H:%M')}")
    
    return "\n".join(schedule_lines)
