#!/usr/bin/env python3
"""
会话管理脚本
创建、更新、查询分析会话
"""

import sqlite3
import os
import json
from datetime import datetime

# 获取数据库路径（支持直接调用和exec调用）
if '__file__' in dir():
    DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'analyses.db')
else:
    DB_PATH = os.path.join(os.getcwd(), 'data', 'analyses.db')


def create_session(trigger_source, trigger_reason, focus_area,
                   related_target_id=None, related_status_id=None,
                   issues_identified=None, severity_level=None, analysis_mode='quick'):
    """
    创建新的分析会话

    Args:
        trigger_source: 触发来源 ('manual' | 'scheduled' | 'alert')
        trigger_reason: 触发原因
        focus_area: 关注区域 ('target' | 'status' | 'both')
        related_target_id: 关联的 target benchmark ID（可选）
        related_status_id: 关联的 status benchmark ID（可选）
        issues_identified: 识别的问题列表（字典），会转为 JSON 存储
        severity_level: 问题严重程度 'critical' | 'moderate' | 'mild'（可选）
        analysis_mode: 分析模式 'deep' | 'quick'（默认 'quick'）

    Returns:
        int: 新会话的 ID
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 将 issues_identified 转为 JSON 字符串
    issues_json = json.dumps(issues_identified) if issues_identified else None

    try:
        cursor.execute('''
            INSERT INTO analysis_sessions
            (session_type, trigger_source, trigger_reason, focus_area,
             related_target_id, related_status_id, issues_identified,
             severity_level, analysis_mode, status, conversation_stage)
            VALUES ('active', ?, ?, ?, ?, ?, ?, ?, ?, 'active', 'initial')
        ''', (trigger_source, trigger_reason, focus_area,
              related_target_id, related_status_id, issues_json,
              severity_level, analysis_mode))

        conn.commit()
        session_id = cursor.lastrowid
        conn.close()
        return session_id
    except Exception as e:
        conn.close()
        raise e


def update_session_conversation_stage(session_id, stage, substage=None):
    """
    更新会话的对话阶段

    Args:
        session_id: 会话 ID
        stage: 新的对话阶段
        substage: 子阶段（可选）

    Returns:
        bool: 是否成功
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        if substage:
            cursor.execute('''
                UPDATE analysis_sessions
                SET conversation_stage = ?, conversation_substage = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (stage, substage, session_id))
        else:
            cursor.execute('''
                UPDATE analysis_sessions
                SET conversation_stage = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (stage, session_id))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        raise e


def increment_why_count(session_id):
    """
    增加 why 计数

    Args:
        session_id: 会话 ID

    Returns:
        bool: 是否成功
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE analysis_sessions
            SET why_count = why_count + 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (session_id,))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        raise e


def add_identified_cause(session_id, cause):
    """
    添加识别的原因

    Args:
        session_id: 会话 ID
        cause: 识别的原因

    Returns:
        bool: 是否成功
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 读取现有的 causes
    cursor.execute('SELECT identified_causes FROM analysis_sessions WHERE id = ?', (session_id,))
    row = cursor.fetchone()

    try:
        if row and row[0]:
            causes = json.loads(row[0])
        else:
            causes = []

        causes.append(cause)

        cursor.execute('''
            UPDATE analysis_sessions
            SET identified_causes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (json.dumps(causes), session_id))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        raise e


def update_session(session_id, summary=None, root_causes=None,
                   action_plan=None, status=None):
    """
    更新分析会话

    Args:
        session_id: 会话 ID
        summary: 分析总结（可选）
        root_causes: 根本原因分析（字典），会转为 JSON 存储（可选）
        action_plan: 行动计划（字典），会转为 JSON 存储（可选）
        status: 状态 ('active' | 'resolved' | 'on_hold')（可选）

    Returns:
        bool: 是否成功
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    updates = []
    values = []

    if summary is not None:
        updates.append("summary = ?")
        values.append(summary)
    if root_causes is not None:
        updates.append("root_causes = ?")
        values.append(json.dumps(root_causes))
    if action_plan is not None:
        updates.append("action_plan = ?")
        values.append(json.dumps(action_plan))
    if status is not None:
        updates.append("status = ?")
        values.append(status)
        if status == 'resolved':
            updates.append("resolved_at = CURRENT_TIMESTAMP")

    if not updates:
        conn.close()
        return False

    values.append(session_id)
    query = f"UPDATE analysis_sessions SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"

    try:
        cursor.execute(query, values)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        raise e


def archive_session(session_id):
    """
    归档会话

    Args:
        session_id: 会话 ID

    Returns:
        bool: 是否成功
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE analysis_sessions
            SET session_type = 'archived',
                status = CASE WHEN status = 'active' THEN 'resolved' ELSE status END,
                updated_at = CURRENT_TIMESTAMP,
                resolved_at = CASE WHEN resolved_at IS NULL AND status = 'active'
                                  THEN CURRENT_TIMESTAMP ELSE resolved_at END
            WHERE id = ?
        ''', (session_id,))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        raise e


def get_session(session_id):
    """
    获取单个会话

    Args:
        session_id: 会话 ID

    Returns:
        dict: 会话信息
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, session_type, trigger_source, trigger_reason, focus_area,
               related_target_id, related_status_id, summary, issues_identified,
               root_causes, action_plan, status, created_at, updated_at, resolved_at
        FROM analysis_sessions WHERE id = ?
    ''', (session_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        columns = ['id', 'session_type', 'trigger_source', 'trigger_reason', 'focus_area',
                   'related_target_id', 'related_status_id', 'summary', 'issues_identified',
                   'root_causes', 'action_plan', 'status', 'created_at', 'updated_at', 'resolved_at']
        result = dict(zip(columns, row))

        # 解析 JSON 字段
        if result['issues_identified']:
            result['issues_identified'] = json.loads(result['issues_identified'])
        if result['root_causes']:
            result['root_causes'] = json.loads(result['root_causes'])
        if result['action_plan']:
            result['action_plan'] = json.loads(result['action_plan'])

        return result
    return None


def get_sessions(status=None, limit=None):
    """
    获取会话列表

    Args:
        status: 过滤状态（可选）
        limit: 返回数量限制（可选）

    Returns:
        list: 会话列表
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = '''
        SELECT id, session_type, trigger_source, trigger_reason, focus_area,
               related_target_id, related_status_id, summary, status, created_at
        FROM analysis_sessions
    '''

    params = []
    if status:
        query += " WHERE status = ?"
        params.append(status)

    query += " ORDER BY created_at DESC"

    if limit:
        query += " LIMIT ?"
        params.append(limit)

    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)

    columns = ['id', 'session_type', 'trigger_source', 'trigger_reason', 'focus_area',
               'related_target_id', 'related_status_id', 'summary', 'status', 'created_at']
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))

    conn.close()
    return results


def get_active_sessions():
    """
    获取所有活跃会话

    Returns:
        list: 活跃会话列表
    """
    return get_sessions(status='active')


def get_archived_sessions(limit=10):
    """
    获取已归档会话

    Args:
        limit: 返回数量限制

    Returns:
        list: 已归档会话列表
    """
    return get_sessions(status='resolved', limit=limit)


def add_message(session_id, role, content, message_type=None):
    """
    添加消息到会话

    Args:
        session_id: 会话 ID
        role: 角色 ('user' | 'assistant')
        content: 消息内容
        message_type: 消息类型（可选）

    Returns:
        int: 消息 ID
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO analysis_messages
            (session_id, role, content, message_type)
            VALUES (?, ?, ?, ?)
        ''', (session_id, role, content, message_type))

        conn.commit()
        message_id = cursor.lastrowid
        conn.close()
        return message_id
    except Exception as e:
        conn.close()
        raise e


def get_messages(session_id, limit=None):
    """
    获取会话的消息列表

    Args:
        session_id: 会话 ID
        limit: 返回数量限制（可选）

    Returns:
        list: 消息列表
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = '''
        SELECT id, role, content, message_type, created_at
        FROM analysis_messages
        WHERE session_id = ?
        ORDER BY created_at ASC
    '''

    params = [session_id]

    if limit:
        query += " LIMIT ?"
        params.append(limit)

    cursor.execute(query, params)

    columns = ['id', 'role', 'content', 'message_type', 'created_at']
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))

    conn.close()
    return results


def format_session_summary(session):
    """
    格式化会话摘要

    Args:
        session: 会话字典

    Returns:
        str: 格式化的摘要
    """
    lines = []
    lines.append(f"会话 ID: {session['id']}")
    lines.append(f"触发来源: {session['trigger_source']}")
    lines.append(f"触发原因: {session['trigger_reason']}")
    lines.append(f"关注区域: {session['focus_area']}")
    lines.append(f"状态: {session['status']}")
    lines.append(f"创建时间: {session['created_at']}")

    if session['related_target_id']:
        lines.append(f"关联 Target: ID {session['related_target_id']}")
    if session['related_status_id']:
        lines.append(f"关联 Status: ID {session['related_status_id']}")

    if session['summary']:
        lines.append(f"\n总结: {session['summary']}")

    return "\n".join(lines)


if __name__ == "__main__":
    # 测试：创建会话
    session_id = create_session(
        trigger_source='manual',
        trigger_reason='用户主动发起分析',
        focus_area='both',
        issues_identified={'target_issues': [], 'status_issues': []}
    )
    print(f"Created session {session_id}")

    # 测试：添加消息
    msg_id = add_message(
        session_id,
        role='assistant',
        content='你好，我来帮你分析一下目标执行情况。',
        message_type='question'
    )
    print(f"Added message {msg_id}")

    # 测试：获取会话
    session = get_session(session_id)
    print(f"\nSession summary:")
    print(format_session_summary(session))

    # 测试：获取消息
    messages = get_messages(session_id)
    print(f"\nMessages:")
    for msg in messages:
        print(f"  [{msg['role']}] {msg['content']}")
