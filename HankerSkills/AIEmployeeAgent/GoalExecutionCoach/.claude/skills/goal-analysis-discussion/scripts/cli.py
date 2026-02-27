#!/usr/bin/env python3
"""
CLI 命令行接口
提供命令行方式操作 goal-analysis-discussion
"""

import argparse
import os
import sys
import json

# 获取脚本根目录
if '__file__' in dir():
    SCRIPTS_DIR = os.path.dirname(__file__)
else:
    SCRIPTS_DIR = os.path.join(os.getcwd(), 'scripts')

# 导入所有功能模块
exec(open(os.path.join(SCRIPTS_DIR, 'init_db.py')).read())
exec(open(os.path.join(SCRIPTS_DIR, 'identify_issues.py')).read())
exec(open(os.path.join(SCRIPTS_DIR, 'create_session.py')).read())
exec(open(os.path.join(SCRIPTS_DIR, 'conversation_flow.py')).read())


def cmd_init(args):
    """初始化数据库"""
    print("Initializing database...")
    init_database()
    print("Database initialized successfully.")


def cmd_identify(args):
    """识别问题"""
    issue_type = args.type if args.type else 'both'
    severity = args.severity if args.severity else None

    print(f"Identifying {issue_type} issues")
    if severity:
        print(f"  Severity filter: {severity}")
    print()

    issues = identify_all_issues(issue_type=issue_type, severity_filter=severity)

    print("Target Benchmark Issues:")
    for issue in issues['target_issues']:
        severity_mark = ""
        if issue.get('severity') == 'critical':
            severity_mark = " [严重]"
        elif issue.get('severity') == 'moderate':
            severity_mark = " [中等]"
        elif issue.get('severity') == 'mild':
            severity_mark = " [轻微]"
        print(f"  - {issue['name']}: {issue['progress']}%{severity_mark}")

    print("\nStatus Benchmark Issues:")
    for issue in issues['status_issues']:
        severity_mark = ""
        if issue.get('severity') == 'critical':
            severity_mark = " [严重]"
        elif issue.get('severity') == 'moderate':
            severity_mark = " [中等]"
        elif issue.get('severity') == 'mild':
            severity_mark = " [轻微]"
        print(f"  - {issue['name']}: {issue['consecutive_missed']} consecutive misses{severity_mark}")

    print("\n" + format_issues_summary(issues))


def cmd_session_create(args):
    """创建会话"""
    trigger_source = args.trigger if args.trigger else 'manual'
    trigger_reason = args.reason if args.reason else '手动创建'
    analysis_mode = args.mode if args.mode else 'quick'
    severity_level = args.severity if args.severity else None

    print(f"Creating session (trigger: {trigger_source}, reason: {trigger_reason}, mode: {analysis_mode})...")
    if severity_level:
        print(f"  Severity: {severity_level}")

    result = create_analysis_session(
        trigger_source=trigger_source,
        trigger_reason=trigger_reason,
        severity_level=severity_level,
        analysis_mode=analysis_mode
    )

    print(f"\nSession ID: {result['session_id']}")
    print(f"\nInitial Prompt:\n{result['initial_prompt']}")


def cmd_session_list(args):
    """列出会话"""
    status = args.status if args.status else None
    limit = args.limit if args.limit else 10

    print(f"Listing sessions (status: {status if status else 'all'}, limit: {limit})...\n")

    sessions = get_sessions(status=status, limit=limit)

    if not sessions:
        print("No sessions found.")
        return

    for session in sessions:
        print(f"ID: {session['id']}")
        print(f"  Type: {session['session_type']}")
        print(f"  Trigger: {session['trigger_source']} - {session['trigger_reason']}")
        print(f"  Focus: {session['focus_area']}")
        print(f"  Status: {session['status']}")
        print(f"  Created: {session['created_at']}")
        if session['summary']:
            print(f"  Summary: {session['summary'][:100]}...")
        print()


def cmd_session_show(args):
    """查看会话详情"""
    session_id = args.id
    session = get_session(session_id)

    if not session:
        print(f"Session {session_id} not found.")
        return

    print("Session Details:")
    print(format_session_summary(session))

    # 显示消息
    print("\nMessages:")
    messages = get_messages(session_id)
    for msg in messages:
        role_display = "User" if msg['role'] == 'user' else "Assistant"
        type_display = f" [{msg['message_type']}]" if msg['message_type'] else ""
        print(f"\n[{role_display}]{type_display}")
        print(f"  {msg['content']}")


def cmd_session_archive(args):
    """归档会话"""
    session_id = args.id
    print(f"Archiving session {session_id}...")

    success = archive_session(session_id)

    if success:
        print("Session archived successfully.")
    else:
        print("Failed to archive session.")


def cmd_message_add(args):
    """添加消息"""
    session_id = args.session_id
    role = args.role
    content = args.content
    message_type = args.type if args.type else None

    print(f"Adding message to session {session_id}...")

    message_id = add_message(
        session_id=session_id,
        role=role,
        content=content,
        message_type=message_type
    )

    print(f"Message added successfully (ID: {message_id}).")


def cmd_message_list(args):
    """列出会话消息"""
    session_id = args.session_id
    limit = args.limit if args.limit else None

    print(f"Messages for session {session_id}:\n")

    messages = get_messages(session_id, limit=limit)

    if not messages:
        print("No messages found.")
        return

    for i, msg in enumerate(messages, 1):
        role_display = "User" if msg['role'] == 'user' else "Assistant"
        type_display = f" [{msg['message_type']}]" if msg['message_type'] else ""
        timestamp = msg['created_at'][:16] if msg['created_at'] else ""
        print(f"[{i}] [{timestamp}] [{role_display}]{type_display}")
        print(f"    {msg['content']}\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Goal Analysis Discussion CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py init                           # Initialize database
  python cli.py identify                       # Identify all issues
  python cli.py identify --type target          # Identify only target issues
  python cli.py session create                  # Create a new session
  python cli.py session create --trigger scheduled --reason "Weekly analysis"
  python cli.py session list                    # List all sessions
  python cli.py session list --status active    # List active sessions
  python cli.py session show --id 1            # Show session details
  python cli.py session archive --id 1          # Archive a session
  python cli.py message add --session-id 1 --role user --content "Test message"
  python cli.py message list --session-id 1     # List session messages
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # init 命令
    subparsers.add_parser('init', help='Initialize database')

    # identify 命令
    parser_identify = subparsers.add_parser('identify', help='Identify issues')
    parser_identify.add_argument('--type', choices=['target', 'status', 'both'],
                               help='Type of issues to identify')
    parser_identify.add_argument('--severity', choices=['critical', 'moderate', 'mild', 'all'],
                               help='Filter by severity level (default: all)')

    # session 命令
    parser_session = subparsers.add_parser('session', help='Manage sessions')
    session_subparsers = parser_session.add_subparsers(dest='session_command', help='Session commands')

    parser_session_create = session_subparsers.add_parser('create', help='Create a new session')
    parser_session_create.add_argument('--trigger', choices=['manual', 'scheduled', 'alert'],
                                      default='manual', help='Trigger source')
    parser_session_create.add_argument('--reason', type=str, default='手动创建',
                                      help='Trigger reason')
    parser_session_create.add_argument('--mode', choices=['deep', 'quick'], default='quick',
                                      help='Analysis mode (default: quick)')
    parser_session_create.add_argument('--severity', choices=['critical', 'moderate', 'mild'],
                                      help='Issue severity level (optional)')

    parser_session_list = session_subparsers.add_parser('list', help='List sessions')
    parser_session_list.add_argument('--status', choices=['active', 'resolved', 'on_hold'],
                                    help='Filter by status')
    parser_session_list.add_argument('--limit', type=int, default=10,
                                    help='Maximum number of sessions to return')

    parser_session_show = session_subparsers.add_parser('show', help='Show session details')
    parser_session_show.add_argument('--id', type=int, required=True,
                                    help='Session ID')

    parser_session_archive = session_subparsers.add_parser('archive', help='Archive a session')
    parser_session_archive.add_argument('--id', type=int, required=True,
                                       help='Session ID')

    # message 命令
    parser_message = subparsers.add_parser('message', help='Manage messages')
    message_subparsers = parser_message.add_subparsers(dest='message_command', help='Message commands')

    parser_message_add = message_subparsers.add_parser('add', help='Add a message')
    parser_message_add.add_argument('--session-id', type=int, required=True,
                                   help='Session ID')
    parser_message_add.add_argument('--role', choices=['user', 'assistant'], required=True,
                                   help='Message role')
    parser_message_add.add_argument('--content', type=str, required=True,
                                   help='Message content')
    parser_message_add.add_argument('--type', choices=['question', 'analysis', 'suggestion', 'confirmation'],
                                   help='Message type')

    parser_message_list = message_subparsers.add_parser('list', help='List messages')
    parser_message_list.add_argument('--session-id', type=int, required=True,
                                    help='Session ID')
    parser_message_list.add_argument('--limit', type=int, help='Maximum number of messages to return')

    args = parser.parse_args()

    # 根据命令执行对应操作
    if args.command == 'init':
        cmd_init(args)
    elif args.command == 'identify':
        cmd_identify(args)
    elif args.command == 'session':
        if args.session_command == 'create':
            cmd_session_create(args)
        elif args.session_command == 'list':
            cmd_session_list(args)
        elif args.session_command == 'show':
            cmd_session_show(args)
        elif args.session_command == 'archive':
            cmd_session_archive(args)
        else:
            parser_session.print_help()
    elif args.command == 'message':
        if args.message_command == 'add':
            cmd_message_add(args)
        elif args.message_command == 'list':
            cmd_message_list(args)
        else:
            parser_message.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
