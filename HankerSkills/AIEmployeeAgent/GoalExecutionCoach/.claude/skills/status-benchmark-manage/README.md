# Status Benchmark Manage Skill

实时状态达标线管理技能，用于跟踪和管理日常/每周的状态达标情况。

## 功能特性

- ✅ 管理实时状态达标线（Status Benchmark）
- ✅ 自动计算当前值并判定达标状态
- ✅ 支持添加、修改、删除状态指标
- ✅ 生成清晰的达标报告
- ✅ 预装7个常用状态达标线
- ✅ 支持从飞书多维表格获取真实数据

## 预设的 Status Benchmarks

| 名称 | 目标值 | 周期 |
|------|--------|------|
| 每日工作时间 | >= 5.0 小时 | daily |
| 每周工作时间 | >= 35.0 小时 | weekly |
| 每日创作时间 | >= 4.0 小时 | daily |
| 每周创作时间 | >= 25.0 小时 | weekly |
| 每日娱乐+放松时间 | <= 1.0 小时 | daily |
| 每日运动时间 | >= 0.5 小时 | daily |
| 每周运动时间 | >= 5.0 小时 | weekly |

## 项目结构

```
status-benchmark-manage/
├── SKILL.md                    # 技能描述文档
├── data/
│   └── status_benchmarks.db    # SQLite 数据库
└── scripts/
    ├── init_db.py              # 初始化数据库脚本
    ├── manage_benchmarks.py   # Benchmark 增删改查
    ├── calculate_values.py     # 计算当前值和达标判定
    └── fetch_data/
        └── fetch_feishu_data.py # 从飞书获取数据
```

## 快速开始

### 1. 初始化数据库

首次使用需要初始化数据库（会自动预装预设的 benchmarks）：

```bash
python scripts/init_db.py
```

### 2. 更新当前值并生成报告

```bash
python scripts/calculate_values.py
```

### 3. 查看报告

运行后会生成如下格式的报告：

```
============================================================
📊 状态达标线报告
============================================================

📅 每日达标线
------------------------------------------------------------

📌 每日工作时间
   目标值: >= 5.0 小时
   当前值: 6.5 小时
   达标状态: ✅ 已达标

📌 每日娱乐+放松时间
   目标值: <= 1.0 小时
   当前值: 0.8 小时
   达标状态: ✅ 已达标
```

## 数据源配置

### 使用真实的飞书数据

#### 当前配置方式（推荐）

脚本已配置为使用飞书开放平台 OAuth 2.0 方式，通过 app_id + app_secret 自动获取访问令牌。

1. 配置 OAuth 凭证

编辑 `.env` 文件（已预配置您的凭证）：

```env
# 飞书开放平台 OAuth 2.0 凭证
FEISHU_APP_ID=cli_a92adee577389cc2
FEISHU_APP_SECRET=2I5NiKVxY4GvkBSQLMx9Rbs20rXz0Iss

# 飞书多维表格信息
FEISHU_APP_TOKEN=AUagbEJ3ZadyjwsfjAPcD991nGg
FEISHU_TABLE_ID=tblFXOx2aYXcDLLw
FEISHU_VIEW_ID=vewjPhzV7h
```

2. 数据字段映射

脚本已自动配置为使用正确的字段名：
- 类别字段：`二级分类`（包含 "💼 其他工作"、"👑 创作"、"💆 放松"、"🏋️ 健身" 等）
- 时长字段：`任务时长（小时）`
- 时间筛选：基于 `开始时间`（毫秒时间戳）

#### 其他认证方式（备选）

如果需要使用其他方式：

**方式一：使用已有的 access_token**

编辑 `.env` 文件，添加已有的 access_token：

```env
FEISHU_OAUTH_ACCESS_TOKEN=your_existing_access_token
```

**方式二：使用 COZE 方式**

编辑 `.env` 文件，添加 COZE 凭证：

```env
COZE_FEISHU_BITABLE_7605639493156274228=your_coze_token
```

#### 安全说明

- ✅ 脚本只使用 `GET` 请求，**不会修改飞书云文档**
- ✅ `.env` 文件已在 `.gitignore` 中，不会被提交到版本控制
- ✅ 所有写入操作只针对本地 SQLite 数据库
- ✅ 复用了已验证的 read_bitable.py 逻辑，确保稳定性

## API 使用示例

### 添加新的 Benchmark

```python
from scripts.manage_benchmarks import add_benchmark

add_benchmark(
    name="每日阅读时间",
    target_value=1.0,
    unit="小时",
    period="daily",
    comparison_type=">=",
    calculation_script="fetch_data/fetch_custom_data.py"
)
```

### 更新当前值

```python
from scripts.calculate_values import update_all_benchmarks

results = update_all_benchmarks()
for result in results:
    if result['success']:
        print(f"{result['name']}: {result['current_value']} {result['unit']}")
```

### 生成报告

```python
from scripts.calculate_values import generate_report

report = generate_report()
print(report)
```

## 下一步

- [x] 配置真实的飞书 API 凭证
- [x] 创建飞书多维表格的实际字段映射
- [ ] 实现定时任务自动更新（cycle_update_remind）
- [ ] 创建目标执行教练的整体调度系统
