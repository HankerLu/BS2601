#!/usr/bin/env python3
"""
合并日报 JSON 可视化查看器（PyQt5）
默认加载同目录下的 work_daily_report_merged_by_day.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QTextEdit,
    QMainWindow,
    QMessageBox,
    QFileDialog,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)


DEFAULT_JSON = Path(__file__).resolve().parent / "work_daily_report_merged_by_day.json"


class WorkDailyMergedViewer(QMainWindow):
    def __init__(self, json_path: Path | None = None):
        super().__init__()
        self.setWindowTitle("合并日报查看器")
        self.resize(980, 720)

        self._json_path = Path(json_path) if json_path else DEFAULT_JSON
        self._data: dict | None = None

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        top = QHBoxLayout()
        self.path_label = QLabel()
        self.path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        top.addWidget(QLabel("当前文件："), 0)
        top.addWidget(self.path_label, 1)

        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("筛选日期（例：2026-04）")
        self.filter_edit.textChanged.connect(self._apply_filter)
        top.addWidget(QLabel("筛选："), 0)
        top.addWidget(self.filter_edit, 0)

        layout.addLayout(top)

        splitter = QSplitter(Qt.Horizontal)
        self.day_list = QListWidget()
        self.day_list.currentRowChanged.connect(self._on_day_selected)
        splitter.addWidget(self.day_list)

        right = QWidget()
        rv = QVBoxLayout(right)
        self.day_header = QLabel()
        self.day_header.setWordWrap(True)
        self.day_header.setTextInteractionFlags(Qt.TextSelectableByMouse)
        font = self.day_header.font()
        font.setPointSize(font.pointSize() + 1)
        font.setBold(True)
        self.day_header.setFont(font)
        rv.addWidget(self.day_header)

        self.body = QTextEdit()
        self.body.setReadOnly(True)
        self.body.setLineWrapMode(QTextEdit.WidgetWidth)
        self.body.setPlaceholderText("在左侧选择日期后，此处平铺展示当日所有分点内容。")
        rv.addWidget(self.body)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([220, 740])
        layout.addWidget(splitter)

        self.setStatusBar(QStatusBar())

        menubar = self.menuBar()
        file_menu = menubar.addMenu("文件")
        open_act = QAction("打开 JSON…", self)
        open_act.triggered.connect(self._open_file)
        file_menu.addAction(open_act)
        reload_act = QAction("重新加载", self)
        reload_act.triggered.connect(self.reload)
        file_menu.addAction(reload_act)

        self._load_from_disk()
        self._populate_day_list()

    def _load_from_disk(self) -> None:
        path = self._json_path
        if not path.is_file():
            self._data = None
            self.path_label.setText(str(path))
            self.statusBar().showMessage("文件不存在，请「文件 → 打开 JSON」")
            return
        try:
            text = path.read_text(encoding="utf-8")
            self._data = json.loads(text)
        except (OSError, json.JSONDecodeError) as e:
            self._data = None
            QMessageBox.warning(self, "读取失败", str(e))
            self.statusBar().showMessage("加载失败")
            return
        self.path_label.setText(str(path.resolve()))
        gen = (self._data or {}).get("generated_at", "")
        days = len((self._data or {}).get("days") or [])
        self.statusBar().showMessage(f"已加载 {days} 天 · generated_at: {gen}")

    def reload(self) -> None:
        row = self.day_list.currentRow()
        self._load_from_disk()
        self._populate_day_list()
        if 0 <= row < self.day_list.count():
            self.day_list.setCurrentRow(row)

    def _open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择合并日报 JSON",
            str(self._json_path.parent),
            "JSON (*.json);;所有文件 (*)",
        )
        if path:
            self._json_path = Path(path)
            self.reload()

    def _all_days_sorted(self) -> list[dict]:
        if not self._data:
            return []
        days = self._data.get("days") or []
        return sorted(days, key=lambda d: d.get("date") or "", reverse=True)

    def _populate_day_list(self) -> None:
        self.day_list.clear()
        self.body.clear()
        self.day_header.clear()
        if not self._data:
            return
        needle = self.filter_edit.text().strip()
        for d in self._all_days_sorted():
            date_str = d.get("date") or ""
            if needle and needle not in date_str:
                continue
            mins = d.get("work_minutes", 0)
            hours = d.get("work_hours_approx", 0)
            label = f"{date_str}  ·  {mins} 分钟（约 {hours} h）"
            QListWidgetItem(label, self.day_list)
        if self.day_list.count() > 0:
            self.day_list.setCurrentRow(0)

    def _apply_filter(self) -> None:
        self._populate_day_list()

    @staticmethod
    def _format_day_flat(day: dict) -> str:
        """将当日 merged_items 展平为纯文本分点（无需树形展开）。"""
        lines: list[str] = []
        n = 0
        for item in day.get("merged_items") or []:
            n += 1
            theme = item.get("theme") or "（无主题）"
            tm = item.get("total_minutes", "")
            head = f"{n}. 【{theme}】　{tm} 分钟"
            lines.append(head)

            kps = [str(p).strip() for p in (item.get("key_points") or []) if str(p).strip()]
            summ = (item.get("summary") or "").strip()

            if kps:
                for p in kps:
                    lines.append(f"　　· {p}")
            elif summ:
                lines.append(f"　　· {summ}")
            else:
                lines.append("　　· （本条无要点摘要）")

            cnt = item.get("source_item_count")
            if cnt is not None and int(cnt) > 1:
                lines.append(f"　　（合并自 {cnt} 条原始记录）")

            lines.append("")

        return "\n".join(lines).rstrip()

    def _on_day_selected(self, row: int) -> None:
        if row < 0 or not self._data:
            self.day_header.clear()
            self.body.clear()
            return
        needle = self.filter_edit.text().strip()
        days = [
            d
            for d in self._all_days_sorted()
            if (not needle or needle in (d.get("date") or ""))
        ]
        if row >= len(days):
            return
        day = days[row]
        date_str = day.get("date") or ""
        wmin = day.get("work_minutes", 0)
        wh = day.get("work_hours_approx", 0)
        self.day_header.setText(f"{date_str}  ·  工作 {wmin} 分钟（约 {wh} 小时）")
        self.body.setPlainText(self._format_day_flat(day))


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    app = QApplication(sys.argv)
    win = WorkDailyMergedViewer(json_path=path)
    win.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
