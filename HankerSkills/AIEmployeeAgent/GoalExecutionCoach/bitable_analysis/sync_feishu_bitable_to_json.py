#!/usr/bin/env python3
"""
独立脚本：将飞书多维表格（Bitable）全量记录导出为本地 JSON。

依赖同目录下的 fetch_feishu_data.py（鉴权、分页）；凭证放在同目录 .env（参考 .env.example）。
仅读取飞书，不修改云端数据。

用法（在 bitable_analysis 目录）:
  python3 sync_feishu_bitable_to_json.py
  python3 sync_feishu_bitable_to_json.py -o ./feishu_bitable_export.json
  python3 sync_feishu_bitable_to_json.py --no-pretty

首次使用：复制 .env.example 为 .env 并填写飞书凭证。
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# 与 sync 脚本同目录，保证从项目任意位置调用时仍能导入
_SYNC_DIR = Path(__file__).resolve().parent
if str(_SYNC_DIR) not in sys.path:
    sys.path.insert(0, str(_SYNC_DIR))

from fetch_feishu_data import (
    FEISHU_APP_TOKEN,
    FEISHU_TABLE_ID,
    FEISHU_VIEW_ID,
    fetch_feishu_records,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export full Feishu Bitable to local JSON (read-only)."
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "feishu_bitable_export.json",
        help="Output JSON path (default: feishu_bitable_export.json in this folder)",
    )
    parser.add_argument(
        "--no-pretty",
        action="store_true",
        help="Write compact JSON (no indent)",
    )
    args = parser.parse_args()

    try:
        # 不传周期 => 全部分页拉取；仅在客户端按视图分页，无日期过滤
        records = fetch_feishu_records(None, None)
    except Exception as e:
        print(f"拉取失败: {e}", file=sys.stderr)
        return 1

    payload = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "app_token": FEISHU_APP_TOKEN,
            "table_id": FEISHU_TABLE_ID,
            "view_id": FEISHU_VIEW_ID or None,
        },
        "record_count": len(records),
        "records": records,
    }

    out = args.output.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    indent = None if args.no_pretty else 2
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=indent)

    print(f"已写入 {len(records)} 条记录 -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
