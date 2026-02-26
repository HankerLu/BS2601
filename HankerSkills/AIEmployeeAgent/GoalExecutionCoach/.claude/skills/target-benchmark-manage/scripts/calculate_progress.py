#!/usr/bin/env python3
"""
进度计算脚本
计算目标的完成进度并生成报告
"""

import sqlite3
import os
from datetime import datetime

# 获取数据库路径（支持直接调用和exec调用）
if '__file__' in dir():
    DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'targets.db')
else:
    DB_PATH = os.path.join(os.getcwd(), 'data', 'targets.db')


def calculate_progress(target_value, current_value, starting_value=None):
    """计算完成进度百分比"""
    # 如果有起始值且当前值小于起始值，说明是减少类目标（如减重）
    if starting_value is not None and current_value < starting_value:
        total_to_reduce = starting_value - target_value
        if total_to_reduce == 0:
            return 100.0
        already_reduced = starting_value - current_value
        progress = (already_reduced / total_to_reduce) * 100
        return min(round(progress, 2), 100.0)
    else:
        # 普通增长类目标
        if target_value == 0:
            return 0
        progress = (current_value / target_value) * 100
        return min(round(progress, 2), 100.0)


def calculate_days_remaining(deadline):
    """计算剩余天数"""
    deadline_date = datetime.strptime(deadline, '%Y-%m-%d').date()
    today = datetime.now().date()
    delta = deadline_date - today
    return delta.days


def generate_report():
    """生成进度报告"""
    # 直接查询数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, name, target_value, unit, deadline, current_value, starting_value
        FROM targets
        ORDER BY deadline
    ''')

    columns = ['id', 'name', 'target_value', 'unit', 'deadline', 'current_value', 'starting_value']
    targets = []
    for row in cursor.fetchall():
        targets.append(dict(zip(columns, row)))

    conn.close()

    if not targets:
        return "目前没有设置任何目标。"

    report_lines = ["=" * 60]
    report_lines.append("📊 目标进度报告")
    report_lines.append("=" * 60)

    for target in targets:
        progress = calculate_progress(target['target_value'], target['current_value'], target.get('starting_value'))
        days_remaining = calculate_days_remaining(target['deadline'])

        # 判断状态
        if progress >= 100:
            status = "✅ 已完成"
        elif days_remaining < 0:
            status = "⚠️ 已过期"
        else:
            status = "🔄 进行中"

        report_lines.append(f"\n📌 {target['name']}")
        report_lines.append(f"   起始值: {target.get('starting_value', '-')} {target['unit'] or ''}")
        report_lines.append(f"   目标值: {target['target_value']} {target['unit'] or ''}")
        report_lines.append(f"   当前值: {target['current_value']} {target['unit'] or ''}")
        report_lines.append(f"   进度: {progress}%")
        report_lines.append(f"   截止日期: {target['deadline']} ({days_remaining}天)")
        report_lines.append(f"   状态: {status}")

    report_lines.append("\n" + "=" * 60)

    return "\n".join(report_lines)


def get_target_summary(target_id):
    """获取单个目标的摘要信息"""
    # 直接查询数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, name, target_value, unit, deadline, current_value, starting_value, updated_at
        FROM targets WHERE id = ?
    ''', (int(target_id),))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return f"未找到 ID 为 {target_id} 的目标"

    columns = ['id', 'name', 'target_value', 'unit', 'deadline', 'current_value', 'starting_value', 'updated_at']
    target = dict(zip(columns, row))

    progress = calculate_progress(target['target_value'], target['current_value'], target.get('starting_value'))
    days_remaining = calculate_days_remaining(target['deadline'])

    starting_line = f"起始值: {target.get('starting_value', '-')} {target['unit'] or ''}\n   " if target.get('starting_value') else ''
    summary = f"""
目标: {target['name']}
{starting_line}目标值: {target['target_value']} {target['unit'] or ''}
当前值: {target['current_value']} {target['unit'] or ''}
进度: {progress}%
截止日期: {target['deadline']} ({days_remaining}天)
最后更新: {target['updated_at']}
    """.strip()

    return summary
