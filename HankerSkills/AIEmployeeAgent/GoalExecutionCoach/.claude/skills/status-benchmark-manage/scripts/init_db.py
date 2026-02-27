#!/usr/bin/env python3
"""
初始化状态达标线管理数据库
创建 SQLite 数据库表结构并预装预设的 status benchmarks
"""

import sqlite3
import os
from datetime import datetime

# 获取数据库路径（支持直接调用和exec调用）
if '__file__' in dir():
    DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'status_benchmarks.db')
else:
    DB_PATH = os.path.join(os.getcwd(), 'data', 'status_benchmarks.db')


def init_database():
    """初始化数据库，创建 status_benchmarks 表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS status_benchmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            target_value REAL NOT NULL,
            unit TEXT,
            period TEXT NOT NULL CHECK(period IN ('daily', 'weekly')),
            comparison_type TEXT NOT NULL CHECK(comparison_type IN ('>=', '<=')),
            current_value REAL DEFAULT 0,
            is_met BOOLEAN DEFAULT 0,
            calculation_script TEXT NOT NULL,
            source_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_calculated_at TIMESTAMP
        )
    ''')

    # 创建历史记录表，用于追踪每次更新的达标情况
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS benchmark_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            benchmark_id INTEGER NOT NULL,
            current_value REAL NOT NULL,
            is_met BOOLEAN NOT NULL,
            period_start TIMESTAMP NOT NULL,
            period_end TIMESTAMP NOT NULL,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (benchmark_id) REFERENCES status_benchmarks(id)
        )
    ''')

    # 创建索引以加快查询
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_history_benchmark_id
        ON benchmark_history(benchmark_id)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_history_recorded_at
        ON benchmark_history(recorded_at DESC)
    ''')

    conn.commit()

    # 检查是否已有数据，如果没有则插入预设的 benchmarks
    cursor.execute('SELECT COUNT(*) FROM status_benchmarks')
    count = cursor.fetchone()[0]

    if count == 0:
        # 预设的 status benchmarks
        preset_benchmarks = [
            ("每日工作时间", 5.0, "小时", "daily", ">=", "fetch_data/fetch_feishu_data.py",
             "https://my.feishu.cn/base/AUagbEJ3ZadyjwsfjAPcD991nGg?table=tblFXOx2aYXcDLLw&view=vewjPhzV7h"),
            ("每周工作时间", 35.0, "小时", "weekly", ">=", "fetch_data/fetch_feishu_data.py",
             "https://my.feishu.cn/base/AUagbEJ3ZadyjwsfjAPcD991nGg?table=tblFXOx2aYXcDLLw&view=vewjPhzV7h"),
            ("每日创作时间", 4.0, "小时", "daily", ">=", "fetch_data/fetch_feishu_data.py",
             "https://my.feishu.cn/base/AUagbEJ3ZadyjwsfjAPcD991nGg?table=tblFXOx2aYXcDLLw&view=vewjPhzV7h"),
            ("每周创作时间", 25.0, "小时", "weekly", ">=", "fetch_data/fetch_feishu_data.py",
             "https://my.feishu.cn/base/AUagbEJ3ZadyjwsfjAPcD991nGg?table=tblFXOx2aYXcDLLw&view=vewjPhzV7h"),
            ("每日娱乐+放松时间", 1.0, "小时", "daily", "<=", "fetch_data/fetch_feishu_data.py",
             "https://my.feishu.cn/base/AUagbEJ3ZadyjwsfjAPcD991nGg?table=tblFXOx2aYXcDLLw&view=vewjPhzV7h"),
            ("每日运动时间", 0.5, "小时", "daily", ">=", "fetch_data/fetch_feishu_data.py",
             "https://my.feishu.cn/base/AUagbEJ3ZadyjwsfjAPcD991nGg?table=tblFXOx2aYXcDLLw&view=vewjPhzV7h"),
            ("每周运动时间", 5.0, "小时", "weekly", ">=", "fetch_data/fetch_feishu_data.py",
             "https://my.feishu.cn/base/AUagbEJ3ZadyjwsfjAPcD991nGg?table=tblFXOx2aYXcDLLw&view=vewjPhzV7h"),
        ]

        for benchmark in preset_benchmarks:
            cursor.execute('''
                INSERT INTO status_benchmarks
                (name, target_value, unit, period, comparison_type,
                 calculation_script, source_url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', benchmark)

        conn.commit()
        print(f"Initialized {len(preset_benchmarks)} preset benchmarks.")

    conn.close()
    print(f"Database initialized at: {DB_PATH}")


if __name__ == "__main__":
    init_database()
