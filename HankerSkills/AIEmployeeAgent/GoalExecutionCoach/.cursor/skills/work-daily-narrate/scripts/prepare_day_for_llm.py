#!/usr/bin/env python3
"""
从本技能 data/work_daily_report.json 抽取指定日期（或最近 N 天）的原始条目，
输出便于交给大模型做「合并化梳理」的纯文本。

本技能为独立包：输入/输出均须在「work-daily-narrate/」目录树下，不引用仓库其他路径。

用法（在任意 cwd 下均可，建议从 SKILL_ROOT 调用）:
  cd /path/to/work-daily-narrate
  python scripts/prepare_day_for_llm.py --date 2026-04-06
  python scripts/prepare_day_for_llm.py --last 3
  python scripts/prepare_day_for_llm.py --json data/work_daily_report.json --date 2026-04-06

请将聚合生成的 work_daily_report.json 复制到本目录 data/work_daily_report.json 后再运行。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _paths import default_work_daily_report_path, resolve_under_skill, skill_root


def _load(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _day_block(day: dict) -> str:
    lines = [
        f"【日期】{day['date']}",
        f"【工作时长】{day.get('任务时长（分钟）_日合计', 0)} 分钟（约 {day.get('任务时长（小时）_日合计', 0)} 小时，以报表为准）",
        "【当日原始条目（三级分类 + 单条分钟数，按报表顺序）】",
    ]
    for i, item in enumerate(day.get("明细") or [], 1):
        title = item.get("三级分类", "").replace("\n", " ").strip()
        mins = item.get("任务时长（分钟）", 0)
        lines.append(f"  {i}. ({mins} 分钟) {title}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="从本技能 data/ 抽取 work_daily_report 供 LLM 合并梳理")
    ap.add_argument(
        "--json",
        type=Path,
        dest="json_path",
        help="相对本技能根目录的路径，如 data/work_daily_report.json（须位于技能包内）",
    )
    ap.add_argument("--date", help="指定 YYYY-MM-DD")
    ap.add_argument("--last", type=int, metavar="N", help="最近 N 个有记录的自然日（按报表从新到旧）")
    args = ap.parse_args()

    try:
        if args.json_path is None:
            path = default_work_daily_report_path()
        else:
            path = resolve_under_skill(args.json_path)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1

    if not path.is_file():
        root = skill_root()
        print(
            f"未找到输入文件: {path}\n"
            f"请将 work_daily_report.json 放到: {root / 'data' / 'work_daily_report.json'}",
            file=sys.stderr,
        )
        return 1

    data = _load(path)
    days: list[dict] = data.get("days") or []

    if args.date:
        picked = [d for d in days if d.get("date") == args.date]
        if not picked:
            print(f"未找到日期: {args.date}", file=sys.stderr)
            return 1
        blocks = [_day_block(picked[0])]
    elif args.last is not None:
        if args.last < 1:
            print("--last 须 >= 1", file=sys.stderr)
            return 1
        blocks = [_day_block(d) for d in days[: args.last]]
    else:
        print("请指定 --date YYYY-MM-DD 或 --last N", file=sys.stderr)
        return 1

    try:
        rel = path.relative_to(skill_root().resolve())
    except ValueError:
        rel = path.name

    header = (
        f"技能根目录: {skill_root()}\n"
        f"数据源（包内）: {rel}\n"
        f"报表生成时间: {data.get('generated_at', '')}\n"
        f"筛选条件（一级分类）: {data.get('filter_一级分类', '')}\n"
        "---\n"
    )
    print(header + "\n\n".join(blocks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
