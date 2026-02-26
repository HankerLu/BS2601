#!/usr/bin/env python3
"""
状态值计算和达标判定脚本
计算 benchmark 的当前值并判定是否达标
"""

import sqlite3
import os
import sys
from datetime import datetime, date, timedelta

# 获取数据库路径（支持直接调用和exec调用）
if '__file__' in dir():
    DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'status_benchmarks.db')
    SCRIPTS_DIR = os.path.dirname(__file__)
else:
    DB_PATH = os.path.join(os.getcwd(), 'data', 'status_benchmarks.db')
    SCRIPTS_DIR = os.path.join(os.getcwd(), 'scripts')


def get_period_range(period_type):
    """
    获取当前周期的开始和结束时间

    Args:
        period_type: 'daily' 或 'weekly'

    Returns:
        tuple: (period_start, period_end) 都是 datetime 对象
    """
    now = datetime.now()

    if period_type == 'daily':
        # 今天的开始和结束
        period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        period_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif period_type == 'weekly':
        # 本周的开始（周一）和结束（周日）
        # 获取今天是星期几 (0=周一, 6=周日)
        today = now.date()
        weekday = today.weekday()  # Monday is 0
        period_start = datetime.combine(today - timedelta(days=weekday), datetime.min.time())
        period_end = datetime.combine(today + timedelta(days=6-weekday), datetime.max.time())
    else:
        raise ValueError(f"Unsupported period type: {period_type}")

    return period_start, period_end


def check_if_met(current_value, target_value, comparison_type):
    """
    判断是否达标

    Args:
        current_value: 当前值
        target_value: 目标值
        comparison_type: '>=' 或 '<='

    Returns:
        bool: 是否达标
    """
    if comparison_type == '>=':
        return current_value >= target_value
    elif comparison_type == '<=':
        return current_value <= target_value
    else:
        raise ValueError(f"Unsupported comparison type: {comparison_type}")


def calculate_gap(current_value, target_value, comparison_type):
    """
    计算与目标的差距

    Args:
        current_value: 当前值
        target_value: 目标值
        comparison_type: '>=' 或 '<='

    Returns:
        float: 差距值（正值表示还需要多少才能达标）
    """
    if comparison_type == '>=':
        gap = target_value - current_value
        return max(0, gap)  # 已达标则返回0
    elif comparison_type == '<=':
        gap = current_value - target_value
        return max(0, gap)  # 已达标则返回0
    else:
        raise ValueError(f"Unsupported comparison type: {comparison_type}")


def determine_metric_type(benchmark_name):
    """
    根据 benchmark 名称确定 metric_type

    Args:
        benchmark_name: benchmark 的名称，例如 "每日工作时间"

    Returns:
        str: metric_type，例如 "daily_work_time"
    """
    # 定义名称到 metric_type 的映射
    metric_mappings = {
        '每日工作时间': 'daily_work_time',
        '每周工作时间': 'weekly_work_time',
        '每日创作时间': 'daily_creation_time',
        '每周创作时间': 'weekly_creation_time',
        '每日娱乐+放松时间': 'daily_entertainment_time',
        '每日运动时间': 'daily_exercise_time',
        '每周运动时间': 'weekly_exercise_time',
    }

    return metric_mappings.get(benchmark_name, None)


def load_and_execute_calculation_script(script_path, period_start, period_end, metric_type=None):
    """
    加载并执行计算脚本

    Args:
        script_path: 计算脚本路径（相对于 scripts/ 目录）
        period_start: 周期开始时间
        period_end: 周期结束时间
        metric_type: 可选，指定要计算的指标类型

    Returns:
        float: 计算得到的当前值
    """
    full_script_path = os.path.join(SCRIPTS_DIR, script_path)

    if not os.path.exists(full_script_path):
        raise FileNotFoundError(f"Calculation script not found: {full_script_path}")

    # 将脚本路径转换为模块导入路径
    # 例如: "fetch_data/fetch_feishu_data.py" -> "scripts.fetch_data.fetch_feishu_data"
    module_path = script_path.replace('/', '.').replace('.py', '')

    try:
        # 动态导入模块
        import importlib.util
        spec = importlib.util.spec_from_file_location(module_path, full_script_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_path] = module
        spec.loader.exec_module(module)

        # 获取 calculate_current_value 函数
        if hasattr(module, 'calculate_current_value'):
            # 尝试传入 metric_type 参数（如果函数支持）
            try:
                current_value = module.calculate_current_value(period_start, period_end, metric_type)
            except TypeError:
                # 如果函数不支持 metric_type 参数，使用旧的调用方式（向后兼容）
                current_value = module.calculate_current_value(period_start, period_end)
            return float(current_value)
        else:
            raise ValueError("Script does not define 'calculate_current_value' function")
    except Exception as e:
        raise Exception(f"Error executing calculation script {script_path}: {str(e)}")


def update_single_benchmark(benchmark_id):
    """
    更新单个 benchmark 的当前值和达标状态

    Args:
        benchmark_id: benchmark 的 ID

    Returns:
        dict: 包含更新结果的字典
    """
    # 获取 benchmark 信息
    from manage_benchmarks import get_benchmark, update_current_value

    benchmark = get_benchmark(benchmark_id)

    if not benchmark:
        raise ValueError(f"Benchmark with ID {benchmark_id} not found")

    # 获取周期时间范围
    period_start, period_end = get_period_range(benchmark['period'])

    # 确定要计算的指标类型
    metric_type = determine_metric_type(benchmark['name'])

    # 调用计算脚本
    try:
        current_value = load_and_execute_calculation_script(
            benchmark['calculation_script'],
            period_start,
            period_end,
            metric_type
        )

        # 判断是否达标
        is_met = check_if_met(current_value, benchmark['target_value'],
                             benchmark['comparison_type'])

        # 更新数据库
        update_current_value(benchmark_id, current_value, is_met)

        # 计算差距
        gap = calculate_gap(current_value, benchmark['target_value'],
                           benchmark['comparison_type'])

        return {
            'success': True,
            'benchmark_id': benchmark_id,
            'name': benchmark['name'],
            'current_value': current_value,
            'target_value': benchmark['target_value'],
            'comparison_type': benchmark['comparison_type'],
            'is_met': is_met,
            'gap': gap if not is_met else 0,
            'unit': benchmark['unit'],
            'period': benchmark['period'],
            'period_start': period_start,
            'period_end': period_end
        }
    except Exception as e:
        return {
            'success': False,
            'benchmark_id': benchmark_id,
            'error': str(e)
        }


def update_all_benchmarks():
    """
    更新所有 benchmarks 的当前值和达标状态

    Returns:
        list: 包含所有 benchmark 更新结果的列表
    """
    from manage_benchmarks import get_all_benchmarks

    benchmarks = get_all_benchmarks()
    results = []

    for benchmark in benchmarks:
        result = update_single_benchmark(benchmark['id'])
        results.append(result)

    return results


def generate_report():
    """生成达标报告"""
    from manage_benchmarks import get_all_benchmarks

    benchmarks = get_all_benchmarks()

    if not benchmarks:
        return "目前没有设置任何状态达标线。"

    # 分为 daily 和 weekly 两组
    daily_benchmarks = [b for b in benchmarks if b['period'] == 'daily']
    weekly_benchmarks = [b for b in benchmarks if b['period'] == 'weekly']

    report_lines = ["=" * 60]
    report_lines.append("📊 状态达标线报告")
    report_lines.append("=" * 60)

    # 处理 daily benchmarks
    if daily_benchmarks:
        report_lines.append("\n📅 每日达标线")
        report_lines.append("-" * 60)
        for b in daily_benchmarks:
            status = "✅ 已达标" if b['is_met'] else "❌ 未达标"
            if not b['is_met']:
                gap = calculate_gap(b['current_value'], b['target_value'], b['comparison_type'])
                gap_info = f" (差距 {gap}{b['unit'] or ''})"
            else:
                gap_info = ""

            report_lines.append(f"\n📌 {b['name']}")
            report_lines.append(f"   目标值: {b['comparison_type']} {b['target_value']} {b['unit'] or ''}")
            report_lines.append(f"   当前值: {b['current_value']} {b['unit'] or ''}")
            report_lines.append(f"   达标状态: {status}{gap_info}")
            if b['last_calculated_at']:
                report_lines.append(f"   最后计算: {b['last_calculated_at']}")

    # 处理 weekly benchmarks
    if weekly_benchmarks:
        report_lines.append("\n📅 每周达标线")
        report_lines.append("-" * 60)
        for b in weekly_benchmarks:
            status = "✅ 已达标" if b['is_met'] else "❌ 未达标"
            if not b['is_met']:
                gap = calculate_gap(b['current_value'], b['target_value'], b['comparison_type'])
                gap_info = f" (差距 {gap}{b['unit'] or ''})"
            else:
                gap_info = ""

            report_lines.append(f"\n📌 {b['name']}")
            report_lines.append(f"   目标值: {b['comparison_type']} {b['target_value']} {b['unit'] or ''}")
            report_lines.append(f"   当前值: {b['current_value']} {b['unit'] or ''}")
            report_lines.append(f"   达标状态: {status}{gap_info}")
            if b['last_calculated_at']:
                report_lines.append(f"   最后计算: {b['last_calculated_at']}")

    report_lines.append("\n" + "=" * 60)

    return "\n".join(report_lines)


def get_benchmark_summary(benchmark_id):
    """获取单个 benchmark 的摘要信息"""
    from manage_benchmarks import get_benchmark

    benchmark = get_benchmark(benchmark_id)

    if not benchmark:
        return f"未找到 ID 为 {benchmark_id} 的状态达标线"

    status = "✅ 已达标" if benchmark['is_met'] else "❌ 未达标"

    if not benchmark['is_met']:
        gap = calculate_gap(benchmark['current_value'], benchmark['target_value'],
                          benchmark['comparison_type'])
        gap_info = f"\n   差距: {gap}{benchmark['unit'] or ''}"
    else:
        gap_info = ""

    summary = f"""
状态达标线: {benchmark['name']}
周期: {benchmark['period']}
目标值: {benchmark['comparison_type']} {benchmark['target_value']} {benchmark['unit'] or ''}
当前值: {benchmark['current_value']} {benchmark['unit'] or ''}
达标状态: {status}{gap_info}
最后更新: {benchmark['updated_at']}
最后计算: {benchmark['last_calculated_at'] or '未计算'}
计算脚本: {benchmark['calculation_script']}
数据源: {benchmark['source_url'] or '未指定'}
    """.strip()

    return summary


if __name__ == "__main__":
    # 测试：更新所有 benchmarks 并生成报告
    print("Updating all benchmarks...")
    results = update_all_benchmarks()

    for result in results:
        if result['success']:
            print(f"✓ {result['name']}: {result['current_value']} {result['unit']} (target: {result['comparison_type']} {result['target_value']})")
        else:
            print(f"✗ {result['benchmark_id']}: {result['error']}")

    print("\n" + generate_report())
