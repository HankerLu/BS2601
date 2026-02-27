---
name: status-benchmark-manage
description: 管理实时状态达标线（Status Benchmark），计算和同步达标情况。支持添加、修改、删除状态指标，自动计算当前值并判定达标状态。当用户提到"状态"、"达标"、"工作时间"、"娱乐时间"等实时指标时使用。
---

# 状态达标线管理 (Status Benchmark Manager)

你是一个帮助用户管理和跟踪实时状态达标线（Status Benchmark）的教练。

## 什么是 Status Benchmark？

实时状态达标线定义了在一个特定周期（每日/每周）下需要达到的指标及格线。

**示例**：
- 每日工作时间 >= 5小时
- 每周创作时间 >= 25小时
- 每日娱乐+放松时间 <= 1小时

与 Target Benchmark（长期目标）不同，Status Benchmark 关注的是日常习惯的持续达标情况。

## 路径约定

所有脚本路径均**相对于本 SKILL 根目录**（即本文件 `SKILL.md` 所在目录，通常为工作区中的 `status-benchmark-manage` 目录）。执行前请先确定该目录路径并设为 `SKILL_ROOT`，再拼接 `scripts/` 下的脚本名使用。

## 工作流程

### 1. 初始化数据库

首次使用时，确保数据库已初始化（会自动预装预设的status benchmarks）：
```bash
# 将 SKILL_ROOT 替换为 SKILL.md 所在目录的实际路径
python "${SKILL_ROOT}/scripts/init_db.py"
```

或在 Python 中：
```python
import os
SKILL_ROOT = os.path.join(os.getcwd(), "status-benchmark-manage")  # 从项目根运行时；否则改为 SKILL.md 所在目录
exec(open(os.path.join(SKILL_ROOT, "scripts", "init_db.py")).read())
init_database()
```

初始化后会自动创建以下预设 benchmarks：
- 每日工作时间 >= 5小时
- 每周工作时间 >= 35小时
- 每日创作时间 >= 4小时
- 每周创作时间 >= 25小时
- 每日娱乐+放松时间 <= 1小时
- 每日运动时间 >= 0.5小时
- 每周运动时间 >= 5小时

### 2. 添加新的 Status Benchmark

收集以下信息：
- **名称**：清晰的描述（如"每日阅读时间"）
- **目标值**：具体的数字（如1）
- **单位**：计量单位（如小时、次）
- **周期**：daily（每日）或 weekly（每周）
- **比较类型**：>=（大于等于）或 <=（小于等于）
- **计算脚本**：计算当前值的脚本路径（相对于 `scripts/` 目录）
- **数据源**：可选，原始数据来源说明

调用脚本添加：
```python
import os
SKILL_ROOT = os.path.join(os.getcwd(), "status-benchmark-manage")
exec(open(os.path.join(SKILL_ROOT, "scripts", "manage_benchmarks.py")).read())
add_benchmark(
    name="每日阅读时间",
    target_value=1.0,
    unit="小时",
    period="daily",
    comparison_type=">=",
    calculation_script="fetch_data/fetch_custom_data.py"
)
```

### 3. 更新 Status Benchmark 的当前值

当被指定更新具体 benchmark 的当前值时，会自动调用对应的计算脚本：

```python
import os
SKILL_ROOT = os.path.join(os.getcwd(), "status-benchmark-manage")
exec(open(os.path.join(SKILL_ROOT, "scripts", "calculate_values.py")).read())
update_all_benchmarks()  # 更新所有benchmarks
# 或
update_single_benchmark(benchmark_id=1)  # 更新单个benchmark
```

### 4. 修改/删除 Status Benchmark

- 修改 benchmark：
```python
import os
SKILL_ROOT = os.path.join(os.getcwd(), "status-benchmark-manage")
exec(open(os.path.join(SKILL_ROOT, "scripts", "manage_benchmarks.py")).read())
update_benchmark(1, target_value=6.0, comparison_type=">=")
```

- 删除 benchmark：
```python
import os
SKILL_ROOT = os.path.join(os.getcwd(), "status-benchmark-manage")
exec(open(os.path.join(SKILL_ROOT, "scripts", "manage_benchmarks.py")).read())
delete_benchmark(1)
```

### 5. 查看达标报告

生成文本格式的达标报告：
```python
import os
SKILL_ROOT = os.path.join(os.getcwd(), "status-benchmark-manage")
exec(open(os.path.join(SKILL_ROOT, "scripts", "calculate_values.py")).read())
print(generate_report())
```

## 输出格式

达标报告采用简洁的文本格式：

```
============================================================
📊 状态达标线报告
============================================================

📌 每日工作时间 (daily)
   目标值: >= 5.0 小时
   当前值: 6.5 小时
   达标状态: ✅ 已达标

📌 每周创作时间 (weekly)
   目标值: >= 25.0 小时
   当前值: 18.5 小时
   达标状态: ❌ 未达标 (差距 6.5小时)

============================================================
```

## 计算脚本规范

计算脚本位于 `scripts/fetch_data/` 目录下，需要导出 `calculate_current_value()` 函数：

```python
def calculate_current_value(period_start, period_end):
    """
    计算当前值

    Args:
        period_start: 周期开始时间 (datetime对象)
        period_end: 周期结束时间 (datetime对象)

    Returns:
        float: 计算得到的当前值
    """
    # 从数据源获取数据并计算
    # 例如从飞书表格获取时间日志
    return calculated_value
```

示例：`scripts/fetch_data/fetch_feishu_data.py` 提供了从飞书表格获取时间数据的实现。

## 用户交互提示

根据用户表述判断操作类型：

- "添加状态指标"、"新增状态线" → 添加新 benchmark
- "更新状态"、"计算当前值" → 更新 benchmark 当前值
- "查看达标情况"、"我的状态" → 生成报告
- "修改状态线"、"改一下" → 更新 benchmark 信息
- "删除状态线"、"不要了" → 删除 benchmark

## CLI 命令行接口

本 skill 提供 CLI 接口，支持命令行方式操作。适用于定时任务、自动化脚本或手动调试。

### 使用方式

```bash
python .claude/skills/status-benchmark-manage/scripts/cli.py <command> [options]
```

### 可用命令

#### 1. update - 更新 benchmarks

```bash
# 更新所有 benchmarks
python scripts/cli.py update --period all --output-report

# 只更新 daily benchmarks
python scripts/cli.py update --period daily --output-report

# 只更新 weekly benchmarks
python scripts/cli.py update --period weekly --output-report

# 更新指定 ID 的 benchmark
python scripts/cli.py update --id 1
```

#### 2. report - 生成报告

```bash
# 生成所有 benchmarks 的报告
python scripts/cli.py report
```

#### 3. check-stale - 检查未更新的 benchmarks

```bash
# 检查 daily benchmarks 是否超过 12 小时未更新
python scripts/cli.py check-stale --period daily --max-age-hours 12

# 检查 weekly benchmarks 是否超过 24 小时未更新
python scripts/cli.py check-stale --period weekly --max-age-hours 24
```

### OpenClaw 定时任务集成

在 OpenClaw 的 `jobs.json` 中配置定时任务：

```json
{
  "id": "daily-update-status",
  "name": "每日更新 Status Benchmarks",
  "schedule": {
    "kind": "cron",
    "expr": "0 23 * * *",
    "tz": "Asia/Shanghai"
  },
  "payload": {
    "kind": "agentTurn",
    "message": "请更新所有 daily period 的 status benchmarks 并生成报告"
  },
  "sessionTarget": "isolated",
  "enabled": true
}
```

## 注意事项

1. **路径**：`SKILL_ROOT` 为本 SKILL 根目录（即 `SKILL.md` 所在目录）。若当前工作目录为项目根，可设为 `os.path.join(os.getcwd(), 'status-benchmark-manage')`；若已在 skill 目录内，可设为 `os.getcwd()`。
2. 每次更新当前值后，会自动判断是否达标并更新达标状态
3. 达标判断基于比较类型：>= 表示当前值需大于等于目标值，<= 表示当前值需小于等于目标值
4. 未达标时会计算与目标的差距
5. 计算脚本需要正确处理 period_start 和 period_end 参数
6. 数据源主要是飞书多维表格，包含从2026年以来的 time log
