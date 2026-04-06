---
name: work-daily-narrate
description: 自包含技能包：包内从飞书导出聚合为 work_daily_report，再经模型合并梳理为 Markdown + data/work_daily_narrated/{date}.json。当用户提到工作日报、日报合并、日报梳理、work_daily_report、合并化梳理、日报 JSON 时使用。
---

# 工作日报合并梳理 (Work Daily Narrate)

本目录 **`work-daily-narrate/`** 作为**可独立拷贝/执行的环境**：**数据与脚本均在包内**（`data/`、`scripts/`），不依赖仓库里其它目录下的 Python 脚本；路径校验要求文件落在 `{SKILL_ROOT}` 下。

把 `data/work_daily_report.json` 里**按条罗列**的工作记录交给大模型做**主题合并与叙事整理**，输出 Markdown（编号要点 + 当日时长）及 **JSON 归档**。**汇总时长以输入 JSON 为准**；合并要点由模型完成。

**仓库内目标路径：** `GoalExecutionCoach/.cursor/skills/work-daily-narrate/`（不使用 `.claude/skills/`）。

## 目录约定（`{SKILL_ROOT}` = 本技能根目录）

| 路径 | 用途 |
|------|------|
| `{SKILL_ROOT}/data/feishu_bitable_export.json` | **可选输入**：飞书多维表格全量导出（由你任用意方式拉取后**复制进包内**此文件名） |
| `{SKILL_ROOT}/data/work_daily_report.json` | **中间/输入**：由包内 `build_work_daily_report.py` 从上图生成，或直接手写/粘贴后符合结构亦可 |
| `{SKILL_ROOT}/data/work_daily_narrated/{YYYY-MM-DD}.json` | **输出**：模型合并梳理后的日报 JSON |
| `{SKILL_ROOT}/scripts/` | 见下「与 Python 的分工」 |

## 推荐工作流

### 0. （可选）在包内生成 `work_daily_report.json`

若你已有飞书 Bitable 的导出 JSON，复制为：

```text
{SKILL_ROOT}/data/feishu_bitable_export.json
```

在本技能内执行（路径相对技能根，且必须在包内）：

```bash
python "{SKILL_ROOT}/scripts/build_work_daily_report.py"
```

会读取 `data/feishu_bitable_export.json`，写出 `data/work_daily_report.json`（筛选「👩‍💻 工作」、按日+三级分类汇总分钟）。**不调用** `bitable_analysis` 或其它仓库脚本。

若你已在别处生成好 `work_daily_report.json`，也可**仅复制**到本包 `data/work_daily_report.json`，跳过本步。

### 1. 抽取供模型使用的「原始日块」

```bash
python "{SKILL_ROOT}/scripts/prepare_day_for_llm.py" --date 2026-04-06
python "{SKILL_ROOT}/scripts/prepare_day_for_llm.py" --last 3
```

```bash
python "{SKILL_ROOT}/scripts/prepare_day_for_llm.py" --json data/work_daily_report.json --date 2026-04-06
```

### 2. 模型执行「合并化梳理」

根据打印文本或 `work_daily_report.json` 中某日的 `days[]`，按下文原则生成 Markdown + 规范 JSON。

### 3. 保存梳理结果 JSON

```bash
python "{SKILL_ROOT}/scripts/save_narrated_report.py" - < narrated.json
python "{SKILL_ROOT}/scripts/save_narrated_report.py" ./single_day.json
```

默认写入 `data/work_daily_narrated/{date}.json`。`--out-dir` 须相对技能根且仍在包内。

---

## 合并原则（必须遵守）

1. **时长**  
   - **直接使用输入中的「工作时长」**（分钟与小时），写进日报标题区；不要自行把明细再加总替代报表（若发现明细与合计明显不一致，可在日报末尾用一句话说明「与分项加总略有差异，以系统汇总为准」）。

2. **合并**  
   - 将**同一主题、同一项目线**的多条合并为**一条编号要点**（例如多条「SolidWorks / 装配体」合并为一条「SolidWorks 装配体学习与练习」）。  
   - **保留**关键专名：项目代号（如 RB003、SS001）、产品名、人名、公司等。  
   - **删减**纯过程口头禅式重复（如多次「上厕所PK」可并入一条「间歇休息」或不单独成条，视信息量而定）。  
   - 要点数量建议 **3～10 条/日**；信息极少的可少于 3 条。

3. **表述**  
   - 每条以**动词或主题**开头，**简洁**，避免把原始长文整段粘贴；必要时用分号连接子动作。  
   - **编号**必须是 `1.` `2.` `3.` …（阿拉伯数字 + 英文句点 + 空格）。

4. **禁止**  
   - 不要捏造未出现在原始条目中的事实；不确定则笼统概括（��读行业资讯」）而非虚构标题。

---

## 输出格式（面向用户）

```markdown
## 工作日报 · {YYYY-MM-DD}

- **工作时长：** {X} 分钟（约 {Y} 小时）

### 今日工作要点

1. …
2. …
3. …
```

多日则按日期**各写一节**（从新到旧或用户指定顺序）。

---

## JSON 输出规范（与 Markdown 同步）

每条合并梳理结果除 Markdown 外，须能序列化为下列结构（**`schema_version` 固定为 `"1"`**）。

### 单日对象（写入 `data/work_daily_narrated/{date}.json`）

| 字段 | 类型 | 说明 |
|------|------|------|
| `schema_version` | string | 固定 `"1"` |
| `date` | string | `YYYY-MM-DD` |
| `work_minutes` | number | 与源 `work_daily_report` 当日 **任务时长（分钟）_日合计** 一致 |
| `work_hours_approx` | number | 与源报表 **任务时长（小时）_日合计** 一致（通常两位小数） |
| `bullets` | array | 合并后的要点：每项为 `{ "index": 1, "text": "..." }` 或纯字符串（保存脚本会规范化） |
| `narrated_at` | string | ISO8601；若省略，`save_narrated_report.py` 会自动补 UTC 时间 |
| `source` | object | 可选。建议含 `report_file`（如 `work_daily_report.json`）、`report_generated_at` |
| `markdown_body` | string | 可选。与该日 Markdown 全文一致，便于复核 |

### 多日包装（可选）

顶层含 `reports: [ {...}, ... ]`；交给 `save_narrated_report.py` 会拆成多个 `data/work_daily_narrated/{date}.json`。

---

## 与 Python 的分工（均在 `{SKILL_ROOT}/scripts/`，无包外脚本依赖）

| 能力 | 脚本 |
|------|------|
| 飞书导出 JSON → `work_daily_report.json`（聚合规则与原先 bitable 工具一致） | `build_work_daily_report.py` |
| 抽取单日/多日文本给模型 | `prepare_day_for_llm.py` |
| 分钟/小时**汇总** | 写在 `work_daily_report.json` 中，模型**引用即可** |
| **合并、归类、重写为 1.2.3.** | **本 Skill（模型）** |
| 梳理结果 **JSON 校验与落盘** | `save_narrated_report.py` |
| 路径解析与「须在包内」校验 | `_paths.py` |

**说明：** 从飞书拉取全量导出（网络、凭证）可在包外用任意工具完成；只需把得到的 `feishu_bitable_export.json` **复制进** `data/`，后续步骤全部由本包脚本处理。

---

## 触发关键词（供路由）

工作日报、日报合并、日报梳理、合并化梳理、`work_daily_report`、飞书工作记录整理、把今天的多条记录合成要点、编号要点日报、日报 JSON。
