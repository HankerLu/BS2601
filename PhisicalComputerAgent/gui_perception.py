import sys
import os
import traceback
import shutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                             QWidget, QTextEdit, QLabel, QHBoxLayout, QScrollArea,
                             QFileDialog)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QPixmap, QFont, QTextCursor
from datetime import datetime
import json
import time
import base64
from PIL import Image, ImageDraw, ImageColor

# 导入感知测试模块和相关依赖
from test_qwen_vlm_perception import (run_perception_test, encode_image, 
                                       draw_point_with_label)
from computer_agent_utils.cv_utils import capture_screen_and_save
from computer_agent_utils.config import Config
from openai import OpenAI

try:
    from transformers.models.qwen2_vl.image_processing_qwen2_vl_fast import smart_resize
except ImportError:
    def smart_resize(h, w, factor=32, min_pixels=3136, max_pixels=12845056):
        return h, w


class PerceptionThread(QThread):
    """用于在后台线程运行感知测试的工作线程（屏幕截图模式）"""
    finished = pyqtSignal(str, str, str, float)  # log_dir, result_image_path, json_path, elapsed_time
    error = pyqtSignal(str, str)  # error_msg, traceback_str
    log_message = pyqtSignal(str, str)  # message, level (INFO/WARNING/ERROR/SUCCESS)
    progress = pyqtSignal(str)  # 进度更新
    
    def emit_log(self, message, level="INFO"):
        """发送带时间戳和级别的日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_message.emit(f"[{timestamp}] {message}", level)
    
    def run(self):
        """执行感知测试"""
        start_time = time.time()
        log_dir = None
        
        try:
            self.emit_log("🚀 初始化感知识别任务", "INFO")
            
            # 1. 准备日志目录
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_dir = os.path.join("logs", f"perception_test_{timestamp}")
            os.makedirs(log_dir, exist_ok=True)
            self.emit_log(f"📁 创建日志目录: {log_dir}", "INFO")
            
            # 2. 执行截图
            self.progress.emit("正在截取屏幕...")
            screenshot_path = os.path.join(log_dir, "screen.png")
            self.emit_log(f"📸 开始截取屏幕，保存路径: {screenshot_path}", "INFO")
            
            success, scale = capture_screen_and_save(save_path=screenshot_path)
            
            if not success:
                self.emit_log("❌ 截图失败，无法继续执行", "ERROR")
                self.error.emit("截图失败", "")
                return
            
            # 获取图片信息
            if os.path.exists(screenshot_path):
                screen_img = Image.open(screenshot_path)
                img_size = f"{screen_img.width}x{screen_img.height}"
                file_size = os.path.getsize(screenshot_path) / 1024
                
                self.emit_log(f"✅ 截图成功", "SUCCESS")
                self.emit_log(f"   图像尺寸: {img_size}", "INFO")
                self.emit_log(f"   文件大小: {file_size:.2f} KB", "INFO")
                self.emit_log(f"   缩放比例: {scale:.4f}" if scale != 1 else "   无缩放", "INFO")
            else:
                self.emit_log("⚠️ 截图文件未找到", "WARNING")
            
            # 3. 调用 VLM 模型识别
            self.progress.emit("正在调用 VLM 模型进行识别...")
            self.emit_log(f"🤖 准备调用 VLM 模型: {Config.MODEL_ID}", "INFO")
            self.emit_log(f"🌐 API 端点: {Config.API_BASE_URL}", "INFO")
            
            # 捕获 run_perception_test 的输出
            import io
            from contextlib import redirect_stdout, redirect_stderr
            
            f_out = io.StringIO()
            f_err = io.StringIO()
            
            api_start = time.time()
            with redirect_stdout(f_out), redirect_stderr(f_err):
                run_perception_test()
            api_elapsed = time.time() - api_start
            
            # 输出捕获的日志
            stdout_content = f_out.getvalue()
            stderr_content = f_err.getvalue()
            
            if stdout_content:
                for line in stdout_content.strip().split('\n'):
                    if line.strip():
                        self.emit_log(f"  {line}", "INFO")
            
            if stderr_content:
                for line in stderr_content.strip().split('\n'):
                    if line.strip():
                        self.emit_log(f"  ⚠️ {line}", "WARNING")
            
            self.emit_log(f"⏱️ VLM 模型识别耗时: {api_elapsed:.2f} 秒", "SUCCESS")
            
            # 4. 验证结果文件
            self.progress.emit("正在验证结果文件...")
            result_image = os.path.join(log_dir, "perception_result.png")
            json_result = os.path.join(log_dir, "perception_result.json")
            
            self.emit_log("🔍 检查结果文件是否生成...", "INFO")
            
            if not os.path.exists(result_image):
                self.emit_log(f"❌ 未找到结果图片: {result_image}", "ERROR")
                self.error.emit("未找到结果图片文件", "")
                return
            
            if not os.path.exists(json_result):
                self.emit_log(f"❌ 未找到 JSON 结果: {json_result}", "ERROR")
                self.error.emit("未找到 JSON 结果文件", "")
                return
            
            self.emit_log(f"✅ 结果图片: {result_image} ({os.path.getsize(result_image) / 1024:.2f} KB)", "SUCCESS")
            self.emit_log(f"✅ JSON 结果: {json_result} ({os.path.getsize(json_result) / 1024:.2f} KB)", "SUCCESS")
            
            # 5. 解析并验证 JSON 内容
            try:
                with open(json_result, 'r', encoding='utf-8') as f:
                    elements = json.load(f)
                
                if isinstance(elements, list):
                    self.emit_log(f"📊 成功解析 JSON，共识别 {len(elements)} 个元素", "SUCCESS")
                else:
                    self.emit_log("⚠️ JSON 格式异常：不是列表类型", "WARNING")
                    
            except json.JSONDecodeError as e:
                self.emit_log(f"⚠️ JSON 解析警告: {str(e)}", "WARNING")
            
            # 6. 完成
            elapsed_time = time.time() - start_time
            self.emit_log(f"🎉 识别任务完成！总耗时: {elapsed_time:.2f} 秒", "SUCCESS")
            self.progress.emit("完成")
            
            self.finished.emit(log_dir, result_image, json_result, elapsed_time)
                
        except Exception as e:
            error_msg = f"执行过程中发生错误: {str(e)}"
            tb_str = traceback.format_exc()
            self.emit_log(f"❌ {error_msg}", "ERROR")
            self.emit_log(f"📝 详细错误信息:\n{tb_str}", "ERROR")
            self.error.emit(error_msg, tb_str)


class LocalImagePerceptionThread(QThread):
    """用于处理本地图片识别的工作线程"""
    finished = pyqtSignal(str, str, str, float)  # log_dir, result_image_path, json_path, elapsed_time
    error = pyqtSignal(str, str)  # error_msg, traceback_str
    log_message = pyqtSignal(str, str)  # message, level (INFO/WARNING/ERROR/SUCCESS)
    progress = pyqtSignal(str)  # 进度更新
    
    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path
    
    def emit_log(self, message, level="INFO"):
        """发送带时间戳和级别的日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_message.emit(f"[{timestamp}] {message}", level)
    
    def run(self):
        """执行本地图片识别"""
        start_time = time.time()
        log_dir = None
        
        try:
            self.emit_log("🚀 初始化本地图片识别任务", "INFO")
            self.emit_log(f"📂 图片路径: {self.image_path}", "INFO")
            
            # 1. 验证图片文件
            if not os.path.exists(self.image_path):
                self.emit_log("❌ 图片文件不存在", "ERROR")
                self.error.emit("图片文件不存在", "")
                return
            
            # 2. 准备日志目录
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_dir = os.path.join("logs", f"local_image_{timestamp}")
            os.makedirs(log_dir, exist_ok=True)
            self.emit_log(f"📁 创建日志目录: {log_dir}", "INFO")
            
            # 3. 复制图片到日志目录
            self.progress.emit("正在加载图片...")
            screenshot_path = os.path.join(log_dir, "screen.png")
            
            try:
                # 打开图片并保存为PNG格式
                img = Image.open(self.image_path)
                img_format = img.format
                img_size = f"{img.width}x{img.height}"
                file_size = os.path.getsize(self.image_path) / 1024
                
                self.emit_log(f"✅ 图片加载成功", "SUCCESS")
                self.emit_log(f"   原始格式: {img_format}", "INFO")
                self.emit_log(f"   图像尺寸: {img_size}", "INFO")
                self.emit_log(f"   文件大小: {file_size:.2f} KB", "INFO")
                
                # 转换为RGB模式（如果需要）
                if img.mode in ('RGBA', 'LA', 'P'):
                    self.emit_log(f"   转换图像模式: {img.mode} -> RGB", "INFO")
                    img = img.convert('RGB')
                
                # 保存为PNG
                img.save(screenshot_path, 'PNG')
                self.emit_log(f"💾 图片已保存到工作目录: {screenshot_path}", "INFO")
                
            except Exception as e:
                self.emit_log(f"❌ 图片加载失败: {str(e)}", "ERROR")
                self.error.emit(f"图片加载失败: {str(e)}", "")
                return
            
            # 4. 调用 VLM 模型识别
            self.progress.emit("正在调用 VLM 模型进行识别...")
            self.emit_log(f"🤖 准备调用 VLM 模型: {Config.MODEL_ID}", "INFO")
            self.emit_log(f"🌐 API 端点: {Config.API_BASE_URL}", "INFO")
            
            api_start = time.time()
            
            # 调用识别函数
            success = self._perform_recognition(screenshot_path, log_dir)
            
            api_elapsed = time.time() - api_start
            self.emit_log(f"⏱️ VLM 模型识别耗时: {api_elapsed:.2f} 秒", "SUCCESS")
            
            if not success:
                self.error.emit("识别过程失败", "")
                return
            
            # 5. 验证结果文件
            self.progress.emit("正在验证结果文件...")
            result_image = os.path.join(log_dir, "perception_result.png")
            json_result = os.path.join(log_dir, "perception_result.json")
            
            self.emit_log("🔍 检查结果文件是否生成...", "INFO")
            
            if not os.path.exists(result_image):
                self.emit_log(f"❌ 未找到结果图片: {result_image}", "ERROR")
                self.error.emit("未找到结果图片文件", "")
                return
            
            if not os.path.exists(json_result):
                self.emit_log(f"❌ 未找到 JSON 结果: {json_result}", "ERROR")
                self.error.emit("未找到 JSON 结果文件", "")
                return
            
            self.emit_log(f"✅ 结果图片: {result_image} ({os.path.getsize(result_image) / 1024:.2f} KB)", "SUCCESS")
            self.emit_log(f"✅ JSON 结果: {json_result} ({os.path.getsize(json_result) / 1024:.2f} KB)", "SUCCESS")
            
            # 6. 解析并验证 JSON 内容
            try:
                with open(json_result, 'r', encoding='utf-8') as f:
                    elements = json.load(f)
                
                if isinstance(elements, list):
                    self.emit_log(f"📊 成功解析 JSON，共识别 {len(elements)} 个元素", "SUCCESS")
                else:
                    self.emit_log("⚠️ JSON 格式异常：不是列表类型", "WARNING")
                    
            except json.JSONDecodeError as e:
                self.emit_log(f"⚠️ JSON 解析警告: {str(e)}", "WARNING")
            
            # 7. 完成
            elapsed_time = time.time() - start_time
            self.emit_log(f"🎉 识别任务完成！总耗时: {elapsed_time:.2f} 秒", "SUCCESS")
            self.progress.emit("完成")
            
            self.finished.emit(log_dir, result_image, json_result, elapsed_time)
                
        except Exception as e:
            error_msg = f"执行过程中发生错误: {str(e)}"
            tb_str = traceback.format_exc()
            self.emit_log(f"❌ {error_msg}", "ERROR")
            self.emit_log(f"📝 详细错误信息:\n{tb_str}", "ERROR")
            self.error.emit(error_msg, tb_str)
    
    def _perform_recognition(self, image_path, log_dir):
        """执行图片识别"""
        try:
            # 准备图像
            input_image = Image.open(image_path)
            base64_image = encode_image(image_path)
            
            self.emit_log(f"   原始图像尺寸: {input_image.width}x{input_image.height}", "INFO")
            
            # 智能缩放
            min_pixels = 3136
            max_pixels = 12845056
            
            resized_height, resized_width = smart_resize(
                input_image.height,
                input_image.width,
                factor=32,
                min_pixels=min_pixels,
                max_pixels=max_pixels,
            )
            
            self.emit_log(f"   处理后图像尺寸: {resized_width}x{resized_height}", "INFO")
            
            # 配置客户端
            client = OpenAI(
                api_key=Config.API_KEY,
                base_url=Config.API_BASE_URL,
            )
            
            # 构建 Prompt
            system_prompt = """你是一个具备强大视觉感知能力的AI助手。你的任务是分析屏幕截图，识别并列出屏幕上所有可见的交互元素和重要内容区域。

请输出 JSON 格式的数据，不要包含任何 markdown 代码块标记（如 ```json），直接输出 JSON 字符串。
JSON 结构应该是一个列表，列表中每个对象代表一个识别到的元素，包含以下字段：
- "element_name": 元素的名称或简短描述（中文）
- "element_type": 元素类型（例如：图标、按钮、输入框、链接、文本区域、菜单项、窗口等）
- "coordinate": [x, y] 归一化中心点坐标（范围 0.0 到 1.0）
- "confidence": 你的识别置信度（可选，高/中/低）

请尽可能详尽地识别屏幕上的元素，包括但不限于：
1. 桌面图标、Dock栏图标
2. 菜单栏图标（右上角）和菜单项
3. 窗口标题栏、关闭/最小化/最大化按钮
4. 窗口内的按钮、搜索框、导航栏
5. 网页或应用内的主要文本区域或交互点

请不要输出任何函数调用 (tool call) 或其他解释性文本，只输出 JSON 数据。"""
            
            user_query = "请分析这张图片，列出所有你看到的 UI 元素及其坐标。"
            
            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}},
                        {"type": "text", "text": user_query},
                    ],
                }
            ]
            
            self.emit_log("📤 发送识别请求到 VLM 模型...", "INFO")
            
            completion = client.chat.completions.create(
                model=Config.MODEL_ID,
                messages=messages,
                temperature=0.1,
            )
            
            output_text = completion.choices[0].message.content
            self.emit_log("📥 收到模型响应", "SUCCESS")
            
            # 解析输出
            json_str = output_text.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.startswith("```"):
                json_str = json_str[3:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            
            elements = json.loads(json_str)
            
            if not isinstance(elements, list):
                self.emit_log("❌ 模型输出的不是列表格式", "ERROR")
                return False
            
            self.emit_log(f"✅ 成功识别到 {len(elements)} 个元素", "SUCCESS")
            
            # 绘制可视化结果
            self.emit_log("🎨 正在绘制可视化结果...", "INFO")
            display_image = input_image.copy()
            
            for i, el in enumerate(elements):
                name = el.get("element_name", "Unknown")
                etype = el.get("element_type", "Unknown")
                coord = el.get("coordinate")
                
                if coord and len(coord) == 2:
                    norm_x, norm_y = coord
                    
                    # 处理幻觉绝对坐标
                    if norm_x > 1.0:
                        norm_x /= Config.SCREENSHOT_WIDTH
                    if norm_y > 1.0:
                        norm_y /= Config.SCREENSHOT_HEIGHT
                    
                    # 限制范围
                    norm_x = max(0.0, min(1.0, norm_x))
                    norm_y = max(0.0, min(1.0, norm_y))
                    
                    pixel_x = int(norm_x * display_image.width)
                    pixel_y = int(norm_y * display_image.height)
                    
                    label = f"{i+1}. {name}"
                    display_image = draw_point_with_label(display_image, [pixel_x, pixel_y], label)
            
            # 保存结果
            result_path = os.path.join(log_dir, "perception_result.png")
            display_image.save(result_path)
            self.emit_log(f"💾 可视化结果已保存", "SUCCESS")
            
            # 保存 JSON 结果
            json_path = os.path.join(log_dir, "perception_result.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(elements, f, indent=4, ensure_ascii=False)
            self.emit_log(f"💾 JSON 结果已保存", "SUCCESS")
            
            return True
            
        except json.JSONDecodeError as e:
            self.emit_log(f"❌ JSON 解析失败: {str(e)}", "ERROR")
            return False
        except Exception as e:
            self.emit_log(f"❌ 识别过程出错: {str(e)}", "ERROR")
            return False


class PerceptionGUI(QMainWindow):
    """感知识别主界面"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.perception_thread = None
        self.task_start_time = None
        self.log_count = {"INFO": 0, "WARNING": 0, "ERROR": 0, "SUCCESS": 0}
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("屏幕感知识别系统")
        self.setGeometry(100, 100, 1400, 900)
        
        # 主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # 标题
        title_label = QLabel("🖥️ Qwen VLM 屏幕感知识别")
        title_label.setFont(QFont("Arial", 20, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 截屏识别按钮
        self.run_button = QPushButton("🚀 执行截屏识别")
        self.run_button.setFont(QFont("Arial", 14))
        self.run_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 15px 32px;
                border-radius: 8px;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.run_button.clicked.connect(self.start_perception)
        
        # 导入图片按钮
        self.import_button = QPushButton("📂 导入本地图片")
        self.import_button.setFont(QFont("Arial", 14))
        self.import_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 15px 32px;
                border-radius: 8px;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.import_button.clicked.connect(self.import_local_image)
        
        button_layout.addStretch()
        button_layout.addWidget(self.run_button)
        button_layout.addSpacing(20)
        button_layout.addWidget(self.import_button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        # 状态标签
        self.status_label = QLabel("状态: 💤 等待执行")
        self.status_label.setFont(QFont("Arial", 12))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("padding: 10px; background-color: #e8f5e9; border-radius: 5px;")
        main_layout.addWidget(self.status_label)
        
        # 进度标签
        self.progress_label = QLabel("")
        self.progress_label.setFont(QFont("Arial", 10))
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("color: #666; font-style: italic;")
        main_layout.addWidget(self.progress_label)
        
        # 内容区域（左右分栏）
        content_layout = QHBoxLayout()
        
        # 左侧：日志输出
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        
        # 日志标题和统计
        log_header = QHBoxLayout()
        log_label = QLabel("📋 运行日志")
        log_label.setFont(QFont("Arial", 12, QFont.Bold))
        log_header.addWidget(log_label)
        log_header.addStretch()
        
        self.log_stats_label = QLabel("")
        self.log_stats_label.setFont(QFont("Arial", 9))
        self.log_stats_label.setStyleSheet("color: #666;")
        log_header.addWidget(self.log_stats_label)
        
        log_layout.addLayout(log_header)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier", 9))
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        log_layout.addWidget(self.log_text)
        
        content_layout.addWidget(log_widget, stretch=1)
        
        # 右侧：结果显示
        result_widget = QWidget()
        result_layout = QVBoxLayout(result_widget)
        result_label = QLabel("🖼️ 识别结果")
        result_label.setFont(QFont("Arial", 12, QFont.Bold))
        result_layout.addWidget(result_label)
        
        # 图片显示区域（带滚动条）
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.image_label = QLabel("等待识别...")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: #f0f0f0; border: 2px dashed #ccc; padding: 20px;")
        scroll_area.setWidget(self.image_label)
        result_layout.addWidget(scroll_area)
        
        # 统计信息
        self.stats_label = QLabel("")
        self.stats_label.setFont(QFont("Courier", 9))
        self.stats_label.setWordWrap(True)
        self.stats_label.setStyleSheet("background-color: #f5f5f5; padding: 10px; border-radius: 5px;")
        result_layout.addWidget(self.stats_label)
        
        content_layout.addWidget(result_widget, stretch=1)
        
        main_layout.addLayout(content_layout, stretch=1)
        
    def start_perception(self):
        """开始执行感知识别（屏幕截图）"""
        if self.perception_thread and self.perception_thread.isRunning():
            self.append_log("⚠️ 已有任务正在执行中，请稍候...", "WARNING")
            return
        
        # 重置计数器
        self.log_count = {"INFO": 0, "WARNING": 0, "ERROR": 0, "SUCCESS": 0}
        self.task_start_time = datetime.now()
        
        # 清空之前的内容
        self.log_text.clear()
        self.image_label.setText("处理中...")
        self.image_label.setStyleSheet("background-color: #f0f0f0; border: 2px dashed #ccc; padding: 20px;")
        self.stats_label.clear()
        self.progress_label.clear()
        
        # 禁用按钮
        self.run_button.setEnabled(False)
        self.import_button.setEnabled(False)
        self.status_label.setText("状态: 🔄 正在执行识别...")
        self.status_label.setStyleSheet("padding: 10px; background-color: #fff3e0; border-radius: 5px;")
        
        # 打印启动日志
        self.append_log("=" * 80, "INFO")
        self.append_log(f"  屏幕截图识别任务启动", "INFO")
        self.append_log(f"  启动时间: {self.task_start_time.strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
        self.append_log("=" * 80, "INFO")
        self.append_log("", "INFO")
        
        # 创建并启动工作线程
        self.perception_thread = PerceptionThread()
        self.perception_thread.finished.connect(self.on_perception_finished)
        self.perception_thread.error.connect(self.on_perception_error)
        self.perception_thread.log_message.connect(self.append_log)
        self.perception_thread.progress.connect(self.update_progress)
        self.perception_thread.start()
    
    def import_local_image(self):
        """导入本地图片进行识别"""
        if self.perception_thread and self.perception_thread.isRunning():
            self.append_log("⚠️ 已有任务正在执行中，请稍候...", "WARNING")
            return
        
        # 打开文件选择对话框
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择要识别的图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;所有文件 (*)"
        )
        
        if not file_path:
            # 用户取消选择
            return
        
        # 重置计数器
        self.log_count = {"INFO": 0, "WARNING": 0, "ERROR": 0, "SUCCESS": 0}
        self.task_start_time = datetime.now()
        
        # 清空之前的内容
        self.log_text.clear()
        self.image_label.setText("处理中...")
        self.image_label.setStyleSheet("background-color: #f0f0f0; border: 2px dashed #ccc; padding: 20px;")
        self.stats_label.clear()
        self.progress_label.clear()
        
        # 禁用按钮
        self.run_button.setEnabled(False)
        self.import_button.setEnabled(False)
        self.status_label.setText("状态: 🔄 正在执行识别...")
        self.status_label.setStyleSheet("padding: 10px; background-color: #fff3e0; border-radius: 5px;")
        
        # 打印启动日志
        self.append_log("=" * 80, "INFO")
        self.append_log(f"  本地图片识别任务启动", "INFO")
        self.append_log(f"  启动时间: {self.task_start_time.strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
        self.append_log(f"  图片文件: {file_path}", "INFO")
        self.append_log("=" * 80, "INFO")
        self.append_log("", "INFO")
        
        # 创建并启动工作线程
        self.perception_thread = LocalImagePerceptionThread(file_path)
        self.perception_thread.finished.connect(self.on_perception_finished)
        self.perception_thread.error.connect(self.on_perception_error)
        self.perception_thread.log_message.connect(self.append_log)
        self.perception_thread.progress.connect(self.update_progress)
        self.perception_thread.start()
        
    def on_perception_finished(self, log_dir, result_image_path, json_path, elapsed_time):
        """感知识别完成的回调"""
        self.append_log("", "INFO")
        self.append_log("=" * 80, "SUCCESS")
        self.append_log("  🎉 识别任务完成！", "SUCCESS")
        self.append_log("=" * 80, "SUCCESS")
        self.append_log("", "INFO")
        
        self.status_label.setText("状态: ✅ 识别完成")
        self.status_label.setStyleSheet("padding: 10px; background-color: #e8f5e9; border-radius: 5px;")
        self.progress_label.setText(f"完成！总耗时: {elapsed_time:.2f} 秒")
        self.run_button.setEnabled(True)
        self.import_button.setEnabled(True)
        
        # 显示结果图片
        if os.path.exists(result_image_path):
            try:
                pixmap = QPixmap(result_image_path)
                # 获取图片信息
                img_width = pixmap.width()
                img_height = pixmap.height()
                
                # 按比例缩放以适应显示区域
                scaled_pixmap = pixmap.scaledToWidth(700, Qt.SmoothTransformation)
                self.image_label.setPixmap(scaled_pixmap)
                self.image_label.setStyleSheet("background-color: white; border: 2px solid #4CAF50;")
                
                self.append_log(f"🖼️ 结果图片已加载", "SUCCESS")
                self.append_log(f"   路径: {result_image_path}", "INFO")
                self.append_log(f"   尺寸: {img_width}x{img_height}", "INFO")
            except Exception as e:
                self.append_log(f"⚠️ 加载图片失败: {str(e)}", "ERROR")
        
        # 显示统计信息
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    elements = json.load(f)
                
                if isinstance(elements, list):
                    element_types = {}
                    high_conf = 0
                    
                    for el in elements:
                        etype = el.get('element_type', '未知')
                        element_types[etype] = element_types.get(etype, 0) + 1
                        
                        conf = el.get('confidence', '').lower()
                        if conf in ['高', 'high']:
                            high_conf += 1
                    
                    # 构建统计文本
                    stats_text = "╔" + "═" * 58 + "╗\n"
                    stats_text += "║  📊 识别结果统计" + " " * 40 + "║\n"
                    stats_text += "╠" + "═" * 58 + "╣\n"
                    stats_text += f"║  总元素数: {len(elements):<44} ║\n"
                    stats_text += f"║  高置信度: {high_conf:<43} ║\n"
                    stats_text += "╠" + "═" * 58 + "╣\n"
                    stats_text += "║  元素类型分布:" + " " * 43 + "║\n"
                    
                    # 按数量排序
                    sorted_types = sorted(element_types.items(), key=lambda x: x[1], reverse=True)
                    for etype, count in sorted_types[:10]:  # 最多显示前10个
                        line = f"║    • {etype}: {count}"
                        padding = 58 - len(line.encode('utf-8')) + len(line)
                        stats_text += line + " " * padding + "║\n"
                    
                    if len(sorted_types) > 10:
                        stats_text += f"║    ... 还有 {len(sorted_types) - 10} 种类型" + " " * 27 + "║\n"
                    
                    stats_text += "╠" + "═" * 58 + "╣\n"
                    stats_text += f"║  结果目录:" + " " * 46 + "║\n"
                    
                    # 分行显示路径
                    path_parts = log_dir.split('/')
                    for part in path_parts[-2:]:  # 只显示最后两级目录
                        line = f"║    {part}"
                        padding = 58 - len(line.encode('utf-8')) + len(line)
                        stats_text += line + " " * padding + "║\n"
                    
                    stats_text += "╚" + "═" * 58 + "╝"
                    
                    self.stats_label.setText(stats_text)
                    self.append_log(f"📊 JSON 结果统计", "SUCCESS")
                    self.append_log(f"   路径: {json_path}", "INFO")
                    self.append_log(f"   元素总数: {len(elements)}", "INFO")
                    
                    # 详细列出前5个元素
                    self.append_log("", "INFO")
                    self.append_log("🔍 识别到的元素示例 (前5个):", "INFO")
                    for i, el in enumerate(elements[:5], 1):
                        name = el.get('element_name', '未知')
                        etype = el.get('element_type', '未知')
                        coord = el.get('coordinate', [0, 0])
                        self.append_log(f"   {i}. {name} ({etype}) - 坐标: {coord}", "INFO")
                    
                    if len(elements) > 5:
                        self.append_log(f"   ... 还有 {len(elements) - 5} 个元素", "INFO")
                else:
                    self.append_log("⚠️ JSON 格式异常：不是列表类型", "WARNING")
                    
            except json.JSONDecodeError as e:
                self.append_log(f"❌ JSON 解析错误: {str(e)}", "ERROR")
            except Exception as e:
                self.append_log(f"❌ 处理统计信息时出错: {str(e)}", "ERROR")
        
        # 最终汇总
        self.append_log("", "INFO")
        self.append_log("📈 任务执行摘要:", "INFO")
        self.append_log(f"   开始时间: {self.task_start_time.strftime('%H:%M:%S')}", "INFO")
        self.append_log(f"   结束时间: {datetime.now().strftime('%H:%M:%S')}", "INFO")
        self.append_log(f"   总耗时: {elapsed_time:.2f} 秒", "INFO")
        self.append_log(f"   日志统计: INFO={self.log_count['INFO']} SUCCESS={self.log_count['SUCCESS']} WARNING={self.log_count['WARNING']} ERROR={self.log_count['ERROR']}", "INFO")
        
    def on_perception_error(self, error_msg, traceback_str):
        """感知识别出错的回调"""
        self.append_log("", "ERROR")
        self.append_log("=" * 80, "ERROR")
        self.append_log("  ❌ 识别任务失败", "ERROR")
        self.append_log("=" * 80, "ERROR")
        self.append_log("", "ERROR")
        
        self.status_label.setText("状态: ❌ 识别失败")
        self.status_label.setStyleSheet("padding: 10px; background-color: #ffebee; border-radius: 5px;")
        self.progress_label.setText("任务失败")
        self.run_button.setEnabled(True)
        self.import_button.setEnabled(True)
        
        self.append_log(f"错误信息: {error_msg}", "ERROR")
        
        if traceback_str:
            self.append_log("", "ERROR")
            self.append_log("详细错误堆栈:", "ERROR")
            for line in traceback_str.split('\n'):
                if line.strip():
                    self.append_log(f"  {line}", "ERROR")
        
        self.image_label.setText("❌ 识别失败")
        self.image_label.setStyleSheet("background-color: #ffebee; border: 2px dashed #f44336; padding: 20px; color: #c62828;")
        
    def update_progress(self, progress_text):
        """更新进度信息"""
        self.progress_label.setText(f"▶ {progress_text}")
        
    def append_log(self, text, level="INFO"):
        """追加日志文本（带颜色）"""
        # 统计
        if level in self.log_count:
            self.log_count[level] += 1
        
        # 更新统计显示
        self.log_stats_label.setText(
            f"INFO: {self.log_count['INFO']} | "
            f"SUCCESS: {self.log_count['SUCCESS']} | "
            f"WARNING: {self.log_count['WARNING']} | "
            f"ERROR: {self.log_count['ERROR']}"
        )
        
        # 根据级别设置颜色
        color_map = {
            "INFO": "#d4d4d4",      # 白色
            "SUCCESS": "#4ec9b0",   # 青色
            "WARNING": "#dcdcaa",   # 黄色
            "ERROR": "#f48771"      # 红色
        }
        
        color = color_map.get(level, "#d4d4d4")
        
        # 使用 HTML 格式化
        formatted_text = f'<span style="color: {color};">{text}</span>'
        
        # 添加到文本框
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)
        self.log_text.insertHtml(formatted_text + '<br>')
        
        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle('Fusion')
    
    # 创建并显示主窗口
    gui = PerceptionGUI()
    gui.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
