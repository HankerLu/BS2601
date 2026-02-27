---
name: cycle-update-remind
description: 周期性更新提醒和自动化任务管理，通过 Openclaw 定时调用 status 和 target benchmark 的 CLI 接口，实现自动更新和提醒功能。
---

# 周期更新提醒 (Cycle Update Remind)

这是一个自动化调度技能，通过 Openclaw 定时触发任务，自动更新状态达标线和目标进度，并定期发送提醒和简报。

## 工作原理

本技能本身不包含业务逻辑，而是通过调用 `status-benchmark-manage` 和 `target-benchmark-manage` 的 CLI 接口来实现自动化：

```
Openclaw 定时触发
    ↓
执行 CLI 命令
    ↓
status-benchmark-manage/cli.py 或 target-benchmark-manage/cli.py
    ↓
更新数据库 / 生成报告 / 发送通知
```

## 定时任务

| 时间 | 任务 | 说明 | 命令 |
|------|------|------|------|
| 10:00 | 每日更新提醒 | 检查即将到期的目标 | `cli.py check-near-deadline --days 30` |
| 14:00 | 每日更新检查 | 检查 daily benchmarks 是否已更新 | `cli.py check-stale --period daily` |
| 23:00 | 每日自动更新 | 更新所有 daily status benchmarks | `cli.py update --period daily --output-report` |
| 23:00 (周日) | 每周自动更新 | 更新所有 weekly status benchmarks | `cli.py update --period weekly --output-report` |
| 09:00 (每3天) | 状态简报 | 生成所有 benchmarks 的状态简报 | `cli.py report` |

## 安装配置

### 1. 安装 Openclaw

确保 Openclaw 已安装并配置：

```bash
# 检查 Openclaw 是否可用
openclaw --version
```

### 2. 使用 Crontab 格式配置

```bash
# 导入定时任务到系统 crontab（或 Openclaw 的调度系统）
openclaw import openclaw_crontab.conf

# 或直接编辑 crontab
crontab -e
# 将 openclaw_crontab.conf 的内容复制进去
```

### 3. 使用 YAML 格式配置

如果 Openclaw 支持 YAML 配置：

```bash
# 导入配置
openclaw load openclaw_config.yaml
```

### 4. 配置通知（可选）

如果需要通过飞书发送通知，设置环境变量：

```bash
export FEISHU_WEBHOOK_URL="your_webhook_url_here"
```

## CLI 接口说明

### Status Benchmark Manager CLI

```bash
# 更新所有 benchmarks
python .claude/skills/status-benchmark-manage/cli.py update --period all --output-report

# 只更新 daily benchmarks
python .claude/skills/status-benchmark-manage/cli.py update --period daily --output-report

# 只更新 weekly benchmarks
python .claude/skills/status-benchmark-manage/cli.py update --period weekly --output-report

# 生成报告
python .claude/skills/status-benchmark-manage/cli.py report

# 检查未更新的 benchmarks
python .claude/skills/status-benchmark-manage/cli.py check-stale --period daily --max-age-hours 12
```

### Target Benchmark Manager CLI

```bash
# 生成所有目标的报告
python .claude/skills/target-benchmark-manage/cli.py report

# 检查即将到期的目标
python .claude/skills/target-benchmark-manage/cli.py check-near-deadline --days 7

# 列出所有目标
python .claude/skills/target-benchmark-manage/cli.py list

# 更新目标当前值
python .claude/skills/target-benchmark-manage/cli.py update --id 1 --value 75.5
```

## 项目结构

```
cycle-update-remind/
├── SKILL.md                        # 本文档
├── openclaw_crontab.conf           # Crontab 格式配置
└── openclaw_config.yaml            # YAML 格式配置
```

## 调试和日志

所有定时任务的日志输出到 `/tmp/cycle_reminder.log`：

```bash
# 查看最新日志
tail -f /tmp/cycle_reminder.log

# 查看错误日志
grep ERROR /tmp/cycle_reminder.log
```

## 手动触发任务

如果需要手动执行某个任务：

```bash
# 手动更新 daily benchmarks
python .claude/skills/status-benchmark-manage/cli.py update --period daily --output-report

# 手动发送状态简报
python .claude/skills/status-benchmark-manage/cli.py report

# 手动检查目标截止日期
python .claude/skills/target-benchmark-manage/cli.py check-near-deadline --days 7
```

## 注意事项

1. **工作目录**：定时任务执行时需要确保在项目根目录下，否则 CLI 命令找不到正确的数据库路径
2. **时区设置**：确保 Openclaw 使用正确的时区（默认 Asia/Shanghai）
3. **Python 路径**：确保 Python 命令指向正确的 Python 环境
4. **环境变量**：飞书通知等依赖环境变量的功能需要正确配置

## 相关技能

- **status-benchmark-manage**: 管理实时状态达标线
- **target-benchmark-manage**: 管理长期量化目标
