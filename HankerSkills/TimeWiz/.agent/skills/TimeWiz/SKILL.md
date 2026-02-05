---
name: TimeWiz
description: A comprehensive time management assistant for tracking daily tasks, generating prioritized schedules, and visualizing productivity.
---

# TimeWiz Skill

TimeWiz helps users manage their daily tasks by automatically generating schedules based on priorities and duration, tracking completion, and providing visual summaries of accomplishments.

## Capabilities

1.  **Task Entry**: Add tasks with description, duration, and priority (High, Medium, Low).
2.  **Smart Scheduling**: Generates a timeline starting from the current moment, ordering tasks by priority.
3.  **Completion Tracking**: Mark tasks as done to update the schedule and move them to a history log.
4.  **Reporting**: View completed tasks list or generate a word cloud visualization.

## Instructions

When the user interacts with TimeWiz, use the provided Python scripts in the `scripts/` directory to perform actions. 
**ALWAYS run the scripts from the root directory of the skill:** `/Users/hankerlu/Desktop/BS2601/HankerSkills/TimeWiz/.agent/skills/TimeWiz`

### 1. Adding a Task
When the user wants to add a task, ask for duration and priority if not provided.
Command:
```bash
python3 scripts/main.py add "<description>" <duration_in_minutes> <priority>
```
Example:
```bash
python3 scripts/main.py add "Write Report" 45 High
```

### 2. Generating/Viewing Schedule
To show the current daily schedule based on remaining tasks and current time:
Command:
```bash
python3 scripts/main.py list
```

### 3. Completing a Task
When a user finishes a task, mark it as done. You can use the task ID (if known) or the 1-based index from the `list` command.
Command:
```bash
python3 scripts/main.py done <task_id_or_index>
```
Example:
```bash
python3 scripts/main.py done 1
```

### 4. Viewing Completed Tasks (Done List)
To see a text report of what has been accomplished:
Command:
```bash
python3 scripts/main.py report
```

### 5. Visualizing Progress (Word Cloud)
To generate a visual word cloud of completed tasks (saved as HTML):
Command:
```bash
python3 scripts/main.py cloud
```
The script will output the path to the generated HTML file. You should then tell the user where it is or open it if possible.

## Data Storage
- Active tasks: `data/todos.json`
- Completed history: `data/done.json`
- Visualizations: `output/wordcloud.html`

## Technical Notes
- The scheduler automatically sorts tasks by Priority (High > Medium > Low) and then by entry order.
- Schedule times are recalculated dynamically based on the *current system time* whenever `list` or `done` is called.
