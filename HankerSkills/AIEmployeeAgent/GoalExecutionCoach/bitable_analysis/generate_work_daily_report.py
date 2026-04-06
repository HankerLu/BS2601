#!/usr/bin/env python3
"""
工作日报 JSON 生成器

1. 默认先运行 sync_feishu_bitable_to_json.py，将 feishu_bitable_export.json 拉到最新
2. 筛选一级分类为「工作」的记录（与表中一致：👩‍💻 工作）
3. 按日历天聚合：同一天内相同「三级分类」合并，累加「任务时长（分钟）」
4. 输出新的日报结构 JSON

用法:
  python3 generate_work_daily_report.py
  python3 generate_work_daily_report.py --skip-sync
  python3 generate_work_daily_report.py -i feishu_bitable_export.json -o work_daily_report.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_EXPORT = SCRIPT_DIR / "feishu_bitable_export.json"
DEFAULT_OUT = SCRIPT_DIR / "work_daily_report.json"
SYNC_SCRIPT = SCRIPT_DIR / "sync_feishu_bitable_to_json.py"

# 与 feishu_bitable_export 中「一级分类」文案一致
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
    # 兼容若以后变为富文本列表
    return _text_field(p) == WORK_PRIMARY_LABEL


def run_export_sync(export_path: Path) -> None:
    if not SYNC_SCRIPT.is_file():
        print(f"未找到同步脚本: {SYNC_SCRIPT}", file=sys.stderr)
        sys.exit(1)
    proc = subprocess.run(
        [sys.executable, str(SYNC_SCRIPT), "-o", str(export_path)],
        cwd=str(SCRIPT_DIR),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        print(proc.stderr or proc.stdout or "sync 失败", file=sys.stderr)
        sys.exit(proc.returncode)
    if proc.stdout:
        print(proc.stdout.strip())


def build_daily_report(export_path: Path, with_record_ids: bool = False) -> dict[str, Any]:
    with open(export_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    records = raw.get("records") or []
    # day -> tertiary label -> { minutes, record_ids }
    agg: dict[str, dict[str, dict[str, Any]]] = defaultdict(
        lambda: defaultdict(
            lambda: {"minutes": 0, "record_ids": []}  # type: ignore[misc]
        )
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
            entry = {
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
        "source_file": str(export_path.name),
        "source_exported_at": raw.get("exported_at"),
        "source_record_count": raw.get("record_count"),
        "filter_一级分类": WORK_PRIMARY_LABEL,
        "work_record_days": len(days_out),
        "days": days_out,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="生成工作日报 JSON（先同步飞书导出再聚合）")
    ap.add_argument(
        "-i",
        "--input",
        type=Path,
        default=DEFAULT_EXPORT,
        help="飞书导出 JSON（默认 feishu_bitable_export.json）",
    )
    ap.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUT,
        help="输出日报 JSON（默认 work_daily_report.json）",
    )
    ap.add_argument(
        "--skip-sync",
        action="store_true",
        help="不执行 sync，直接使用现有导出文件",
    )
    ap.add_argument(
        "--with-record-ids",
        action="store_true",
        help="在「明细」中保留飞书记录 id（默认省略以减小体积）",
    )
    args = ap.parse_args()

    export_path = args.input.resolve()
    out_path = args.output.resolve()

    if not args.skip_sync:
        run_export_sync(export_path)

    if not export_path.is_file():
        print(f"找不到导出文件: {export_path}", file=sys.stderr)
        return 1

    report = build_daily_report(export_path, with_record_ids=args.with_record_ids)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    total_days = len(report["days"])
    print(f"已生成工作日报: {out_path}（共 {total_days} 个有工作记录的自然日）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
