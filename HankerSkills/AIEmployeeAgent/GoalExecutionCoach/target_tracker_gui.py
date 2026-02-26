#!/usr/bin/env python3
"""
目标追踪可视化工具 - PyQt5版本
用于可视化和管理长期量化目标
"""

import sys
import sqlite3
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QProgressBar,
    QDialog, QFormLayout, QLineEdit, QDateEdit, QMessageBox,
    QHeaderView, QFrame, QDoubleSpinBox, QGroupBox, QSplitter
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor, QFont


# 数据库路径
DB_PATH = '.claude/skills/target-benchmark-manage/data/targets.db'


class TargetDatabase:
    """数据库操作类"""

    def __init__(self, db_path):
        self.db_path = db_path

    def get_all_targets(self):
        """获取所有目标"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM targets ORDER BY deadline')
        targets = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return targets

    def add_target(self, name, target_value, unit, deadline, current_value=0, starting_value=None):
        """添加新目标"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO targets (name, target_value, unit, deadline, current_value, starting_value)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, target_value, unit, deadline, current_value, starting_value))
        conn.commit()
        target_id = cursor.lastrowid
        conn.close()
        return target_id

    def update_target(self, target_id, name, target_value, unit, deadline, current_value, starting_value=None):
        """更新目标"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE targets
            SET name=?, target_value=?, unit=?, deadline=?, current_value=?, starting_value=?, updated_at=?
            WHERE id=?
        ''', (name, target_value, unit, deadline, current_value, starting_value, datetime.now(), target_id))
        conn.commit()
        conn.close()

    def update_current_value(self, target_id, current_value):
        """更新当前值"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE targets
            SET current_value=?, updated_at=?
            WHERE id=?
        ''', (current_value, datetime.now(), target_id))
        conn.commit()
        conn.close()

    def delete_target(self, target_id):
        """删除目标"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM targets WHERE id=?', (target_id,))
        conn.commit()
        conn.close()


class TargetDialog(QDialog):
    """添加/编辑目标对话框"""

    def __init__(self, parent=None, target=None):
        super().__init__(parent)
        self.target = target
        self.setWindowTitle("添加目标" if target is None else "编辑目标")
        self.setMinimumWidth(400)
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.target_value_spin = QDoubleSpinBox()
        self.target_value_spin.setRange(-999999, 999999)
        self.target_value_spin.setDecimals(2)
        self.unit_edit = QLineEdit()
        self.deadline_edit = QDateEdit()
        self.deadline_edit.setCalendarPopup(True)
        self.deadline_edit.setDate(QDate.currentDate().addMonths(3))
        self.current_value_spin = QDoubleSpinBox()
        self.current_value_spin.setRange(-999999, 999999)
        self.current_value_spin.setDecimals(2)
        self.starting_value_spin = QDoubleSpinBox()
        self.starting_value_spin.setRange(-999999, 999999)
        self.starting_value_spin.setDecimals(2)
        self.starting_value_spin.setSpecialValueText("未设置")

        if self.target:
            self.name_edit.setText(self.target['name'])
            self.target_value_spin.setValue(self.target['target_value'])
            self.unit_edit.setText(self.target['unit'] or '')
            deadline = datetime.strptime(self.target['deadline'], '%Y-%m-%d').date()
            self.deadline_edit.setDate(QDate(deadline.year, deadline.month, deadline.day))
            self.current_value_spin.setValue(self.target['current_value'])
            if self.target['starting_value'] is not None:
                self.starting_value_spin.setValue(self.target['starting_value'])
            else:
                self.starting_value_spin.setValue(-999999)

        layout.addRow("目标名称:", self.name_edit)
        layout.addRow("目标值:", self.target_value_spin)
        layout.addRow("单位:", self.unit_edit)
        layout.addRow("截止日期:", self.deadline_edit)
        layout.addRow("当前值:", self.current_value_spin)
        layout.addRow("起始值 (可选):", self.starting_value_spin)

        buttons = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addRow(buttons)

        self.setLayout(layout)

    def get_data(self):
        starting_value = self.starting_value_spin.value()
        if starting_value == -999999:
            starting_value = None

        return {
            'name': self.name_edit.text(),
            'target_value': self.target_value_spin.value(),
            'unit': self.unit_edit.text(),
            'deadline': self.deadline_edit.date().toString('yyyy-MM-dd'),
            'current_value': self.current_value_spin.value(),
            'starting_value': starting_value
        }


class UpdateValueDialog(QDialog):
    """更新当前值对话框"""

    def __init__(self, parent=None, target=None):
        super().__init__(parent)
        self.target = target
        self.setWindowTitle(f"更新: {target['name']}")
        self.setMinimumWidth(350)
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()

        # 显示当前信息
        info_label = QLabel(
            f"目标: {self.target['target_value']} {self.target['unit'] or ''}\n"
            f"起始值: {self.target.get('starting_value', '-')} {self.target['unit'] or ''}"
        )
        layout.addRow(info_label)

        self.current_value_spin = QDoubleSpinBox()
        self.current_value_spin.setRange(-999999, 999999)
        self.current_value_spin.setDecimals(2)
        self.current_value_spin.setValue(self.target['current_value'])
        layout.addRow("新的当前值:", self.current_value_spin)

        buttons = QHBoxLayout()
        ok_btn = QPushButton("更新")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addRow(buttons)

        self.setLayout(layout)

    def get_value(self):
        return self.current_value_spin.value()


class ProgressBarDelegate(QProgressBar):
    """自定义进度条"""

    def __init__(self, progress, status):
        super().__init__()
        self.progress = progress
        self.status = status
        self.setValue(min(int(progress), 100))

        # 根据进度和状态设置颜色
        if self.status == "已完成":
            self.setStyleSheet("QProgressBar::chunk { background-color: #4CAF50; }")
        elif self.status == "已过期":
            self.setStyleSheet("QProgressBar::chunk { background-color: #f44336; }")
        elif progress >= 100:
            self.setStyleSheet("QProgressBar::chunk { background-color: #4CAF50; }")
        elif progress >= 75:
            self.setStyleSheet("QProgressBar::chunk { background-color: #2196F3; }")
        elif progress >= 50:
            self.setStyleSheet("QProgressBar::chunk { background-color: #FF9800; }")
        else:
            self.setStyleSheet("QProgressBar::chunk { background-color: #FFC107; }")


class TargetTrackerApp(QMainWindow):
    """目标追踪主窗口"""

    def __init__(self):
        super().__init__()
        self.db = TargetDatabase(DB_PATH)
        self.init_ui()
        self.load_targets()

    def init_ui(self):
        self.setWindowTitle("🎯 目标追踪器")
        self.setMinimumSize(1000, 600)

        # 主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 顶部工具栏
        toolbar = QHBoxLayout()
        add_btn = QPushButton("➕ 添加目标")
        add_btn.clicked.connect(self.add_target)
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self.load_targets)
        toolbar.addWidget(add_btn)
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch()
        main_layout.addLayout(toolbar)

        # 统计信息面板
        self.stats_frame = QFrame()
        self.stats_frame.setStyleSheet("background-color: #f5f5f5; border-radius: 5px;")
        self.stats_layout = QHBoxLayout(self.stats_frame)
        self.create_stats_panel()

        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "目标名称", "起始值", "目标值", "当前值", "进度", "剩余天数", "状态", "操作"
        ])

        # 设置列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)

        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                alternate-background-color: #f9f9f9;
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)

        main_layout.addWidget(self.stats_frame)
        main_layout.addWidget(self.table)

    def create_stats_panel(self):
        """创建统计面板"""
        self.total_label = QLabel("总目标: 0")
        self.completed_label = QLabel("已完成: 0")
        self.in_progress_label = QLabel("进行中: 0")
        self.expired_label = QLabel("已过期: 0")

        for label in [self.total_label, self.completed_label, self.in_progress_label, self.expired_label]:
            label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
            self.stats_layout.addWidget(label)

    def update_stats(self, targets):
        """更新统计信息"""
        total = len(targets)
        completed = sum(1 for t in targets if t['progress'] >= 100)
        expired = sum(1 for t in targets if t['days_remaining'] < 0)
        in_progress = total - completed

        self.total_label.setText(f"总目标: {total}")
        self.completed_label.setText(f"✅ 已完成: {completed}")
        self.in_progress_label.setText(f"🔄 进行中: {in_progress}")
        self.expired_label.setText(f"⚠️ 已过期: {expired}")

    def calculate_progress(self, target_value, current_value, starting_value=None):
        """计算完成进度百分比"""
        if starting_value is not None and current_value < starting_value:
            total_to_reduce = starting_value - target_value
            if total_to_reduce == 0:
                return 100.0
            already_reduced = starting_value - current_value
            progress = (already_reduced / total_to_reduce) * 100
            return min(round(progress, 2), 100.0)
        else:
            if target_value == 0:
                return 0
            progress = (current_value / target_value) * 100
            return min(round(progress, 2), 100.0)

    def calculate_days_remaining(self, deadline):
        """计算剩余天数"""
        deadline_date = datetime.strptime(deadline, '%Y-%m-%d').date()
        today = datetime.now().date()
        delta = deadline_date - today
        return delta.days

    def get_status(self, progress, days_remaining):
        """获取状态"""
        if progress >= 100:
            return "✅ 已完成"
        elif days_remaining < 0:
            return "⚠️ 已过期"
        else:
            return "🔄 进行中"

    def load_targets(self):
        """加载目标数据"""
        targets = self.db.get_all_targets()

        self.table.setRowCount(len(targets))

        for row, target in enumerate(targets):
            # 计算进度和剩余天数
            progress = self.calculate_progress(
                target['target_value'],
                target['current_value'],
                target.get('starting_value')
            )
            days_remaining = self.calculate_days_remaining(target['deadline'])
            status = self.get_status(progress, days_remaining)
            unit = target['unit'] or ''

            # 存储计算结果用于后续使用
            target['progress'] = progress
            target['days_remaining'] = days_remaining
            target['status'] = status

            # 目标名称
            name_item = QTableWidgetItem(target['name'])
            name_item.setData(Qt.UserRole, target['id'])
            self.table.setItem(row, 0, name_item)

            # 起始值
            starting_val = str(target.get('starting_value', '-')) if target.get('starting_value') is not None else '-'
            self.table.setItem(row, 1, QTableWidgetItem(f"{starting_val} {unit}"))

            # 目标值
            self.table.setItem(row, 2, QTableWidgetItem(f"{target['target_value']} {unit}"))

            # 当前值
            current_item = QTableWidgetItem(f"{target['current_value']} {unit}")
            self.table.setItem(row, 3, current_item)

            # 进度
            progress_widget = QWidget()
            progress_layout = QVBoxLayout(progress_widget)
            progress_layout.setContentsMargins(5, 2, 5, 2)
            progress_bar = ProgressBarDelegate(progress, status)
            progress_label = QLabel(f"{progress}%")
            progress_label.setAlignment(Qt.AlignCenter)
            progress_label.setStyleSheet("font-size: 11px;")
            progress_layout.addWidget(progress_bar)
            progress_layout.addWidget(progress_label)
            self.table.setCellWidget(row, 4, progress_widget)

            # 剩余天数
            days_text = f"{days_remaining}天" if days_remaining >= 0 else f"{abs(days_remaining)}天前"
            days_item = QTableWidgetItem(days_text)
            if days_remaining < 0:
                days_item.setForeground(QColor('#f44336'))
            elif days_remaining <= 7:
                days_item.setForeground(QColor('#FF9800'))
            self.table.setItem(row, 5, days_item)

            # 状态
            status_item = QTableWidgetItem(status)
            if "已完成" in status:
                status_item.setForeground(QColor('#4CAF50'))
            elif "已过期" in status:
                status_item.setForeground(QColor('#f44336'))
            self.table.setItem(row, 6, status_item)

            # 操作按钮
            buttons_widget = QWidget()
            buttons_layout = QHBoxLayout(buttons_widget)
            buttons_layout.setContentsMargins(2, 2, 2, 2)

            update_btn = QPushButton("更新")
            update_btn.setMaximumWidth(50)
            update_btn.clicked.connect(lambda checked, t=target: self.update_current_value(t))

            edit_btn = QPushButton("编辑")
            edit_btn.setMaximumWidth(50)
            edit_btn.clicked.connect(lambda checked, t=target: self.edit_target(t))

            delete_btn = QPushButton("删除")
            delete_btn.setMaximumWidth(50)
            delete_btn.setStyleSheet("background-color: #f44336; color: white;")
            delete_btn.clicked.connect(lambda checked, t=target: self.delete_target(t))

            buttons_layout.addWidget(update_btn)
            buttons_layout.addWidget(edit_btn)
            buttons_layout.addWidget(delete_btn)
            self.table.setCellWidget(row, 7, buttons_widget)

        self.update_stats(targets)

    def add_target(self):
        """添加新目标"""
        dialog = TargetDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            self.db.add_target(
                data['name'],
                data['target_value'],
                data['unit'],
                data['deadline'],
                data['current_value'],
                data['starting_value']
            )
            self.load_targets()

    def edit_target(self, target):
        """编辑目标"""
        dialog = TargetDialog(self, target)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            self.db.update_target(
                target['id'],
                data['name'],
                data['target_value'],
                data['unit'],
                data['deadline'],
                data['current_value'],
                data['starting_value']
            )
            self.load_targets()

    def update_current_value(self, target):
        """更新当前值"""
        dialog = UpdateValueDialog(self, target)
        if dialog.exec_() == QDialog.Accepted:
            value = dialog.get_value()
            self.db.update_current_value(target['id'], value)
            self.load_targets()

    def delete_target(self, target):
        """删除目标"""
        reply = QMessageBox.question(
            self,
            '确认删除',
            f'确定要删除目标 "{target["name"]}" 吗？',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.delete_target(target['id'])
            self.load_targets()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # 设置应用样式
    app.setStyleSheet("""
        QMainWindow {
            background-color: #ffffff;
        }
        QPushButton {
            background-color: #2196F3;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #1976D2;
        }
        QPushButton:pressed {
            background-color: #0D47A1;
        }
        QLabel {
            color: #333;
        }
        QTableWidget {
            border: 1px solid #e0e0e0;
            border-radius: 5px;
        }
        QHeaderView::section {
            background-color: #f0f0f0;
            padding: 8px;
            border: none;
            border-bottom: 1px solid #e0e0e0;
            font-weight: bold;
            color: #333;
        }
    """)

    window = TargetTrackerApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
