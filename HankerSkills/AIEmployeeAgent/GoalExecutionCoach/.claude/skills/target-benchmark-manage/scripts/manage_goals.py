#!/usr/bin/env python3
"""
目标管理脚本
处理目标的增删改查操作
"""

import sqlite3
import os
from datetime import datetime

# 获取数据库路径（支持直接调用和exec调用）
if '__file__' in dir():
    DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'targets.db')
else:
    DB_PATH = os.path.join(os.getcwd(), 'data', 'targets.db')


def add_target(name, target_value, unit, deadline, current_value=0):
    """添加新目标"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO targets (name, target_value, unit, deadline, current_value)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, float(target_value), unit, deadline, float(current_value)))

        conn.commit()
        target_id = cursor.lastrowid
        conn.close()
        return target_id
    except Exception as e:
        conn.close()
        raise e


def update_current_value(target_id, current_value):
    """更新目标的当前数值"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE targets
            SET current_value = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (float(current_value), int(target_id)))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        raise e


def update_target(target_id, name=None, target_value=None, unit=None, deadline=None):
    """修改目标信息"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    updates = []
    values = []

    if name:
        updates.append("name = ?")
        values.append(name)
    if target_value:
        updates.append("target_value = ?")
        values.append(float(target_value))
    if unit is not None:
        updates.append("unit = ?")
        values.append(unit)
    if deadline:
        updates.append("deadline = ?")
        values.append(deadline)

    if not updates:
        conn.close()
        return False

    values.append(int(target_id))
    query = f"UPDATE targets SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"

    try:
        cursor.execute(query, values)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        raise e


def delete_target(target_id):
    """删除目标"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('DELETE FROM targets WHERE id = ?', (int(target_id),))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        raise e


def get_all_targets():
    """获取所有目标"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, name, target_value, unit, deadline, current_value,
               created_at, updated_at
        FROM targets
        ORDER BY deadline
    ''')

    columns = ['id', 'name', 'target_value', 'unit', 'deadline',
               'current_value', 'created_at', 'updated_at']
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))

    conn.close()
    return results


def get_target(target_id):
    """获取单个目标"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, name, target_value, unit, deadline, current_value,
               created_at, updated_at
        FROM targets WHERE id = ?
    ''', (int(target_id),))

    row = cursor.fetchone()
    conn.close()

    if row:
        columns = ['id', 'name', 'target_value', 'unit', 'deadline',
                   'current_value', 'created_at', 'updated_at']
        return dict(zip(columns, row))
    return None
