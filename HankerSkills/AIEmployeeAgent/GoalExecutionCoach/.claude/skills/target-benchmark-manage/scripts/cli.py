#!/usr/bin/env python3
"""
Target Benchmark Manager CLI

为定时任务和外部工具提供命令行接口。
支持生成目标进度报告等功能。
"""

import argparse
import sys
import os

# 添加 scripts 目录到路径
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), 'scripts')
sys.path.insert(0, SCRIPTS_DIR)

from calculate_progress import generate_report, get_target_summary
from manage_goals import get_all_targets, get_target, update_current_value


def cmd_report(args):
    """生成并输出报告"""
    if args.id:
        # 输出单个目标的报告
        summary = get_target_summary(args.id)
        print(summary)
    else:
        # 输出所有目标的报告
        print(generate_report())
    return 0


def cmd_list(args):
    """列出所有目标（简洁格式）"""
    targets = get_all_targets()

    if not targets:
        print("目前没有设置任何目标。")
        return 0

    print(f"{'ID':<4} {'名称':<20} {'目标值':<15} {'当前值':<15} {'截止日期':<12}")
    print("-" * 70)

    for t in targets:
        target_display = f"{t['target_value']} {t['unit'] or ''}"
        current_display = f"{t['current_value']} {t['unit'] or ''}"
        print(f"{t['id']:<4} {t['name']:<20} {target_display:<15} {current_display:<15} {t['deadline']:<12}")

    return 0


def cmd_update(args):
    """更新目标的当前数值"""
    if not args.value:
        print("Error: --value is required for update command")
        return 1

    if not args.id:
        print("Error: --id is required for update command")
        return 1

    try:
        update_current_value(args.id, args.value)
        print(f"✓ Updated target {args.id} to {args.value}")
        return 0
    except Exception as e:
        print(f"✗ Error updating target: {e}")
        return 1


def cmd_check_near_deadline(args):
    """检查即将到期的目标（用于提醒）"""
    from datetime import datetime, timedelta

    targets = get_all_targets()
    now = datetime.now()

    near_deadline_targets = []

    for t in targets:
        deadline = datetime.strptime(t['deadline'], '%Y-%m-%d')
        days_left = (deadline - now.date()).days

        if days_left <= args.days_threshold:
            near_deadline_targets.append((t, days_left))

    if near_deadline_targets:
        print(f"⚠️  Found {len(near_deadline_targets)} target(s) near deadline:")
        print("-" * 60)
        for t, days_left in near_deadline_targets:
            emoji = "🚨" if days_left < 0 else "⏰"
            days_str = f"{days_left}天 (已过期!)" if days_left < 0 else f"{days_left}天"
            print(f"  [{emoji}] {t['name']}")
            print(f"      Deadline: {t['deadline']} ({days_str})")
            print(f"      Target: {t['target_value']} {t['unit'] or ''}")
            print(f"      Current: {t['current_value']} {t['unit'] or ''}")
            print()
        return 1
    else:
        print(f"✓ No targets with deadline within {args.days_threshold} days")
        return 0


def main():
    parser = argparse.ArgumentParser(
        description='Target Benchmark Manager CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s report
  %(prog)s report --id 1
  %(prog)s list
  %(prog)s update --id 1 --value 75.5
  %(prog)s check-near-deadline --days 7
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # report 命令
    report_parser = subparsers.add_parser('report', help='Generate and display report')
    report_parser.add_argument(
        '--id',
        type=int,
        help='Report a specific target by ID'
    )
    report_parser.set_defaults(func=cmd_report)

    # list 命令
    list_parser = subparsers.add_parser('list', help='List all targets (compact format)')
    list_parser.set_defaults(func=cmd_list)

    # update 命令
    update_parser = subparsers.add_parser('update', help='Update current value of a target')
    update_parser.add_argument(
        '--id',
        type=int,
        required=True,
        help='Target ID to update'
    )
    update_parser.add_argument(
        '--value',
        type=float,
        required=True,
        help='New current value'
    )
    update_parser.set_defaults(func=cmd_update)

    # check-near-deadline 命令
    deadline_parser = subparsers.add_parser('check-near-deadline', help='Check targets near deadline')
    deadline_parser.add_argument(
        '--days',
        type=int,
        dest='days_threshold',
        default=7,
        help='Number of days threshold (default: 7)'
    )
    deadline_parser.set_defaults(func=cmd_check_near_deadline)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
