#!/usr/bin/env python3
"""
从飞书多维表格导出的 JSON 中，按自然周汇总「工作时间」小时数。

工作时间定义：一级分类为「👩‍💻 工作」的记录，累加「任务时长（小时）」。
周归属：以「开始时间」（毫秒时间戳）所在周的 ISO 周（周一为一周起始）为准；
若无「开始时间」，则用「日期」（Excel 序列日）换算为日期后同样取 ISO 周。

默认按 UTC+8 解释时间（中国常用；可用 --utc-offset 覆盖）。
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

WORK_PRIMARY = "👩‍💻 工作"
FIELD_PRIMARY = "一级分类"
FIELD_HOURS = "任务时长（小时）"
FIELD_START_MS = "开始时间"
FIELD_DATE_SERIAL = "日期"

# 与 Excel / 飞书导出常见的序列日一致：1899-12-30 为第 0 天
_EXCEL_EPOCH = datetime(1899, 12, 30)


def _fixed_offset_tz(offset_hours: float) -> timezone:
    return timezone(timedelta(hours=offset_hours))


def _serial_to_datetime(serial: float, tz: timezone) -> datetime:
    dt_naive = _EXCEL_EPOCH + timedelta(days=float(serial))
    return dt_naive.replace(tzinfo=tz)


def _record_week_key(
    fields: dict,
    tz: timezone,
) -> tuple[int, int] | None:
    """返回 (ISO 年, ISO 周序号)，无法解析则 None。"""
    start = fields.get(FIELD_START_MS)
    if isinstance(start, (int, float)):
        dt = datetime.fromtimestamp(float(start) / 1000.0, tz=tz)
        y, w, _ = dt.isocalendar()
        return (y, w)

    serial = fields.get(FIELD_DATE_SERIAL)
    if isinstance(serial, (int, float)):
        dt = _serial_to_datetime(float(serial), tz)
        y, w, _ = dt.isocalendar()
        return (y, w)

    return None


def _parse_hours(fields: dict) -> float | None:
    v = fields.get(FIELD_HOURS)
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v.strip())
        except ValueError:
            return None
    return None


def compute_weekly_work_hours(
    records: list[dict],
    tz: timezone,
) -> dict[tuple[int, int], float]:
    totals: dict[tuple[int, int], float] = defaultdict(float)
    for rec in records:
        fields = rec.get("fields") or {}
        if fields.get(FIELD_PRIMARY) != WORK_PRIMARY:
            continue
        wk = _record_week_key(fields, tz)
        if wk is None:
            continue
        hrs = _parse_hours(fields)
        if hrs is None:
            continue
        totals[wk] += hrs
    return dict(totals)


def main() -> int:
    parser = argparse.ArgumentParser(description="按周汇总「👩‍💻 工作」时长（小时）")
    parser.add_argument(
        "json_path",
        nargs="?",
        default=str(Path(__file__).resolve().parent / "feishu_bitable_export.json"),
        help="feishu_bitable_export.json 路径（默认：与本脚本同目录）",
    )
    parser.add_argument(
        "--utc-offset",
        type=float,
        default=8.0,
        metavar="HOURS",
        help="相对 UTC 的小时偏移，用于解释时间戳与 Excel 序列日（默认：8，即中国东八区）",
    )
    parser.add_argument(
        "--json-out",
        metavar="FILE",
        help="将周汇总结果写入 JSON 文件（可选）",
    )
    args = parser.parse_args()

    path = Path(args.json_path)
    if not path.is_file():
        print(f"找不到文件: {path}", file=sys.stderr)
        return 1

    tz = _fixed_offset_tz(args.utc_offset)

    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    records = data.get("records") or []
    totals = compute_weekly_work_hours(records, tz)

    # 按 (年, 周) 排序输出
    for (year, week) in sorted(totals.keys()):
        hours = totals[(year, week)]
        print(f"{year}-W{week:02d}\t{hours:.4f}")

    if args.json_out:
        out_path = Path(args.json_out)
        payload = {
            "utc_offset_hours": args.utc_offset,
            "definition": {
                "primary_category": WORK_PRIMARY,
                "hours_field": FIELD_HOURS,
            },
            "weeks": [
                {"iso_year": y, "iso_week": w, "work_hours": round(totals[(y, w)], 6)}
                for (y, w) in sorted(totals.keys())
            ],
        }
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n已写入: {out_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
