#!/usr/bin/env python3
"""
校验「合并梳理日报」JSON 并写入本技能 data/work_daily_narrated/{date}.json

本技能为独立包：默认输出目录在技能目录内，不写入仓库其他路径。

用法（任意 cwd）:
  python save_narrated_report.py narrated.json
  cat narrated.json | python save_narrated_report.py -
  python save_narrated_report.py narrated.json --out-dir data/work_daily_narrated

--out-dir 须为相对于本技能根目录的路径，且解析后仍在技能包内。
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _paths import default_narrated_out_dir, resolve_under_skill, skill_root as _skill_root

REQUIRED_TOP_SINGLE = ("schema_version", "date", "work_minutes", "bullets")


def _validate_single(obj: dict[str, Any]) -> None:
    for k in REQUIRED_TOP_SINGLE:
        if k not in obj:
            raise ValueError(f"缺少必填字段: {k}")
    if obj["schema_version"] != "1":
        raise ValueError("schema_version 必须为 1")
    bullets = obj["bullets"]
    if not isinstance(bullets, list) or len(bullets) == 0:
        raise ValueError("bullets 必须为非空数组")
    for i, b in enumerate(bullets):
        if isinstance(b, dict):
            if "text" not in b or "index" not in b:
                raise ValueError(f"bullets[{i}] 需含 index 与 text")
        elif isinstance(b, str):
            continue
        else:
            raise ValueError(f"bullets[{i}] 须为字符串或 {{index,text}} 对象")


def _normalize_bullets(bullets: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, b in enumerate(bullets):
        if isinstance(b, str):
            out.append({"index": i + 1, "text": b})
        else:
            out.append({"index": int(b["index"]), "text": str(b["text"])})
    return out


def _ensure_narrated_at(obj: dict[str, Any]) -> None:
    if not obj.get("narrated_at"):
        obj["narrated_at"] = datetime.now(timezone.utc).isoformat()


def main() -> int:
    ap = argparse.ArgumentParser(description="保存合并梳理后的工作日报 JSON（仅写入本技能 data/）")
    ap.add_argument(
        "input",
        help="JSON 文件路径，或 - 表示从 stdin 读取（内容仍为 JSON 文本）",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        help="相对于本技能根目录的输出目录，默认 data/work_daily_narrated",
    )
    args = ap.parse_args()

    if args.input == "-":
        raw = sys.stdin.read()
    else:
        p = Path(args.input).resolve()
        if not p.is_file():
            print(f"文件不存在: {p}", file=sys.stderr)
            return 1
        try:
            p.relative_to(_skill_root().resolve())
        except ValueError:
            print(
                "输入 JSON 文件须位于本技能目录内；请先把文件移入 work-daily-narrate/ 下再指定路径，或使用 stdin（-）。",
                file=sys.stderr,
            )
            return 1
        raw = p.read_text(encoding="utf-8")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"JSON 解析失败: {e}", file=sys.stderr)
        return 1

    try:
        if args.out_dir is None:
            out_root = default_narrated_out_dir()
        else:
            out_root = resolve_under_skill(args.out_dir)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1

    out_root.mkdir(parents=True, exist_ok=True)

    if isinstance(data, dict) and "reports" in data:
        reports = data["reports"]
        if not isinstance(reports, list):
            print("reports 须为数组", file=sys.stderr)
            return 1
        for i, rep in enumerate(reports):
            if not isinstance(rep, dict):
                print(f"reports[{i}] 须为对象", file=sys.stderr)
                return 1
            try:
                _validate_single(rep)
            except ValueError as e:
                print(f"reports[{i}]: {e}", file=sys.stderr)
                return 1
            _ensure_narrated_at(rep)
            rep["bullets"] = _normalize_bullets(rep["bullets"])
            outp = out_root / f"{rep['date']}.json"
            with open(outp, "w", encoding="utf-8") as f:
                json.dump(rep, f, ensure_ascii=False, indent=2)
            print(f"已写入 {outp}")
        return 0

    if not isinstance(data, dict):
        print("根节点须为 JSON 对象或含 reports 数组的包装对象", file=sys.stderr)
        return 1

    try:
        _validate_single(data)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1

    _ensure_narrated_at(data)
    data["bullets"] = _normalize_bullets(data["bullets"])
    outp = out_root / f"{data['date']}.json"
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"已写入 {outp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
