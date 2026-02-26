# Cycle Update Remind Skill PRD

## 概述
负责管理 status benchmark 的周期性提醒和自动更新，根据 benchmark 的周期类型（daily/weekly）执行不同的更新和提醒策略。

## 功能需求

### 1. Target Benchmark 定时汇报提醒及进度更新
**触发时机**：每天上午 10:00
**功能**：
- 提醒用户更新 target benchmark 的进度
- 适用于所有周期的 target benchmarks（daily 和 weekly）
- 通知渠道：飞书消息或其他通知方式

### 2. Status Benchmark 定时自动化计算和达标判定

#### 2.1 Daily Benchmarks 自动更新
**触发时机**：每天晚上 23:00
**功能**：
- 自动调用 `status-benchmark-manage` skill 更新所有 `period = 'daily'` 的 status benchmarks
- 生成达标报告并发送给用户
- 更新的 benchmarks 包括：
  - 每日工作时间 >= 5小时
  - 每日创作时间 >= 4小时
  - 每日娱乐+放松时间 <= 1小时
  - 每日运动时间 >= 0.5小时

#### 2.2 Weekly Benchmarks 自动更新
**触发时机**：每周日 23:00
**功能**：
- 自动调用 `status-benchmark-manage` skill 更新所有 `period = 'weekly'` 的 status benchmarks
- 生成达标报告并发送给用户
- 更新的 benchmarks 包括：
  - 每周工作时间 >= 35 小时
  - 每周创作时间 >= 25 小时
  - 每周运动时间 >= 5小时

### 3. 数据更新检查
**触发时机**：每天下午 14:00
**功能**：
- 检查当日 daily benchmarks 的 `last_calculated_at` 时间
- 如果当天 23:00 前未更新数据，发送催促提醒
- 提醒内容包括：哪些 daily benchmarks 未更新

### 4. 定期状态简报
**触发时机**：每三天
**功能**：
- 汇总所有 status benchmarks（daily + weekly）的当前状态
- 生成简报发送给用户
- 简报内容应包括：
  - 达标的 benchmarks 数量和名称
  - 未达标的 benchmarks 和差距
  - 本周期内的总体表现评价

## 与 Status Benchmark Manage Skill 的交互

### 调用方式
通过导入 status-benchmark-manage skill 的模块来调用相关函数：

```python
from .claude.skills.status_benchmark_manage.scripts.manage_benchmarks import (
    get_all_benchmarks,
    get_benchmarks_by_period
)

from .claude.skills.status_benchmark_manage.scripts.calculate_values import (
    update_single_benchmark,
    generate_report
)
```

### 使用的函数

| 函数 | 用途 | 使用的任务 |
|------|------|------------|
| `get_benchmarks_by_period('daily')` | 获取所有 daily benchmarks | daily_update_job, followup_check_job |
| `get_benchmarks_by_period('weekly')` | 获取所有 weekly benchmarks | weekly_update_job |
| `update_single_benchmark(id)` | 更新单个 benchmark | daily_update_job, weekly_update_job |
| `generate_report()` | 生成状态报告 | 所有任务 |

## 技术实现

### 目录结构
```
.claude/skills/cycle-update-remind/
├── SKILL.md                    # Skill 描述文档
├── config.yaml                  # 定时任务配置
└── jobs/
    ├── daily_update_job.py       # 每天 23:00 更新 daily benchmarks
    ├── weekly_update_job.py      # 每周日 23:00 更新 weekly benchmarks
    ├── morning_reminder_job.py  # 每天 10:00 提醒更新数据
    ├── followup_check_job.py     # 每天 14:00 检查 daily 更新
    └── summary_report_job.py    # 每3天发送简报
```

### 配置文件示例
```yaml
jobs:
  # 每日提醒
  - name: morning_reminder
    time: "10:00"
    frequency: daily
    script: jobs/morning_reminder_job.py
    enabled: true

  # 每日检查
  - name: daily_followup
    time: "14:00"
    frequency: daily
    script: jobs/followup_check_job.py
    enabled: true

  # 每日更新 daily benchmarks
  - name: daily_update
    time: "23:00"
    frequency: daily
    script: jobs/daily_update_job.py
    enabled: true

  # 每周更新 weekly benchmarks
  - name: weekly_update
    time: "23:00"
    frequency: weekly
    day: sunday
    script: jobs/weekly_update_job.py
    enabled: true

  # 每3天简报
  - name: summary_report
    frequency: every_3_days
    script: jobs/summary_report_job.py
    enabled: true

notification:
  channel: feishu
  enabled: true
```

## 数据流

```
┌─────────────────────────────────────────────────────────────────────┐
│                      定时任务触发                              │
│                                                             │
│  ┌──────────────┬──────────────┬──────────────┐      │
│  │   10:00      │    14:00      │   23:00     │      │
│  │              │              │              │          │      │
│  │  发送提醒      │  检查更新      │  更新数据      │      │
│  │  (所有)       │  (daily)      │  (按周期)   │      │
│  └──────┬───────┴──────┬───────┴───────┘      │
│         │              │       │                  │      │
│         ▼              ▼       ▼                  │      │
│  ┌──────────────────────────────────────┐      │      │
│  │  Status Benchmark Manage Skill     │      │      │
│  │                                 │      │      │
│  │  - get_benchmarks_by_period()   │      │      │
│  │  - update_single_benchmark()    │      │      │
│  │  - generate_report()             │      │      │
│  └──────────┬───────────────────────┘      │      │
│             │                               │      │
│             ▼                               │      │
│  ┌──────────────────────────────────┐      │      │
│  │  status_benchmarks.db         │      │      │
│  └──────────────────────────────────┘      │      │
└─────────────────────────────────────────────────────┘
```

## 依赖

1. **status-benchmark-manage** skill 已部署
2. **SQLite 数据库**：`status_benchmarks.db`
3. **通知渠道**：飞书消息或系统通知
4. **Openclaw 调度器**：用于定时触发任务

## 验收标准

- [x] 每日 benchmarks 能在每天 23:00 自动更新
- [x] 每周 benchmarks 能在每周日 23:00 自动更新
- [x] 每天 10:00 发送更新提醒
- [x] 每天 14:00 检查 daily benchmarks 更新状态
- [x] 每3天生成并发送状态简报
- [x] 所有任务通过调用 status-benchmark-manage skill 完成
- [x] 配置文件支持灵活启用/禁用各个任务
