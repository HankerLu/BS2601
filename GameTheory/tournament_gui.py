import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QTextEdit, 
                             QProgressBar, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QSplitter, QSpinBox, QMessageBox, QStyleFactory)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QColor, QFont

# 导入后端逻辑
try:
    from tournament_runner import TournamentRunner
except ImportError:
    # 简单的 mock，防止IDE中没有文件报错
    class TournamentRunner:
        def __init__(self, **kwargs): pass
        def run_tournament(self, rounds): pass

class TournamentWorker(QThread):
    sig_log = pyqtSignal(str)
    sig_progress = pyqtSignal(int, int) # current_match, total_matches
    sig_stats_update = pyqtSignal(dict) # 发送最新的 stats 字典
    sig_finished = pyqtSignal()

    def __init__(self, rounds_per_match=20):
        super().__init__()
        self.rounds_per_match = rounds_per_match
        self.runner = None

    def run(self):
        # 实例化 runner，并注入回调
        self.runner = TournamentRunner(
            log_callback=self.on_log,
            progress_callback=self.on_progress
        )
        
        # 劫持 runner 的 stats 更新
        # 这里的 trick 是我们每次 match 结束后手动触发 UI 更新
        # 但 runner.run_tournament 是阻塞的，所以我们在 runner 内部每次 match 完会调 progress
        # 我们利用 progress 回调来更新 stats
        
        self.runner.run_tournament(self.rounds_per_match)
        self.sig_finished.emit()

    def on_log(self, msg):
        self.sig_log.emit(msg)

    def on_progress(self, current, total):
        self.sig_progress.emit(current, total)
        # 每次进度更新，说明一场比赛结束，发送最新的统计数据
        # 将 defaultdict 转换为普通 dict 发送，防止线程问题
        stats_dict = {}
        for k, v in self.runner.stats.items():
            stats_dict[k] = dict(v)
        self.sig_stats_update.emit(stats_dict)

    def stop(self):
        if self.runner:
            self.runner.stop()

class TournamentWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("黑暗森林 · 循环赛控制台 (The Dark Forest Tournament)")
        self.resize(1200, 800)
        self.init_ui()
        self.worker = None

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # 1. 标题栏
        title_label = QLabel("🌲 黑暗森林生存实验 - 循环赛控制台")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; margin: 10px;")
        layout.addWidget(title_label)

        # 2. 主体分割 (左边排行榜，右边控制台)
        splitter = QSplitter(Qt.Horizontal)
        
        # --- 左侧: 实时排行榜 ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(QLabel("🏆 实时生存积分榜"))
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["排名", "选手", "总得分", "胜/平/负", "背叛率", "被坑/背刺"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        left_layout.addWidget(self.table)
        
        splitter.addWidget(left_widget)

        # --- 右侧: 日志与控制 ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 进度区
        self.match_progress = QProgressBar()
        self.match_progress.setFormat("等待开始... %p%")
        right_layout.addWidget(QLabel("📅 赛程进度"))
        right_layout.addWidget(self.match_progress)
        
        # 日志区
        right_layout.addWidget(QLabel("📝 实时战报日志"))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-family: monospace;")
        right_layout.addWidget(self.log_text)
        
        # 控制区
        ctrl_group = QWidget()
        ctrl_layout = QHBoxLayout(ctrl_group)
        
        ctrl_layout.addWidget(QLabel("每场轮数:"))
        self.rounds_spin = QSpinBox()
        self.rounds_spin.setRange(1, 100)
        self.rounds_spin.setValue(20)
        ctrl_layout.addWidget(self.rounds_spin)
        
        self.btn_start = QPushButton("🚀 启动循环赛")
        self.btn_start.setMinimumHeight(40)
        self.btn_start.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; font-size: 14px;")
        self.btn_start.clicked.connect(self.start_tournament)
        ctrl_layout.addWidget(self.btn_start)
        
        self.btn_stop = QPushButton("🛑 终止")
        self.btn_stop.setMinimumHeight(40)
        self.btn_stop.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold;")
        self.btn_stop.clicked.connect(self.stop_tournament)
        self.btn_stop.setEnabled(False)
        ctrl_layout.addWidget(self.btn_stop)
        
        right_layout.addWidget(ctrl_group)
        
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 3) # 左侧占比 3
        splitter.setStretchFactor(1, 2) # 右侧占比 2
        
        layout.addWidget(splitter)

    def log(self, msg):
        self.log_text.append(msg)
        sb = self.log_text.verticalScrollBar()
        sb.setValue(sb.maximum())

    def start_tournament(self):
        rounds = self.rounds_spin.value()
        self.log(f"--- 系统就绪，准备启动 {rounds} 轮循环赛 ---")
        
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.rounds_spin.setEnabled(False)
        self.table.setRowCount(0)
        self.log_text.clear()
        
        self.worker = TournamentWorker(rounds)
        self.worker.sig_log.connect(self.log)
        self.worker.sig_progress.connect(self.update_progress)
        self.worker.sig_stats_update.connect(self.update_table)
        self.worker.sig_finished.connect(self.on_finished)
        self.worker.start()

    def stop_tournament(self):
        if self.worker:
            self.log("⚠️ 正在请求终止比赛...")
            self.worker.stop()
            self.btn_stop.setEnabled(False)

    def on_finished(self):
        self.log("🏁 循环赛进程已结束。请查看生成的 Markdown 报告。")
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.rounds_spin.setEnabled(True)
        self.match_progress.setFormat("已完成")
        QMessageBox.information(self, "完成", "循环赛已结束！\n战报已生成至 api_logs 目录下 (带时间戳)")

    def update_progress(self, current, total):
        self.match_progress.setMaximum(total)
        self.match_progress.setValue(current)
        self.match_progress.setFormat(f"正在进行: 比赛 {current}/{total} (%p%)")

    def update_table(self, stats_data):
        """更新排行榜表格"""
        # 将字典转为列表并排序
        # stats_data 结构: {'nice': {'total_score': 10, ...}, ...}
        
        # 需要映射 key 到 name，这里简单硬编码或从 backend 获取
        # 为了简单，直接用 key 显示，或者简单映射
        name_map = {
            "nice": "Nice (老好人)",
            "tit_for_tat": "Tit-for-Tat (执法者)",
            "opportunist": "Opportunist (机会主义者)",
            "absolutist": "Absolutist (独裁者)",
            "machiavellian": "Machiavellian (权谋家)"
        }

        row_list = []
        for key, data in stats_data.items():
            name = name_map.get(key, key)
            row_list.append((key, name, data))
            
        # 按总分降序排序
        row_list.sort(key=lambda x: x[2].get('total_score', 0), reverse=True)
        
        self.table.setRowCount(len(row_list))
        for r, (key, name, d) in enumerate(row_list):
            # 排名
            self.table.setItem(r, 0, QTableWidgetItem(str(r + 1)))
            
            # 选手
            self.table.setItem(r, 1, QTableWidgetItem(name))
            
            # 总得分 (加粗)
            score_item = QTableWidgetItem(str(d.get('total_score', 0)))
            score_item.setFont(QFont("Arial", 10, QFont.Bold))
            score_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 2, score_item)
            
            # 胜/平/负
            record = f"{d.get('wins', 0)} / {d.get('ties', 0)} / {d.get('losses', 0)}"
            self.table.setItem(r, 3, QTableWidgetItem(record))
            
            # 背叛率
            total_moves = d.get('cooperate_count', 0) + d.get('defect_count', 0)
            rate = (d.get('defect_count', 0) / total_moves * 100) if total_moves else 0
            rate_item = QTableWidgetItem(f"{rate:.1f}%")
            if rate > 50:
                rate_item.setForeground(QColor("red"))
            elif rate < 10:
                rate_item.setForeground(QColor("green"))
            self.table.setItem(r, 4, rate_item)
            
            # 被坑/背刺
            betrayal = f"{d.get('betrayal_victim_count', 0)} / {d.get('betrayal_success_count', 0)}"
            self.table.setItem(r, 5, QTableWidgetItem(betrayal))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    
    window = TournamentWindow()
    window.show()
    sys.exit(app.exec_())
