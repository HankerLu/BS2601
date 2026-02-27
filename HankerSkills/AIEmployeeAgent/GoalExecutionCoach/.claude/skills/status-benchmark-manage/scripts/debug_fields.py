#!/usr/bin/env python3
"""调试脚本：查看飞书表格的字段结构和分类"""

import os
import sys
from datetime import datetime, timedelta

# 添加 scripts 目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from fetch_data.fetch_feishu_data import fetch_feishu_records

# 获取本周的所有记录
period_start = datetime(2026, 2, 23, 0, 0, 0)
period_end = datetime(2026, 3, 1, 23, 59, 59)

records = fetch_feishu_records(period_start, period_end)
print(f'获取到 {len(records)} 条记录')
print()

# 查看前5条记录的所有字段
print('=== 前5条记录的字段结构 ===')
for i, record in enumerate(records[:5]):
    fields = record.get('fields', {})
    print(f'\n记录 {i+1}:')
    for key, value in fields.items():
        # 显示字段的键和值
        if isinstance(value, list):
            if len(value) > 0:
                if isinstance(value[0], dict):
                    # 列表中的字典格式
                    print(f'  {key}: {[v.get("text", v) for v in value[:3]]}{"..." if len(value) > 3 else ""}')
                else:
                    print(f'  {key}: {value[:3]}{"..." if len(value) > 3 else ""}')
            else:
                print(f'  {key}: []')
        else:
            print(f'  {key}: {value}')

# 统计所有出现的分类值
print('\n=== 统计所有分类相关的字段值 ===')

# 收集所有可能的分类字段
all_categories = set()
all_secondary_categories = set()

for record in records:
    fields = record.get('fields', {})

    # 检查各种可能的分类字段
    for key in ['二级分类', '三级分类', '类别', 'Category', '分类']:
        value = fields.get(key, '')
        if value:
            # 处理列表格式
            if isinstance(value, list):
                for v in value:
                    if isinstance(v, dict):
                        all_categories.add(v.get('text', str(v)))
                    else:
                        all_categories.add(str(v))
            else:
                all_categories.add(str(value))

# 按字段分组统计
for key in ['二级分类', '三级分类', '类别', 'Category', '分类']:
    values = set()
    for record in records:
        value = record.get('fields', {}).get(key, '')
        if value:
            if isinstance(value, list):
                for v in value:
                    if isinstance(v, dict):
                        values.add(v.get('text', str(v)))
                    else:
                        values.add(str(v))
            else:
                values.add(str(value))

    if values:
        print(f'\n"{key}" 字段包含的值:')
        for v in sorted(values):
            print(f'  - {v}')
