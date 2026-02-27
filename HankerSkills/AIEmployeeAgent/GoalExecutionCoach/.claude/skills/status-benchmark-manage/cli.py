#!/usr/bin/env python3
"""
Status Benchmark Manager CLI

为定时任务和外部工具提供命令行接口。
支持更新 benchmarks、生成报告等功能。
"""

import argparse
import sys
import os

# 添加 scripts 目录到路径
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), 'scripts')
sys.path.insert(0, SCRIPTS_DIR)

from calculate_values import update_all_benchmarks, update_single_benchmark, generate_report
from manage_benchmarks import get_benchmarks_by_period, get_all_benchmarks


def cmd_update(args):
    """更新 benchmarks"""
    print(f"🔄 Updating benchmarks (period: {args.period})...")

    if args.id:
        # 更新单个 benchmark
        result = update_single_benchmark(args.id)
        if result['success']:
            print(f"✓ Updated benchmark {result['benchmark_id']}: {result['name']}")
            print(f"  Current: {result['current_value']} {result['unit']}")
            print(f"  Target: {result['comparison_type']} {result['target_value']} {result['unit']}")
            print(f"  Status: {'✅ Met' if result['is_met'] else '❌ Not met'}")
        else:
            print(f"✗ Error updating benchmark {args.id}: {result['error']}")
            return 1
    else:
        # 批量更新
        if args.period == 'all':
            results = update_all_benchmarks()
        else:
            benchmarks = get_benchmarks_by_period(args.period)
            results = []
            for b in benchmarks:
                result = update_single_benchmark(b['id'])
                results.append(result)

        # 输出结果摘要
        success_count = sum(1 for r in results if r['success'])
        fail_count = len(results) - success_count

        print(f"\n✓ Updated {success_count} benchmarks successfully")
        if fail_count > 0:
            print(f"✗ Failed to update {fail_count} benchmarks")
            for result in results:
                if not result['success']:
                    print(f"  - ID {result['benchmark_id']}: {result['error']}")

    # 输出报告
    if args.output_report:
        print("\n" + generate_report())

    return 0


def cmd_report(args):
    """生成并输出报告"""
    print(generate_report())
    return 0


def cmd_check_stale(args):
    """检查未更新的 benchmarks（用于定时催促提醒）"""
    from datetime import datetime, timedelta

    period = args.period
    max_age_hours = args.max_age_hours

    benchmarks = get_benchmarks_by_period(period)

    stale_benchmarks = []
    now = datetime.now()

    for b in benchmarks:
        if not b['last_calculated_at']:
            # 从未计算过
            stale_benchmarks.append((b, 'Never calculated'))
        else:
            # 解析时间
            try:
                last_calc = datetime.strptime(b['last_calculated_at'], '%Y-%m-%d %H:%M:%S')
                age = (now - last_calc).total_seconds() / 3600  # 转换为小时

                if age > max_age_hours:
                    stale_benchmarks.append((b, f'Last updated {age:.1f} hours ago'))
            except Exception as e:
                stale_benchmarks.append((b, f'Invalid timestamp: {e}'))

    if stale_benchmarks:
        print(f"⚠️  Found {len(stale_benchmarks)} stale benchmarks (period: {period})")
        print("-" * 60)
        for b, reason in stale_benchmarks:
            status = "✅" if b['is_met'] else "❌"
            print(f"  [{status}] {b['name']}")
            print(f"      Target: {b['comparison_type']} {b['target_value']} {b['unit']}")
            print(f"      Current: {b['current_value']} {b['unit']}")
            print(f"      {reason}")
            print()
        return 1
    else:
        print(f"✓ All {period} benchmarks are up to date")
        return 0


def main():
    parser = argparse.ArgumentParser(
        description='Status Benchmark Manager CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s update --period daily --output-report
  %(prog)s update --period weekly
  %(prog)s report
  %(prog)s check-stale --period daily --max-age-hours 12
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # update 命令
    update_parser = subparsers.add_parser('update', help='Update benchmarks')
    update_parser.add_argument(
        '--period',
        choices=['daily', 'weekly', 'all'],
        default='all',
        help='Update benchmarks of specific period (default: all)'
    )
    update_parser.add_argument(
        '--id',
        type=int,
        help='Update a specific benchmark by ID'
    )
    update_parser.add_argument(
        '--output-report',
        action='store_true',
        help='Output report after updating'
    )
    update_parser.set_defaults(func=cmd_update)

    # report 命令
    report_parser = subparsers.add_parser('report', help='Generate and display report')
    report_parser.add_argument(
        '--period',
        choices=['daily', 'weekly', 'all'],
        default='all',
        help='Show benchmarks of specific period (default: all)'
    )
    report_parser.set_defaults(func=cmd_report)

    # check-stale 命令
    stale_parser = subparsers.add_parser('check-stale', help='Check for outdated benchmarks')
    stale_parser.add_argument(
        '--period',
        choices=['daily', 'weekly'],
        required=True,
        help='Check benchmarks of specific period'
    )
    stale_parser.add_argument(
        '--max-age-hours',
        type=float,
        default=12,
        help='Maximum age in hours before considered stale (default: 12)'
    )
    stale_parser.set_defaults(func=cmd_check_stale)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
