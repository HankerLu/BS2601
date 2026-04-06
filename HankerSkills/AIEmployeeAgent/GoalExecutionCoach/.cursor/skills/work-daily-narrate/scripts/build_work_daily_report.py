#!/usr/bin/env python3
"""
在本技能包内：从 data/feishu_bitable_export.json 聚合生成 data/work_daily_report.json。

逻辑与仓库 bitable_analysis 侧一致（按「👩‍💻 工作」筛、按日+三级分类汇总分钟），
但不调用任何包外脚本；飞书全量导出须先放入本包 data/feishu_bitable_export.json。

用法:
  python scripts/build_work_daily_report.py
  python scripts/build_work_daily_report.py -i data/feishu_bitable_export.json -o data/work_daily_report.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from _paths import resolve_under_skill, skill_root

WORK_PRIMARY_LABEL = "👩‍💻 工作"


def _text_field(val: Any) -> str:
    if val is None:
        return ""
    if isinstance(val, str):
        return val.strip()
    if isinstance(val, list) and len(val) > 0:
        first = val[0]
        if isinstance(first, dict):
            return str(first.get("text", "") or "").strip()
        return str(first).strip()
    return str(val).strip()


def _minutes(val: Any) -> int:
    if val is None:
        return 0
    if isinstance(val, bool):
        return 0
    if isinstance(val, (int, float)):
        return max(0, int(round(float(val))))
    s = str(val).strip()
    if not s:
        return 0
    try:
        return max(0, int(round(float(s))))
    except ValueError:
        return 0


def _date_key_from_fields(fields: dict[str, Any]) -> str | None:
    st = fields.get("开始时间")
    if st is None:
        return None
    try:
        ms = float(st)
    except (TypeError, ValueError):
        return None
    dt = datetime.fromtimestamp(ms / 1000.0)
    return dt.date().isoformat()


def _is_work_primary(fields: dict[str, Any]) -> bool:
    p = fields.get("一级分类")
    if isinstance(p, str):
        return p.strip() == WORK_PRIMARY_LABEL
    return _text_field(p) == WORK_PRIMARY_LABEL


def build_daily_report(export_path: Path, with_record_ids: bool = False) -> dict[str, Any]:
    with open(export_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    records = raw.get("records") or []
    agg: dict[str, dict[str, dict[str, Any]]] = defaultdict(
        lambda: defaultdict(lambda: {"minutes": 0, "record_ids": []})  # type: ignore[misc]
    )

    for rec in records:
        fields = rec.get("fields") or {}
        if not _is_work_primary(fields):
            continue
        day = _date_key_from_fields(fields)
        if not day:
            continue
        tertiary = _text_field(fields.get("三级分类")) or "(未填写三级分类)"
        minutes = _minutes(fields.get("任务时长（分钟）"))
        rid = rec.get("record_id") or rec.get("id") or ""
        bucket = agg[day][tertiary]
        bucket["minutes"] += minutes
        if rid:
            bucket["record_ids"].append(rid)

    days_out: list[dict[str, Any]] = []
    for day in sorted(agg.keys(), reverse=True):
        entries_src = agg[day]
        entries = []
        day_total = 0
        for label in sorted(entries_src.keys(), key=lambda k: -entries_src[k]["minutes"]):
            b = entries_src[label]
            m = int(b["minutes"])
            day_total += m
            entry: dict[str, Any] = {
                "三级分类": label,
                "任务时长（分钟）": m,
                "合并条目数": len(b["record_ids"]),
            }
            if with_record_ids:
                entry["record_ids"] = b["record_ids"]
            entries.append(entry)
        days_out.append(
            {
                "date": day,
                "任务时长（分钟）_日合计": day_total,
                "任务时长（小时）_日合计": round(day_total / 60.0, 2),
                "明细": entries,
            }
        )

    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "source_file": export_path.name,
        "source_exported_at": raw.get("exported_at"),
        "source_record_count": raw.get("record_count"),
        "filter_一级分类": WORK_PRIMARY_LABEL,
        "work_record_days": len(days_out),
        "days": days_out,
    }


def main() -> int:
    root = skill_root()
    ap = argparse.ArgumentParser(description="从包内飞书导出生成 work_daily_report.json")
    ap.add_argument(
        "-i",
        "--input",
        type=Path,
        default=Path("data/feishu_bitable_export.json"),
        help="相对于技能根的飞书导出 JSON",
    )
    ap.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("data/work_daily_report.json"),
        help="相对于技能根的输出路径",
    )
    ap.add_argument(
        "--with-record-ids",
        action="store_true",
        help="明细中保留 record_ids",
    )
    args = ap.parse_args()

    try:
        export_path = resolve_under_skill(args.input)
        out_path = resolve_under_skill(args.output)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1

    if not export_path.is_file():
        print(
            f"未找到: {export_path}\n"
            f"请先将飞书多维表格全量导出 JSON 复制到: {root / 'data' / 'feishu_bitable_export.json'}",
            file=sys.stderr,
        )
        return 1

    report = build_daily_report(export_path, with_record_ids=args.with_record_ids)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"已生成 {out_path}（{report['work_record_days']} 个有工作记录的自然日）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
