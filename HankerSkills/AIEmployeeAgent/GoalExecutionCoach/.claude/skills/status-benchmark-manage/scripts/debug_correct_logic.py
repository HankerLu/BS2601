#!/usr/bin/env python3
"""调试脚本：按正确的分类逻辑重新统计本周数据"""

import os
import sys
from datetime import datetime, timedelta

# 添加 scripts 目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from fetch_data.fetch_feishu_data import fetch_feishu_records

# 获取本周的所有记录
period_start = datetime(2026, 2, 23, 0, 0, 0)
period_end = datetime(2026, 3, 1, 23, 59, 59)

print(f'查询时间范围: {period_start.strftime("%Y-%m-%d %H:%M")} 至 {period_end.strftime("%Y-%m-%d %H:%M")}')
print()

records = fetch_feishu_records(period_start, period_end)
print(f'获取到 {len(records)} 条记录')
print()

# 按正确的逻辑统计
total_work_time = 0.0
creation_time = 0.0
other_work_time = 0.0

print('=== 工作(👩‍💻 工作) 相关记录详情 ===')
for i, record in enumerate(records):
    fields = record.get('fields', {})
    primary_category = fields.get('一级分类', '')
    secondary_category = fields.get('二级分类', '')

    # 处理分类字段（可能是列表）
    if isinstance(primary_category, list) and len(primary_category) > 0:
        primary_category = primary_category[0].get('text', '') if isinstance(primary_category[0], dict) else str(primary_category[0])
    if isinstance(secondary_category, list) and len(secondary_category) > 0:
        secondary_category = secondary_category[0].get('text', '') if isinstance(secondary_category[0], dict) else str(secondary_category[0])

    # 检查是否是工作分类
    if primary_category == '👩‍💻 工作':
        start_time = fields.get('开始时间', 0)
        duration = fields.get('任务时长（小时）', 0) or fields.get('时长', 0) or fields.get('Duration', 0) or fields.get('小时', 0)

        if start_time:
            record_date = datetime.fromtimestamp(start_time / 1000)
            try:
                duration = float(duration)
                total_work_time += duration

                if secondary_category == '👑 创作':
                    creation_time += duration
                    type_label = '创作'
                elif secondary_category == '💼 其他工作':
                    other_work_time += duration
                    type_label = '其他工作'
                else:
                    type_label = '未知'

                print(f'{i+1}. {record_date.strftime("%m-%d %H:%M")} | {secondary_category} | {duration}h')
            except (ValueError, TypeError):
                pass

print()
print(f'=== 统计结果 ===')
print(f'工作时间总计 (一级分类=👩‍💻 工作): {total_work_time} 小时')
print(f'  其中创作时间 (二级分类=👑 创作): {creation_time} 小时')
print(f'  其中其他工作 (二级分类=💼 其他工作): {other_work_time} 小时')
print(f'  创作时间占比: {creation_time/total_work_time*100:.1f}%' if total_work_time > 0 else '  创作时间占比: N/A')
