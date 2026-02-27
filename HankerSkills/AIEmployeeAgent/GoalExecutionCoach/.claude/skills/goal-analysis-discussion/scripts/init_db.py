#!/usr/bin/env python3
"""
初始化目标分析与讨论数据库
创建 SQLite 数据库表结构
"""

import sqlite3
import os

# 获取数据库路径（支持直接调用和exec调用）
if '__file__' in dir():
    DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'analyses.db')
else:
    DB_PATH = os.path.join(os.getcwd(), 'data', 'analyses.db')


def init_database():
    """初始化数据库，创建分析会话表和消息表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 创建分析会话表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_type TEXT NOT NULL CHECK(session_type IN ('active', 'archived')),
            trigger_source TEXT CHECK(trigger_source IN ('manual', 'scheduled', 'alert')),
            trigger_reason TEXT,
            focus_area TEXT CHECK(focus_area IN ('target', 'status', 'both')),
            related_target_id INTEGER,
            related_status_id INTEGER,
            summary TEXT,
            issues_identified TEXT,
            root_causes TEXT,
            action_plan TEXT,
            status TEXT DEFAULT 'active' CHECK(status IN ('active', 'resolved', 'on_hold')),
            -- 对话流程控制字段
            conversation_stage TEXT DEFAULT 'initial',
            conversation_substage TEXT,
            why_count INTEGER DEFAULT 0,
            identified_causes TEXT,
            proposed_solutions TEXT,
            confirmed_actions TEXT,
            -- 问题严重程度
            severity_level TEXT CHECK(severity_level IN ('critical', 'moderate', 'mild')),
            analysis_mode TEXT CHECK(analysis_mode IN ('deep', 'quick')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP
        )
    ''')

    # 创建分析消息表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            message_type TEXT CHECK(message_type IN ('question', 'analysis', 'suggestion', 'confirmation')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES analysis_sessions(id)
        )
    ''')

    # 创建索引
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_sessions_status
        ON analysis_sessions(status)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_sessions_created_at
        ON analysis_sessions(created_at DESC)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_messages_session_id
        ON analysis_messages(session_id)
    ''')

    conn.commit()
    conn.close()
    print(f"Database initialized at: {DB_PATH}")


if __name__ == "__main__":
    init_database()
