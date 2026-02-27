#!/usr/bin/env python3
"""
问题识别脚本
从 target-benchmark-manage 和 status-benchmark-manage 读取数据，识别问题指标
"""

import sqlite3
import os
import json
from datetime import datetime

# 获取数据库路径（支持直接调用和exec调用）
if '__file__' in dir():
    DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'analyses.db')
    SKILL_ROOT = os.path.dirname(__file__)
else:
    DB_PATH = os.path.join(os.getcwd(), 'data', 'analyses.db')
    SKILL_ROOT = os.path.join(os.getcwd(), 'scripts')

# 两个源数据库的路径
TARGET_DB_PATH = os.path.join(os.getcwd(), '..', 'target-benchmark-manage', 'data', 'targets.db')
STATUS_DB_PATH = os.path.join(os.getcwd(), '..', 'status-benchmark-manage', 'data', 'status_benchmarks.db')


def get_all_targets():
    """获取所有 target benchmarks"""
    if not os.path.exists(TARGET_DB_PATH):
        return []

    conn = sqlite3.connect(TARGET_DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, name, target_value, unit, deadline, current_value
        FROM targets
        ORDER BY deadline
    ''')

    columns = ['id', 'name', 'target_value', 'unit', 'deadline', 'current_value']
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))

    conn.close()
    return results


def get_all_status_benchmarks():
    """获取所有 status benchmarks"""
    if not os.path.exists(STATUS_DB_PATH):
        return []

    conn = sqlite3.connect(STATUS_DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, name, target_value, unit, period, comparison_type, current_value, is_met
        FROM status_benchmarks
        ORDER BY period, id
    ''')

    columns = ['id', 'name', 'target_value', 'unit', 'period', 'comparison_type', 'current_value', 'is_met']
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))

    conn.close()
    return results


def get_consecutive_missed_status(benchmark_id, threshold=3):
    """
    获取 status benchmark 的连续未达标次数

    需要动态导入 status-benchmark-manage 的函数
    """
    status_skill_root = os.path.dirname(os.path.dirname(SKILL_ROOT))

    # 动态导入 manage_benchmarks 模块
    import sys
    sys.path.insert(0, os.path.join(status_skill_root, 'status-benchmark-manage', 'scripts'))

    try:
        from manage_benchmarks import get_consecutive_missed
        return get_consecutive_missed(benchmark_id, threshold)
    except Exception as e:
        print(f"Warning: Could not get consecutive missed count: {e}")
        return 0


def calculate_target_progress(target):
    """
    计算 target benchmark 的进度

    Args:
        target: target benchmark 字典

    Returns:
        float: 进度百分比
    """
    target_value = target['target_value']
    current_value = target['current_value']

    if target_value == 0:
        return 0.0

    # 假设初始值为0（这是默认值）
    progress = (current_value / target_value) * 100

    # 如果目标是减重（current > target），进度应该反向计算
    # 这里简化处理，假设目标方向是 current 越接近 target 越好
    # 实际应该根据具体情况判断

    return round(progress, 2)


def get_days_remaining(deadline_str):
    """
    计算剩余天数

    Args:
        deadline_str: 截止日期字符串，格式为 YYYY-MM-DD

    Returns:
        int: 剩余天数
    """
    deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
    today = datetime.now().date()
    delta = deadline - today
    return delta.days


def classify_target_issue_severity(target):
    """
    判定 target benchmark 的问题严重程度

    Args:
        target: target benchmark 字典（需包含 progress 和 days_remaining）

    Returns:
        str: 严重程度 'critical' | 'moderate' | 'mild' | None
    """
    progress = target.get('progress', 0)
    days_remaining = target.get('days_remaining', 0)

    # 临界时间调整：剩余时间越少，同等进度越严重
    time_factor = 1.0
    if days_remaining < 30:
        time_factor = 1.5  # 剩余时间少，加重判定
    elif days_remaining < 7:
        time_factor = 2.0  # 剩余时间极少，大幅加重

    adjusted_threshold = 5.0 * time_factor

    if progress < adjusted_threshold:
        return 'critical'
    elif progress < 15.0:
        return 'moderate'
    elif progress < 30.0:
        return 'mild'
    else:
        return None


def classify_status_issue_severity(benchmark):
    """
    判定 status benchmark 的问题严重程度

    Args:
        benchmark: status benchmark 字典（需包含 consecutive_missed 和 is_met）

    Returns:
        str: 严重程度 'critical' | 'moderate' | 'mild' | None
    """
    consecutive_missed = benchmark.get('consecutive_missed', 0)

    if consecutive_missed >= 3:
        return 'critical'
    elif consecutive_missed >= 2:
        return 'moderate'
    elif consecutive_missed >= 1:
        return 'mild'
    else:
        return None


def identify_target_issues(targets, severity_filter=None):
    """
    识别有问题的 target benchmarks（支持分级）

    Args:
        targets: 所有 target benchmarks 列表
        severity_filter: 过滤严重程度（可选），'critical' | 'moderate' | 'mild' | None（全部）

    Returns:
        list: 有问题的 target benchmarks 列表
    """
    issues = []

    for target in targets:
        # 计算进度和剩余天数
        progress = calculate_target_progress(target)
        days_remaining = get_days_remaining(target['deadline'])

        # 判定严重程度
        severity = classify_target_issue_severity({
            'progress': progress,
            'days_remaining': days_remaining
        })

        # 如果有严重程度且符合过滤条件
        if severity and (severity_filter is None or severity == severity_filter):
            issue = {
                'id': target['id'],
                'name': target['name'],
                'target_value': target['target_value'],
                'current_value': target['current_value'],
                'unit': target['unit'],
                'progress': progress,
                'deadline': target['deadline'],
                'days_remaining': days_remaining,
                'severity': severity
            }
            issues.append(issue)

    return issues


def identify_status_issues(status_benchmarks, severity_filter=None):
    """
    识别有问题的 status benchmarks（支持分级）

    Args:
        status_benchmarks: 所有 status benchmarks 列表
        severity_filter: 过滤严重程度（可选），'critical' | 'moderate' | 'mild' | None（全部）

    Returns:
        list: 有问题的 status benchmarks 列表
    """
    issues = []

    for benchmark in status_benchmarks:
        # 获取连续未达标次数
        consecutive_missed = get_consecutive_missed_status(
            benchmark['id'],
            10  # 获取更多历史
        )

        # 判定严重程度
        severity = classify_status_issue_severity({
            'consecutive_missed': consecutive_missed
        })

        # 如果有严重程度且符合过滤条件
        if severity and (severity_filter is None or severity == severity_filter):
            issue = {
                'id': benchmark['id'],
                'name': benchmark['name'],
                'target_value': benchmark['target_value'],
                'current_value': benchmark['current_value'],
                'unit': benchmark['unit'],
                'period': benchmark['period'],
                'comparison_type': benchmark['comparison_type'],
                'consecutive_missed': consecutive_missed,
                'severity': severity
            }
            issues.append(issue)

    return issues


def get_target_by_name(name):
    """
    根据名称查找 target benchmark

    Args:
        name: target benchmark 的名称

    Returns:
        dict: target benchmark 信息（包含进度和剩余天数）
    """
    targets = get_all_targets()

    for target in targets:
        if target['name'].lower() == name.lower():
            progress = calculate_target_progress(target)
            days_remaining = get_days_remaining(target['deadline'])
            return {
                **target,
                'progress': progress,
                'days_remaining': days_remaining
            }

    # 模糊匹配
    for target in targets:
        if name.lower() in target['name'].lower():
            progress = calculate_target_progress(target)
            days_remaining = get_days_remaining(target['deadline'])
            return {
                **target,
                'progress': progress,
                'days_remaining': days_remaining
            }

    return None


def get_status_by_name(name):
    """
    根据名称查找 status benchmark

    Args:
        name: status benchmark 的名称

    Returns:
        dict: status benchmark 信息（包含连续未达标次数）
    """
    status_benchmarks = get_all_status_benchmarks()

    for benchmark in status_benchmarks:
        if benchmark['name'].lower() == name.lower():
            consecutive_missed = get_consecutive_missed_status(benchmark['id'], 10)
            return {
                **benchmark,
                'consecutive_missed': consecutive_missed
            }

    # 模糊匹配
    for benchmark in status_benchmarks:
        if name.lower() in benchmark['name'].lower():
            consecutive_missed = get_consecutive_missed_status(benchmark['id'], 10)
            return {
                **benchmark,
                'consecutive_missed': consecutive_missed
            }

    return None


def get_target_by_id(target_id):
    """
    获取指定的 target benchmark

    Args:
        target_id: target benchmark 的 ID

    Returns:
        dict: target benchmark 信息（包含进度和剩余天数）
    """
    targets = get_all_targets()

    for target in targets:
        if target['id'] == int(target_id):
            progress = calculate_target_progress(target)
            days_remaining = get_days_remaining(target['deadline'])
            return {
                **target,
                'progress': progress,
                'days_remaining': days_remaining
            }

    return None


def get_status_by_id(status_id):
    """
    获取指定的 status benchmark

    Args:
        status_id: status benchmark 的 ID

    Returns:
        dict: status benchmark 信息（包含连续未达标次数）
    """
    status_benchmarks = get_all_status_benchmarks()

    for benchmark in status_benchmarks:
        if benchmark['id'] == int(status_id):
            consecutive_missed = get_consecutive_missed_status(benchmark['id'], 10)
            return {
                **benchmark,
                'consecutive_missed': consecutive_missed
            }

    return None


def get_targets_for_analysis(criteria='issues', target_id=None):
    """
    获取用于分析的 target benchmarks

    Args:
        criteria: 选择标准
            - 'issues': 只返回有问题的（进度 < 5%）
            - 'all': 返回全部
            - 'specific': 返回指定的
        target_id: 当 criteria='specific' 时使用，指定 target 的 ID

    Returns:
        list: target benchmarks 列表
    """
    targets = get_all_targets()

    if criteria == 'issues':
        return identify_target_issues(targets)
    elif criteria == 'all':
        # 为所有 target 计算进度和剩余天数
        return [
            {
                **target,
                'progress': calculate_target_progress(target),
                'days_remaining': get_days_remaining(target['deadline'])
            }
            for target in targets
        ]
    elif criteria == 'specific' and target_id:
        target = get_target_by_id(target_id)
        return [target] if target else []
    else:
        return []


def get_status_for_analysis(criteria='issues', status_id=None):
    """
    获取用于分析的 status benchmarks

    Args:
        criteria: 选择标准
            - 'issues': 只返回有问题的（连续 3 次未达标）
            - 'all': 返回全部
            - 'specific': 返回指定的
        status_id: 当 criteria='specific' 时使用，指定 status 的 ID

    Returns:
        list: status benchmarks 列表
    """
    status_benchmarks = get_all_status_benchmarks()

    if criteria == 'issues':
        return identify_status_issues(status_benchmarks)
    elif criteria == 'all':
        # 为所有 status 计算连续未达标次数
        return [
            {
                **benchmark,
                'consecutive_missed': get_consecutive_missed_status(benchmark['id'], 10)
            }
            for benchmark in status_benchmarks
        ]
    elif criteria == 'specific' and status_id:
        status = get_status_by_id(status_id)
        return [status] if status else []
    else:
        return []


def identify_all_issues(issue_type='both', severity_filter=None):
    """
    识别所有问题指标（支持分级）

    Args:
        issue_type: 问题类型，'target' | 'status' | 'both'（默认）
        severity_filter: 过滤严重程度，'critical' | 'moderate' | 'mild' | None（全部）

    Returns:
        dict: 包含 target_issues 和 status_issues 的字典
    """
    result = {
        'target_issues': [],
        'status_issues': []
    }

    # 识别 target benchmark 问题
    if issue_type in ['target', 'both']:
        targets = get_all_targets()
        result['target_issues'] = identify_target_issues(targets, severity_filter)

    # 识别 status benchmark 问题
    if issue_type in ['status', 'both']:
        status_benchmarks = get_all_status_benchmarks()
        result['status_issues'] = identify_status_issues(status_benchmarks, severity_filter)

    return result


def format_issues_summary(issues):
    """
    格式化问题摘要，用于对话呈现

    Args:
        issues: identify_all_issues 返回的字典

    Returns:
        str: 格式化的问题摘要
    """
    lines = []

    # Target Benchmark 问题
    if issues['target_issues']:
        # 按严重程度分组
        by_severity = {'critical': [], 'moderate': [], 'mild': []}
        for issue in issues['target_issues']:
            severity = issue.get('severity', 'unknown')
            by_severity[severity].append(issue)

        # 严重问题
        if by_severity['critical']:
            lines.append("\n【严重问题】Target Benchmark")
            for issue in by_severity['critical']:
                lines.append(f"• {issue['name']}: 进度仅 {issue['progress']}%")
                lines.append(f"  目标 {issue['target_value']}{issue['unit']}，当前 {issue['current_value']}{issue['unit']}")
                lines.append(f"  截止日期: {issue['deadline']}，剩余 {issue['days_remaining']} 天\n")

        # 中等问题
        if by_severity['moderate']:
            lines.append("\n【中等问题】Target Benchmark")
            for issue in by_severity['moderate']:
                lines.append(f"• {issue['name']}: 进度 {issue['progress']}%")
                lines.append(f"  目标 {issue['target_value']}{issue['unit']}，当前 {issue['current_value']}{issue['unit']}")
                lines.append(f"  截止日期: {issue['deadline']}，剩余 {issue['days_remaining']} 天\n")

        # 轻微问题
        if by_severity['mild']:
            lines.append("\n【轻微问题】Target Benchmark")
            for issue in by_severity['mild']:
                lines.append(f"• {issue['name']}: 进度 {issue['progress']}%")
                lines.append(f"  目标 {issue['target_value']}{issue['unit']}，当前 {issue['current_value']}{issue['unit']}\n")

    # Status Benchmark 问题
    if issues['status_issues']:
        # 按严重程度分组
        by_severity = {'critical': [], 'moderate': [], 'mild': []}
        for issue in issues['status_issues']:
            severity = issue.get('severity', 'unknown')
            by_severity[severity].append(issue)

        # 严重问题
        if by_severity['critical']:
            lines.append("\n【严重问题】Status Benchmark")
            for issue in by_severity['critical']:
                lines.append(f"• {issue['name']}: 连续 {issue['consecutive_missed']} 次未达标")
                lines.append(f"  目标 {issue['comparison_type']} {issue['target_value']} {issue['unit']}")
                lines.append(f"  当前 {issue['current_value']} {issue['unit']}\n")

        # 中等问题
        if by_severity['moderate']:
            lines.append("\n【中等问题】Status Benchmark")
            for issue in by_severity['moderate']:
                lines.append(f"• {issue['name']}: 连续 {issue['consecutive_missed']} 次未达标")
                lines.append(f"  目标 {issue['comparison_type']} {issue['target_value']} {issue['unit']}")
                lines.append(f"  当前 {issue['current_value']} {issue['unit']}\n")

        # 轻微问题
        if by_severity['mild']:
            lines.append("\n【轻微问题】Status Benchmark")
            for issue in by_severity['mild']:
                lines.append(f"• {issue['name']}: 连续 {issue['consecutive_missed']} 次未达标")
                lines.append(f"  目标 {issue['comparison_type']} {issue['target_value']} {issue['unit']}")
                lines.append(f"  当前 {issue['current_value']} {issue['unit']}\n")

    if not lines:
        return "没有发现需要分析的指标。"

    # 如果只有轻微问题，添加提示
    target_issues = issues.get('target_issues', []) or []
    status_issues = issues.get('status_issues', []) or []
    if all(issue.get('severity') == 'mild' for issue in target_issues + status_issues):
        lines.append("\n💡 提示：目前没有严重问题。如需深入分析，可以指定具体指标或选择全面分析模式。")

    return "\n".join(lines)


if __name__ == "__main__":
    # 测试：识别所有问题
    issues = identify_all_issues()

    print("Target Benchmark Issues:")
    for issue in issues['target_issues']:
        print(f"  - {issue['name']}: {issue['progress']}%")

    print("\nStatus Benchmark Issues:")
    for issue in issues['status_issues']:
        print(f"  - {issue['name']}: {issue['consecutive_missed']} consecutive misses")

    print("\nFormatted Summary:")
    print(format_issues_summary(issues))
