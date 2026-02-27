#!/usr/bin/env python3
"""调试脚本：查看本周工作时间计算的详细信息"""

from datetime import datetime, timedelta
import os
import sys

# 添加 scripts 目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from fetch_data.fetch_feishu_data import fetch_feishu_records, CATEGORY_MAPPINGS

# 本周时间范围: 2026-02-23 (Monday) to 2026-03-01 (Sunday)
period_start = datetime(2026, 2, 23, 0, 0, 0)
period_end = datetime(2026, 3, 1, 23, 59, 59)

print(f'查询时间范围: {period_start.strftime("%Y-%m-%d %H:%M")} 至 {period_end.strftime("%Y-%m-%d %H:%M")}')
print()

records = fetch_feishu_records(period_start, period_end)
print(f'获取到 {len(records)} 条记录')
print()

# 统计工作类别的记录
work_categories = CATEGORY_MAPPINGS['work']

print(f'工作类别包含: {work_categories}')
print()

# 打印所有工作相关的记录详情
print('=== 工作相关记录详情 ===')
total_hours = 0
for i, record in enumerate(records):
    fields = record.get('fields', {})
    category = fields.get('二级分类', '') or fields.get('类别', '') or fields.get('Category', '')

    # 处理类别字段（可能是列表）
    if isinstance(category, list) and len(category) > 0:
        if isinstance(category[0], dict):
            category = category[0].get('text', '')
        else:
            category = str(category[0])

    if category in work_categories:
        start_time = fields.get('开始时间', 0)
        if start_time:
            record_date = datetime.fromtimestamp(start_time / 1000)
            duration = fields.get('任务时长（小时）', 0) or fields.get('时长', 0) or fields.get('Duration', 0) or fields.get('小时', 0)
            try:
                duration = float(duration)
                total_hours += duration
                print(f'{i+1}. 日期: {record_date.strftime("%Y-%m-%d %H:%M")}, 类别: {category}, 时长: {duration}小时')
            except (ValueError, TypeError):
                pass

print()
print(f'=== 总计: {total_hours} 小时 ===')
