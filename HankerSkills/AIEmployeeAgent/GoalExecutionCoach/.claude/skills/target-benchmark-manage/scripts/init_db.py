#!/usr/bin/env python3
"""
初始化目标管理数据库
创建 SQLite 数据库表结构
"""

import sqlite3
import os
from datetime import datetime

# 获取数据库路径（支持直接调用和exec调用）
if '__file__' in dir():
    DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'targets.db')
else:
    DB_PATH = os.path.join(os.getcwd(), 'data', 'targets.db')


def init_database():
    """初始化数据库，创建目标表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            target_value REAL NOT NULL,
            unit TEXT,
            deadline DATE NOT NULL,
            current_value REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print(f"Database initialized at: {DB_PATH}")


if __name__ == "__main__":
    init_database()
