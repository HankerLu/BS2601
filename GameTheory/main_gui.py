import sys
import json
import time
import concurrent.futures
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QTextEdit, QGroupBox, 
                             QProgressBar, QMessageBox, QStyleFactory, QSpinBox, QFileDialog, QLineEdit, QDialog)
import os
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QColor, QPalette

# 导入自定义模块
from llm_wraper import LLMWrapper
from player_agent import PrisonerAgent
from game_referee import GameReferee

class GameWorker(QThread):
    """
    后台工作线程，负责处理博弈逻辑和 LLM 调用，避免阻塞 UI。
    """
    # 信号定义
    sig_log = pyqtSignal(str)  # 通用日志信息
    sig_round_start = pyqtSignal(int) # 回合开始
    sig_agent_thought = pyqtSignal(str, str) # 选手名字, 思考内容
    sig_round_result = pyqtSignal(int, dict, dict, int, int) # round, p1_data, p2_data, s1, s2
    sig_game_over = pyqtSignal(dict) # 最终结果

    def __init__(self, max_rounds=5, p1_config="default_agent_config.json", p2_config="default_agent_config.json"):
        super().__init__()
        self.max_rounds = max_rounds
        self.p1_config = p1_config
        self.p2_config = p2_config
        self.is_running = True

    def run(self):
        self.sig_log.emit("正在初始化 AI 选手和裁判...")
        
        try:
            # 初始化对象
            # 注意：这里会实例化 LLMWrapper，如果 API Key 有问题会在这里报错
            llm = LLMWrapper()
            p1_name = "选手 A"
            p2_name = "选手 B"
            
            p1 = PrisonerAgent(p1_name, llm, self.max_rounds, config_path=self.p1_config)
            p2 = PrisonerAgent(p2_name, llm, self.max_rounds, config_path=self.p2_config)
            referee = GameReferee(p1_name, p2_name, max_rounds=self.max_rounds)
            
            self.sig_log.emit(f"对局开始！共 {self.max_rounds} 轮。")
            
            # 游戏循环
            for r in range(1, self.max_rounds + 1):
                if not self.is_running:
                    break
                
                self.sig_round_start.emit(r)
                self.sig_log.emit(f"--- 第 {r} 轮思考中 ---")
                
                # 并发调用两个 Agent 进行决策，节省时间
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                    future1 = executor.submit(p1.decide, r)
                    future2 = executor.submit(p2.decide, r)
                    
                    try:
                        res1 = future1.result()
                        res2 = future2.result()
                    except Exception as e:
                        self.sig_log.emit(f"错误: LLM 调用失败 - {str(e)}")
                        return

                # 发送思考过程给 UI
                self.sig_agent_thought.emit(p1_name, res1.get("thought", "无思考内容"))
                self.sig_agent_thought.emit(p2_name, res2.get("thought", "无思考内容"))
                
                # 获取动作
                act1 = res1.get("action", "cooperate")
                act2 = res2.get("action", "cooperate")
                
                # 裁判判分
                score1, score2 = referee.judge_round(act1, act2)
                
                # 更新 Agent 记忆 (非常重要，否则 Agent 不知道上一轮发生了什么)
                # update_history(round, my_action, op_action, my_score, op_score)
                p1.update_history(r, act1, act2, score1, score2)
                p2.update_history(r, act2, act1, score2, score1)
                
                # 发送本轮结果给 UI
                self.sig_round_result.emit(r, res1, res2, score1, score2)
                
                self.sig_log.emit(f"第 {r} 轮结束: {p1_name}[{act1}] vs {p2_name}[{act2}]")
                
                # 稍微停顿一下，让用户能看清过程
                time.sleep(1.5)

            # 游戏结束
            final_res = referee.get_final_result()
            self.sig_game_over.emit(final_res)
            self.sig_log.emit("比赛结束！")

        except Exception as e:
            import traceback
            err_msg = f"运行时发生严重错误:\n{traceback.format_exc()}"
            self.sig_log.emit(err_msg)

    def stop(self):
        self.is_running = False


class PlayerPanel(QGroupBox):
    """单个选手的显示面板"""
    def __init__(self, title):
        super().__init__(title)
        self.config_path = "default_agent_config.json"
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 配置选择
        config_layout = QHBoxLayout()
        self.config_edit = QLineEdit(self.config_path)
        self.config_edit.setReadOnly(True)
        config_layout.addWidget(self.config_edit)
        
        self.config_btn = QPushButton("选择配置")
        self.config_btn.clicked.connect(self.choose_config)
        config_layout.addWidget(self.config_btn)

        self.preview_btn = QPushButton("预览")
        self.preview_btn.clicked.connect(self.preview_config)
        config_layout.addWidget(self.preview_btn)

        layout.addLayout(config_layout)
        
        # 分数显示
        self.score_label = QLabel("当前得分: 0")
        self.score_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        self.score_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.score_label)
        
        # 动作显示
        self.action_label = QLabel("等待出招...")
        self.action_label.setStyleSheet("font-size: 18px; font-weight: bold; color: gray; border: 2px solid #ccc; border-radius: 5px; padding: 10px;")
        self.action_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.action_label)
        
        # 思考过程
        layout.addWidget(QLabel("思考过程:"))
        self.thought_text = QTextEdit()
        self.thought_text.setReadOnly(True)
        self.thought_text.setStyleSheet("background-color: #f9f9f9; border: 1px solid #ddd; font-family: sans-serif;")
        layout.addWidget(self.thought_text)
        
        self.setLayout(layout)

    def choose_config(self):
        filename, _ = QFileDialog.getOpenFileName(self, "选择配置文件", "", "JSON Files (*.json);;All Files (*)")
        if filename:
            self.config_path = filename
            self.config_edit.setText(filename)

    def preview_config(self):
        """预览选中的配置文件，以友好方式展示"""
        config_path = self.config_path
        if not config_path or not os.path.exists(config_path):
            QMessageBox.warning(self, "错误", "配置文件路径无效")
            return

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"配置预览: {os.path.basename(config_path)}")
            dialog.resize(700, 600)
            
            layout = QVBoxLayout(dialog)
            
            # 使用 QTextBrowser 显示格式化后的内容
            text_browser = QTextEdit()
            text_browser.setReadOnly(True)
            layout.addWidget(text_browser)
            
            # 构建 HTML 内容
            html_content = f"""
            <style>
                h3 {{ color: #2c3e50; background-color: #ecf0f1; padding: 5px; border-radius: 4px; }}
                p, li {{ font-size: 14px; line-height: 1.6; color: #34495e; }}
                .highlight {{ color: #e74c3c; font-weight: bold; }}
                pre {{ background-color: #f8f9fa; padding: 10px; border: 1px solid #ddd; border-radius: 4px; white-space: pre-wrap; }}
            </style>
            """
            
            # 1. 规则描述
            rules = content.get("rules_description", "无").replace("\n", "<br>")
            html_content += f"<h3>📜 规则描述</h3><p>{rules}</p>"
            
            # 2. 策略指导
            guidance = content.get("strategy_guidance", {})
            html_content += "<h3>💡 策略指导</h3><ul>"
            if isinstance(guidance, dict):
                tie = guidance.get("tie", "无")
                lead = guidance.get("lead", "无")
                lag = guidance.get("lag", "无")
                html_content += f"<li><b>⚖️ 平局时:</b> {tie}</li>"
                html_content += f"<li><b>🚀 领先时:</b> {lead}</li>"
                html_content += f"<li><b>⚠️ 落后时:</b> {lag}</li>"
            else:
                html_content += f"<li>{guidance}</li>"
            html_content += "</ul>"
            
            # 3. 用户提示词模板
            user_prompt = content.get("user_prompt_template", "无").replace("\n", "<br>")
            html_content += f"<h3>🗣️ 用户提示词模板</h3><p style='background-color: #fdfefe; padding: 8px; border-left: 3px solid #3498db;'>{user_prompt}</p>"
            
            # 4. JSON 格式说明 (可选，折叠或简化)
            json_instr = content.get("json_format_instruction", "无").replace("\n", "<br>")
            html_content += f"<h3>🤖 JSON 输出要求</h3><p style='color: #7f8c8d; font-size: 12px;'>{json_instr}</p>"
            
            text_browser.setHtml(html_content)
            
            btn = QPushButton("关闭")
            btn.clicked.connect(dialog.accept)
            layout.addWidget(btn)
            
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"读取配置文件失败:\n{str(e)}")

    def update_score(self, score):
        self.score_label.setText(f"当前得分: {score}")

    def update_action(self, action):
        text = "合作 (Cooperate)" if action.lower() == "cooperate" else "背叛 (Defect)"
        color = "#2ecc71" if action.lower() == "cooperate" else "#e74c3c" # 绿 vs 红
        self.action_label.setText(text)
        self.action_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: white; background-color: {color}; border-radius: 5px; padding: 10px;")

    def update_thought(self, thought):
        self.thought_text.setText(thought)
        
    def reset(self):
        self.score_label.setText("当前得分: 0")
        self.action_label.setText("等待出招...")
        self.action_label.setStyleSheet("font-size: 18px; font-weight: bold; color: gray; border: 2px solid #ccc; border-radius: 5px; padding: 10px;")
        self.thought_text.clear()


class GameWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("囚徒困境博弈模拟器 (AI vs AI)")
        self.resize(1000, 700)
        self.init_ui()
        self.worker = None

    def init_ui(self):
        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)

        # 1. 顶部状态栏
        top_bar = QHBoxLayout()
        self.round_label = QLabel("准备开始")
        self.round_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        top_bar.addWidget(self.round_label, alignment=Qt.AlignCenter)
        main_layout.addLayout(top_bar)

        # 2. 中间选手区域
        players_layout = QHBoxLayout()
        
        self.panel_p1 = PlayerPanel("选手 A")
        self.panel_p2 = PlayerPanel("选手 B")
        
        players_layout.addWidget(self.panel_p1)
        players_layout.addWidget(self.panel_p2)
        
        main_layout.addLayout(players_layout, stretch=1)

        # 3. 底部控制区
        bottom_layout = QVBoxLayout()
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 5) # 默认5轮
        self.progress_bar.setValue(0)
        bottom_layout.addWidget(self.progress_bar)

        # 设置区域
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(QLabel("博弈轮数:"))
        self.rounds_spin = QSpinBox()
        self.rounds_spin.setRange(1, 100)
        self.rounds_spin.setValue(5)
        settings_layout.addWidget(self.rounds_spin)
        settings_layout.addStretch()
        bottom_layout.addLayout(settings_layout)

        # 按钮
        self.start_btn = QPushButton("开始博弈")
        self.start_btn.setMinimumHeight(50)
        self.start_btn.setStyleSheet("font-size: 16px; background-color: #3498db; color: white; border-radius: 5px;")
        self.start_btn.clicked.connect(self.start_game)
        bottom_layout.addWidget(self.start_btn)
        
        # 日志区
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(100)
        self.log_text.setReadOnly(True)
        bottom_layout.addWidget(self.log_text)

        main_layout.addLayout(bottom_layout)

    def log(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {msg}")
        # 滚动到底部
        sb = self.log_text.verticalScrollBar()
        sb.setValue(sb.maximum())

    def start_game(self):
        if self.worker is not None and self.worker.isRunning():
            return
            
        # 获取设定的轮数
        rounds = self.rounds_spin.value()

        # 重置 UI
        self.panel_p1.reset()
        self.panel_p2.reset()
        self.progress_bar.setRange(0, rounds)
        self.progress_bar.setValue(0)
        self.log_text.clear()
        self.round_label.setText("博弈初始化...")
        self.start_btn.setEnabled(False)
        self.start_btn.setText("博弈进行中...")
        self.rounds_spin.setEnabled(False)
        self.panel_p1.config_btn.setEnabled(False)
        self.panel_p2.config_btn.setEnabled(False)
        
        # 启动线程
        p1_config = self.panel_p1.config_path
        p2_config = self.panel_p2.config_path
        self.worker = GameWorker(max_rounds=rounds, p1_config=p1_config, p2_config=p2_config)
        self.worker.sig_log.connect(self.log)
        self.worker.sig_round_start.connect(self.on_round_start)
        self.worker.sig_agent_thought.connect(self.on_agent_thought)
        self.worker.sig_round_result.connect(self.on_round_result)
        self.worker.sig_game_over.connect(self.on_game_over)
        self.worker.start()

    def on_round_start(self, round_num):
        total_rounds = self.worker.max_rounds if self.worker else self.rounds_spin.value()
        self.round_label.setText(f"--- 第 {round_num} / {total_rounds} 轮 ---")
        self.progress_bar.setValue(round_num - 1)

    def on_agent_thought(self, name, thought):
        if name == "选手 A":
            self.panel_p1.update_thought(thought)
        else:
            self.panel_p2.update_thought(thought)

    def on_round_result(self, round_num, res1, res2, s1, s2):
        self.progress_bar.setValue(round_num)
        
        # 更新动作显示
        self.panel_p1.update_action(res1.get("action", ""))
        self.panel_p2.update_action(res2.get("action", ""))
        
        # 更新当前累积得分 (Worker 发送的是本轮得分，我们需要累加吗？
        # 其实 game_referee 内部维护了总分，但 Worker 信号目前发的是本轮得分。
        # 为了简单，我们让 UI 自己累加，或者更准确地，我们应该从 Referee 获取总分。
        # 为了修复这个问题，我们在 Worker 里面稍微改一下，把 total_score 也发出来，或者简单点在 UI 里累加。
        # 这里为了展示清晰，我们简单在 UI 里累加)
        
        # 获取当前 UI 上的分数并更新
        current_s1 = int(self.panel_p1.score_label.text().split(": ")[1])
        current_s2 = int(self.panel_p2.score_label.text().split(": ")[1])
        
        self.panel_p1.update_score(current_s1 + s1)
        self.panel_p2.update_score(current_s2 + s2)

    def on_game_over(self, result):
        self.start_btn.setEnabled(True)
        self.start_btn.setText("开始博弈")
        self.rounds_spin.setEnabled(True)
        self.panel_p1.config_btn.setEnabled(True)
        self.panel_p2.config_btn.setEnabled(True)
        self.round_label.setText("博弈结束")
        if self.worker:
            self.progress_bar.setValue(self.worker.max_rounds)
        
        winner = result["winner"]
        final_scores = result["final_scores"]
        p1_score = final_scores.get("选手 A", 0)
        p2_score = final_scores.get("选手 B", 0)
        
        # 确保最后分数对齐
        self.panel_p1.update_score(p1_score)
        self.panel_p2.update_score(p2_score)

        msg = f"最终胜者: {winner}\n\n选手 A 总分: {p1_score}\n选手 B 总分: {p2_score}"
        QMessageBox.information(self, "比赛结果", msg)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置简单的样式
    app.setStyle(QStyleFactory.create("Fusion"))
    
    window = GameWindow()
    window.show()
    sys.exit(app.exec_())
