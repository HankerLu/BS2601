#!/usr/bin/env python3
"""
状态达标线管理脚本
处理 status benchmark 的增删改查操作
"""

import sqlite3
import os
from datetime import datetime

# 获取数据库路径（支持直接调用和exec调用）
if '__file__' in dir():
    DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'status_benchmarks.db')
else:
    DB_PATH = os.path.join(os.getcwd(), 'data', 'status_benchmarks.db')


def add_benchmark(name, target_value, unit, period, comparison_type,
                   calculation_script, source_url=None):
    """添加新的 status benchmark"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO status_benchmarks
            (name, target_value, unit, period, comparison_type,
             calculation_script, source_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, float(target_value), unit, period, comparison_type,
              calculation_script, source_url))

        conn.commit()
        benchmark_id = cursor.lastrowid
        conn.close()
        return benchmark_id
    except Exception as e:
        conn.close()
        raise e


def update_benchmark(benchmark_id, name=None, target_value=None, unit=None,
                     period=None, comparison_type=None, calculation_script=None,
                     source_url=None):
    """修改 benchmark 信息"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    updates = []
    values = []

    if name:
        updates.append("name = ?")
        values.append(name)
    if target_value is not None:
        updates.append("target_value = ?")
        values.append(float(target_value))
    if unit is not None:
        updates.append("unit = ?")
        values.append(unit)
    if period:
        updates.append("period = ?")
        values.append(period)
    if comparison_type:
        updates.append("comparison_type = ?")
        values.append(comparison_type)
    if calculation_script:
        updates.append("calculation_script = ?")
        values.append(calculation_script)
    if source_url is not None:
        updates.append("source_url = ?")
        values.append(source_url)

    if not updates:
        conn.close()
        return False

    values.append(int(benchmark_id))
    query = f"UPDATE status_benchmarks SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"

    try:
        cursor.execute(query, values)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        raise e


def delete_benchmark(benchmark_id):
    """删除 benchmark"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('DELETE FROM status_benchmarks WHERE id = ?', (int(benchmark_id),))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        raise e


def get_all_benchmarks():
    """获取所有 benchmarks"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, name, target_value, unit, period, comparison_type,
               current_value, is_met, calculation_script, source_url,
               created_at, updated_at, last_calculated_at
        FROM status_benchmarks
        ORDER BY period, id
    ''')

    columns = ['id', 'name', 'target_value', 'unit', 'period', 'comparison_type',
               'current_value', 'is_met', 'calculation_script', 'source_url',
               'created_at', 'updated_at', 'last_calculated_at']
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))

    conn.close()
    return results


def get_benchmark(benchmark_id):
    """获取单个 benchmark"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, name, target_value, unit, period, comparison_type,
               current_value, is_met, calculation_script, source_url,
               created_at, updated_at, last_calculated_at
        FROM status_benchmarks WHERE id = ?
    ''', (int(benchmark_id),))

    row = cursor.fetchone()
    conn.close()

    if row:
        columns = ['id', 'name', 'target_value', 'unit', 'period', 'comparison_type',
                   'current_value', 'is_met', 'calculation_script', 'source_url',
                   'created_at', 'updated_at', 'last_calculated_at']
        return dict(zip(columns, row))
    return None


def get_benchmarks_by_period(period):
    """根据周期获取 benchmarks (daily 或 weekly)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, name, target_value, unit, period, comparison_type,
               current_value, is_met, calculation_script, source_url,
               created_at, updated_at, last_calculated_at
        FROM status_benchmarks WHERE period = ?
        ORDER BY id
    ''', (period,))

    columns = ['id', 'name', 'target_value', 'unit', 'period', 'comparison_type',
               'current_value', 'is_met', 'calculation_script', 'source_url',
               'created_at', 'updated_at', 'last_calculated_at']
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))

    conn.close()
    return results


def update_current_value(benchmark_id, current_value, is_met):
    """更新 benchmark 的当前值和达标状态"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE status_benchmarks
            SET current_value = ?, is_met = ?, updated_at = CURRENT_TIMESTAMP,
                last_calculated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (float(current_value), int(is_met), int(benchmark_id)))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        raise e
