"""本技能目录解析：所有数据文件须落在 SKILL_ROOT 之下（独立可执行包）。"""

from __future__ import annotations

from pathlib import Path


def skill_root() -> Path:
    """work-daily-narrate/（scripts 的父目录）。"""
    return Path(__file__).resolve().parent.parent


def default_work_daily_report_path() -> Path:
    return skill_root() / "data" / "work_daily_report.json"


def default_narrated_out_dir() -> Path:
    return skill_root() / "data" / "work_daily_narrated"


def resolve_under_skill(rel_or_abs: Path) -> Path:
    """
    将 rel_or_abs 解析为绝对路径，且必须位于 skill_root() 之下。
    若为相对路径，则相对于 skill_root() 解析。
    """
    root = skill_root()
    p = (rel_or_abs if rel_or_abs.is_absolute() else root / rel_or_abs).resolve()
    try:
        p.relative_to(root.resolve())
    except ValueError as e:
        raise ValueError(
            f"路径必须在本技能目录内: {root}\n"
            f"拒绝: {p}"
        ) from e
    return p
