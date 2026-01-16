import os
import json
import base64
import time
import shutil
import sys
from datetime import datetime
from openai import OpenAI
from PIL import Image
from qwen_agent.llm.fncall_prompts.nous_fncall_prompt import (
    NousFnCallPrompt,
    Message,
    ContentItem,
)
from transformers.models.qwen2_vl.image_processing_qwen2_vl_fast import smart_resize

import platform

try:
    # 尝试导入 AppKit 用于 macOS 的高级窗口控制
    import objc
    from AppKit import NSWindow, NSWindowCollectionBehaviorCanJoinAllSpaces, NSWindowCollectionBehaviorStationary, NSApplication, NSFloatingWindowLevel
except ImportError:
    pass

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                            QTextEdit, QPushButton, QLabel, QDesktopWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from computer_agent_utils.computer_agent_function_call import ComputerUse
from computer_agent_utils.cv_utils import capture_screen_and_save
from computer_agent_utils.config import Config, Utils

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def perform_gui_grounding_with_api(screenshot_path, user_query, model_id, prev_screenshot_path=None, prev_action_summary=None, min_pixels=3136, max_pixels=12845056):
    """
    Perform GUI grounding using Qwen model to interpret user query on a screenshot.
    
    Args:
        screenshot_path (str): Path to the screenshot image
        user_query (str): User's query/instruction
        model: Preloaded Qwen model
        prev_screenshot_path (str): Path to the previous screenshot image (optional)
        prev_action_summary (str): Summary of the previous action taken (optional)
        min_pixels: Minimum pixels for the image
        max_pixels: Maximum pixels for the image
        
    Returns:
        tuple: (output_text, display_image) - Model's output text and annotated image
    """

    # Open and process image
    input_image = Image.open(screenshot_path)
    base64_image = encode_image(screenshot_path)
    
    # Auto-detect image format from file extension
    file_ext = os.path.splitext(screenshot_path)[1].lower()
    if file_ext == '.png':
        image_type = 'png'
    elif file_ext in ['.jpg', '.jpeg']:
        image_type = 'jpeg'
    elif file_ext == '.webp':
        image_type = 'webp'
    else:
        image_type = 'jpeg'  # Default to jpeg if unknown
    
    # Process previous image if provided
    prev_image_content = []
    prompt_suffix = ""
    if prev_screenshot_path and os.path.exists(prev_screenshot_path):
        try:
            prev_base64 = encode_image(prev_screenshot_path)
            prev_ext = os.path.splitext(prev_screenshot_path)[1].lower()
            prev_type = 'png' if prev_ext == '.png' else ('jpeg' if prev_ext in ['.jpg', '.jpeg'] else 'jpeg')
            
            prev_image_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/{prev_type};base64,{prev_base64}"},
            })
            prompt_suffix = "\n\n注意：第一张图片是上一步操作后的截图（用于参考），第二张图片是当前屏幕截图。请针对当前屏幕（第二张图）进行下一步操作。"
        except Exception as e:
            print(f"Warning: Failed to process previous screenshot: {e}")

    # Process previous action summary
    prev_action_text = ""
    if prev_action_summary:
        prev_action_text = f"\n\n**上一步执行的操作**：{prev_action_summary}\n请根据上一步操作和当前屏幕变化，判断任务进展。如果上一步操作成功（如菜单已展开、应用已打开），请继续下一步或结束任务。"

    client = OpenAI(
        #If the environment variable is not configured, please replace the following line with the Dashscope API Key: api_key="sk-xxx". Access via https://bailian.console.alibabacloud.com/?apiKey=1 "
        api_key=Config.API_KEY,
        base_url=Config.API_BASE_URL,
    )
    resized_height, resized_width = smart_resize(
        input_image.height,
        input_image.width,
        factor=32,
        min_pixels=min_pixels,
        max_pixels=max_pixels,
    )
    
    # Initialize computer use function
    computer_use = ComputerUse()

    # Build messages
    system_message = NousFnCallPrompt().preprocess_fncall_messages(
        messages=[
            Message(role="system", content=[ContentItem(text=f"你是一个能够操作电脑的AI助手。你正在运行于 macOS 操作系统上。你可以通过截图理解当前屏幕内容，并输出坐标和操作指令来控制鼠标和键盘。\n\n**重要步骤**：\n1. 首先，用自然语言详细描述你在截图上看到了什么，以及你打算做什么。\n2. 然后，生成相应的工具调用代码。\n\n**任务完成判断**：\n当你认为用户指派的任务已经完成时，请务必调用 `computer_use` 工具，将 `action` 设置为 `terminate`，并将 `status` 设置为 `success`。")]),
        ],
        functions=[computer_use.function],
        lang=None,
    )
    system_message = system_message[0].model_dump()
    messages=[
        {
            "role": "system",
            "content": [
                {"type": "text", "text": msg["text"]} for msg in system_message["content"]
            ],
        },
        {
            "role": "user",
            "content": [
                *prev_image_content,
                {
                    "type": "image_url",
                    # "min_pixels": 1024,
                    # "max_pixels": max_pixels,
                    # Pass in BASE64 image data. Note that the image format (i.e., image/{format}) must match the Content Type in the list of supported images. "f" is the method for string formatting.
                    # PNG image:  f"data:image/png;base64,{base64_image}"
                    # JPEG image: f"data:image/jpeg;base64,{base64_image}"
                    # WEBP image: f"data:image/webp;base64,{base64_image}"
                    # Auto-detected format based on file extension
                    "image_url": {"url": f"data:image/{image_type};base64,{base64_image}"},
                },
                {"type": "text", "text": user_query + prev_action_text + "\n\n请注意：请务必先用中文简要描述你的观察和思考，然后再输出工具调用。如果任务已完成，请调用 terminate 结束。" + prompt_suffix},
            ],
        }
    ]
    # print(json.dumps(messages, indent=4))
    completion = client.chat.completions.create(
        model = model_id,
        messages = messages,
       
    )
    
    output_text = completion.choices[0].message.content


    # Parse action and visualize
    try:
        tool_call_content = output_text.split('<tool_call>\n')[1].split('\n</tool_call>')[0]
        action = json.loads(tool_call_content)
        
        display_image = input_image.resize((resized_width, resized_height))

        if 'arguments' in action and 'coordinate' in action['arguments']:
            coordinate_relative = action['arguments']['coordinate']
            # 使用统一 Utils 进行转换，支持 hallucinated absolute coordinates
            real_x, real_y = Utils.normalize_to_pixel(coordinate_relative[0], coordinate_relative[1], resized_width, resized_height)
            coordinate_absolute = [real_x, real_y]
            display_image = draw_point(display_image, coordinate_absolute, color='green')
            
    except (IndexError, json.JSONDecodeError, KeyError) as e:
        print(f"Warning: Could not parse tool call or coordinates from output. Error: {e}")
        display_image = input_image.resize((resized_width, resized_height))
    
    return output_text, display_image


from PIL import Image, ImageDraw, ImageColor

def draw_point(image: Image.Image, point: list, color=None):
    if isinstance(color, str):
        try:
            color = ImageColor.getrgb(color)
            color = color + (128,)  
        except ValueError:
            color = (255, 0, 0, 128)  
    else:
        color = (255, 0, 0, 128)  

    overlay = Image.new('RGBA', image.size, (255, 255, 255, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    radius = min(image.size) * 0.05
    x, y = point 

    overlay_draw.ellipse(
        [(x - radius, y - radius), (x + radius, y + radius)],
        fill=color
    )
    
    center_radius = radius * 0.1
    overlay_draw.ellipse(
        [(x - center_radius, y - center_radius), 
         (x + center_radius, y + center_radius)],
        fill=(0, 255, 0, 255)
    )

    image = image.convert('RGBA')
    combined = Image.alpha_composite(image, overlay)

    return combined.convert('RGB')

class ComputerAgentWorker(QThread):
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    
    def __init__(self, user_query, model_id):
        super().__init__()
        self.user_query = user_query
        self.model_id = model_id
        self.is_running = True

    def stop(self):
        self.is_running = False

    def run(self):
        self.log_signal.emit(f"Task: {self.user_query}")
        self.log_signal.emit("Starting agent...")

        # Create log directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = os.path.join("logs", f"run_{timestamp}")
        os.makedirs(log_dir, exist_ok=True)
        self.log_signal.emit(f"Logging to: {log_dir}")
        
        # Initialize action history list
        action_history = []
        step_count = 0
        last_screenshot_path = None
        last_action_summary = None

        try:
            while self.is_running:
                step_count += 1
                step_prefix = f"step_{step_count:03d}"
                self.status_signal.emit(f"Step {step_count}: Capture Screen")
                self.log_signal.emit(f"\n--- Step {step_count} ---")

                # 截图并保存
                screenshot_path = "imgs/screen.png"
                success, scale = capture_screen_and_save(save_path=screenshot_path)
                if not success:
                    self.log_signal.emit("截图失败")
                    time.sleep(1)
                    continue
                
                # Save screenshot to log
                log_screenshot_path = os.path.join(log_dir, f"{step_prefix}_screen.png")
                shutil.copy(screenshot_path, log_screenshot_path)

                screenshot = screenshot_path
                
                with Image.open(screenshot) as img:
                    img_width, img_height = img.size
                
                try:
                    self.status_signal.emit(f"Step {step_count}: Thinking...")
                    output_text, display_image = perform_gui_grounding_with_api(
                        screenshot, 
                        self.user_query, 
                        self.model_id, 
                        prev_screenshot_path=last_screenshot_path,
                        prev_action_summary=last_action_summary
                    )

                    # Display results
                    # self.log_signal.emit(f"Model Output: {output_text}") # 移除原始模型输出日志

                    # Execute the action using ComputerUse
                    action_data = None
                    if '<tool_call>' in output_text:
                        self.status_signal.emit(f"Step {step_count}: Executing Action")
                        
                        # 提取思考过程（tool_call 之前的文本）和工具调用
                        parts = output_text.split('<tool_call>')
                        thought_content = parts[0].strip()
                        tool_call_content = parts[1].split('</tool_call>')[0].strip()
                        
                        action_data = json.loads(tool_call_content)
                        
                        # 提取参数
                        if 'arguments' in action_data:
                            action_params = action_data['arguments']
                        else:
                            action_params = action_data

                        # 构造动作摘要
                        action_type = action_params.get("action", "unknown")
                        action_details = ""
                        if "coordinate" in action_params:
                            action_details += f" at {action_params['coordinate']}"
                        if "keys" in action_params:
                            action_details += f" with keys {action_params['keys']}"
                        if "text" in action_params:
                            action_details += f" typing '{action_params['text']}'"
                        
                        last_action_summary = f"{action_type}{action_details}"

                        # 显示思考过程（来自自然语言文本）
                        if thought_content:
                            self.log_signal.emit(f"\n🧠 思考: {thought_content}")
                        else:
                            self.log_signal.emit(f"\n🧠 思考: (模型未输出思考文本)")
                        
                        action_type = action_params.get("action", "unknown")
                        self.log_signal.emit(f"⚡ 执行操作: {action_type}")
                        if "coordinate" in action_params:
                             self.log_signal.emit(f"📍 坐标: {action_params['coordinate']}")
                        if "text" in action_params:
                             self.log_signal.emit(f"⌨️ 输入: {action_params['text']}")
                        if "keys" in action_params:
                             self.log_signal.emit(f"🎹 按键: {action_params['keys']}")
                        
                        # Initialize computer use tool
                        computer_use = ComputerUse()
                        result = computer_use.call(action_params)
                        # self.log_signal.emit(f"Execution Result: {result}") # 简化输出，不再显示详细执行结果，除非出错
                        if "Error" in str(result):
                            self.log_signal.emit(f"❌ 执行错误: {result}")
                        elif "Terminated with status: success" in str(result):
                            self.log_signal.emit(f"🎉 任务完成，停止运行。")
                            self.stop() # Stop the worker loop
                            break       # Break out of the while loop immediately
                        else:
                            self.log_signal.emit(f"✅ 执行成功")
                        
                        # Small delay to let the action take effect
                        time.sleep(1)
                    else:
                        # self.log_signal.emit("No tool call found in output.") # 隐藏未找到工具调用的日志
                        time.sleep(2)
                    
                    # Save log data
                    log_data = {
                        "step": step_count,
                        "timestamp": datetime.now().isoformat(),
                        "model_output": output_text,
                        "action_data": action_data
                    }
                    
                    # Update history and save to summary file
                    action_history.append(log_data)
                    with open(os.path.join(log_dir, "action_history.json"), "w", encoding="utf-8") as f:
                        json.dump(action_history, f, indent=4, ensure_ascii=False)
                    
                    with open(os.path.join(log_dir, f"{step_prefix}_log.json"), "w", encoding="utf-8") as f:
                        json.dump(log_data, f, indent=4, ensure_ascii=False)
                    
                    # Update last screenshot path for next iteration
                    last_screenshot_path = log_screenshot_path

                except Exception as e:
                    # self.log_signal.emit(f"Error in loop iteration: {e}") # 简化错误输出
                    if "thought" in str(e):
                         self.log_signal.emit(f"⚠️ 模型未输出思考内容，将尝试无思考执行...")
                         # 即使报错也可以尝试补全 thought 并重试执行，或者暂时忽略错误
                    else:
                         self.log_signal.emit(f"❌ 循环错误: {str(e)[:100]}...") # 截断过长错误
                    time.sleep(1)

        except Exception as e:
            self.log_signal.emit(f"Worker Error: {e}")
        finally:
            self.finished_signal.emit()

class AgentGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.initUI()
        self.load_query()

    def initUI(self):
        self.setWindowTitle('Computer Agent')
        # 设置基本窗口属性
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # macOS 特定的窗口置顶和多空间显示逻辑
        if platform.system() == "Darwin":
            try:
                # 获取当前窗口 ID
                win_id = self.winId().__int__()
                
                # 获取 NSView 和 NSWindow
                ns_view = objc.objc_object(c_void_p=win_id)
                ns_window = ns_view.window()
                
                # 设置窗口可以在所有空间（Desktop）显示
                # NSWindowCollectionBehaviorCanJoinAllSpaces = 1 << 0
                # NSWindowCollectionBehaviorStationary = 1 << 4
                ns_window.setCollectionBehavior_(NSWindowCollectionBehaviorCanJoinAllSpaces | NSWindowCollectionBehaviorStationary)
                
                # 设置窗口层级为浮动层级（比普通窗口高）
                # NSFloatingWindowLevel = 3
                ns_window.setLevel_(NSFloatingWindowLevel)
                
                print("已应用 macOS 特定窗口设置：允许在所有空间显示且置顶")
            except Exception as e:
                print(f"应用 macOS 窗口设置失败（可能未安装 pyobjc）: {e}")
                # 回退方案：如果无法使用 AppKit，至少确保 Qt 属性设置正确
                # Qt.Tool 在 macOS 上通常已经有较好的置顶效果，但在全屏应用上可能受限
                pass

        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Container widget for styling
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: 10px;
                border: 1px solid #dcdcdc;
            }
        """)
        container_layout = QVBoxLayout(container)

        # Title
        title = QLabel("Computer Agent")
        title.setStyleSheet("font-weight: bold; color: #333; font-size: 14px;")
        title.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(title)

        # Query Input
        self.query_input = QTextEdit()
        self.query_input.setPlaceholderText("请输入用户指令...")
        self.query_input.setMaximumHeight(80)
        self.query_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                background-color: white;
                color: #333;
            }
        """)
        container_layout.addWidget(self.query_input)

        # Log Output Area
        self.log_output = QTextEdit()
        self.log_output.setPlaceholderText("日志输出...")
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                background-color: #f9f9f9;
                color: #555;
                font-size: 11px;
            }
        """)
        container_layout.addWidget(self.log_output)

        # Status Label
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #666; font-size: 11px;")
        self.status_label.setWordWrap(True)
        container_layout.addWidget(self.status_label)

        # Buttons
        btn_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("开始")
        self.start_btn.clicked.connect(self.start_agent)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        
        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self.stop_agent)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover { background-color: #da190b; }
            QPushButton:disabled { background-color: #cccccc; }
        """)

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        container_layout.addLayout(btn_layout)
        
        # Close button (since frameless)
        close_btn = QPushButton("退出")
        close_btn.clicked.connect(QApplication.instance().quit)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #666;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px;
                font-size: 10px;
            }
            QPushButton:hover { background-color: #555; }
        """)
        container_layout.addWidget(close_btn)

        layout.addWidget(container)
        self.setLayout(layout)

        # Set geometry (Top Right)
        screen = QDesktopWidget().screenGeometry()
        width = 400
        height = 600
        self.setGeometry(screen.width() - width - 20, 40, width, height)

    def load_query(self):
        user_query = "请点击 macOS 顶部菜单栏的微信图标，打开微信主窗口。" # Default
        try:
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_queries.json")
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    selected_id = config.get("selected_query_id")
                    for q in config.get("queries", []):
                        if q["id"] == selected_id:
                            user_query = q["query"]
                            break
        except Exception as e:
            print(f"Warning: Could not load user_queries.json: {e}")
        self.query_input.setText(user_query)

    def start_agent(self):
        query = self.query_input.toPlainText().strip()
        if not query:
            self.status_label.setText("错误：指令不能为空")
            return

        model_id = Config.MODEL_ID
        
        self.worker = ComputerAgentWorker(query, model_id)
        self.worker.log_signal.connect(self.update_log)
        self.worker.status_signal.connect(self.update_status)
        self.worker.finished_signal.connect(self.on_finished)
        
        self.worker.start()
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.query_input.setEnabled(False)
        self.status_label.setText("正在启动...")

    def stop_agent(self):
        if self.worker:
            self.worker.stop()
            self.status_label.setText("正在停止...")

    def on_finished(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.query_input.setEnabled(True)
        self.status_label.setText("代理已停止")

    def update_log(self, text):
        print(text) # Still print to console for debugging
        self.log_output.append(text)
        # Auto scroll to bottom
        cursor = self.log_output.textCursor()
        cursor.movePosition(cursor.End)
        self.log_output.setTextCursor(cursor)

    def update_status(self, text):
        self.status_label.setText(text)
        
    # Support dragging the window
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

def main():
    app = QApplication(sys.argv)
    gui = AgentGUI()
    gui.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

# The original main logic is preserved in ComputerAgentWorker logic above
def original_main():
    """
    Main function to execute GUI grounding example in a closed loop
    """
    # Load user query from config
    user_query = "请点击 macOS 顶部菜单栏的微信图标，打开微信主窗口。" # Default
    try:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_queries.json")
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            selected_id = config.get("selected_query_id")
            for q in config.get("queries", []):
                if q["id"] == selected_id:
                    user_query = q["query"]
                    print(f"Loaded query ID {selected_id}: {q.get('description', '')}")
                    break
            else:
                print(f"Warning: Query ID {selected_id} not found in config, using default.")
    except Exception as e:
        print(f"Warning: Could not load user_queries.json: {e}. Using default query.")

    # Example usage
    # user_query = "Please click on the WeChat icon in the top macOS menu bar to open the main WeChat window."
    model_id = Config.MODEL_ID
    
    print(f"Task: {user_query}")
    print("Starting closed loop agent. Press Ctrl+C to stop.")

    # Create log directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = os.path.join("logs", f"run_{timestamp}")
    os.makedirs(log_dir, exist_ok=True)
    print(f"Logging to: {log_dir}")
    
    # Initialize action history list
    action_history = []
    
    step_count = 0

    try:
        while True:
            step_count += 1
            step_prefix = f"step_{step_count:03d}"
            print(f"\n--- Step {step_count} ---")

            # 截图并保存
            screenshot_path = "imgs/screen.png"
            success, scale = capture_screen_and_save(save_path=screenshot_path)
            if not success:
                print("截图失败")
                time.sleep(1)
                continue
            
            # Save screenshot to log
            log_screenshot_path = os.path.join(log_dir, f"{step_prefix}_screen.png")
            shutil.copy(screenshot_path, log_screenshot_path)

            # screenshot = "./computer_use2.jpeg"
            # screenshot = "./test_pic_1.png"
            screenshot = screenshot_path
            
            with Image.open(screenshot) as img:
                img_width, img_height = img.size
            
            try:
                output_text, display_image = perform_gui_grounding_with_api(screenshot, user_query, model_id)

                # Display results
                print(f"Model Output: {output_text}")
                # display(display_image)
                # display_image.show()

                # Execute the action using ComputerUse
                action_data = None
                if '<tool_call>' in output_text:
                    tool_call_content = output_text.split('<tool_call>\n')[1].split('\n</tool_call>')[0]
                    action_data = json.loads(tool_call_content)
                    
                    print(f"Executing action: {action_data}")
                    
                    # Extract arguments if present
                    if 'arguments' in action_data:
                        action_params = action_data['arguments']
                    else:
                        action_params = action_data

                    # Initialize computer use tool
                    computer_use = ComputerUse()
                    result = computer_use.call(action_params)
                    print(f"Execution Result: {result}")
                    
                    # Small delay to let the action take effect
                    time.sleep(1)
                else:
                    print("No tool call found in output.")
                    time.sleep(2)
                
                # Save log data
                log_data = {
                    "step": step_count,
                    "timestamp": datetime.now().isoformat(),
                    "model_output": output_text,
                    "action_data": action_data
                }
                
                # Update history and save to summary file
                action_history.append(log_data)
                with open(os.path.join(log_dir, "action_history.json"), "w", encoding="utf-8") as f:
                    json.dump(action_history, f, indent=4, ensure_ascii=False)
                
                with open(os.path.join(log_dir, f"{step_prefix}_log.json"), "w", encoding="utf-8") as f:
                    json.dump(log_data, f, indent=4, ensure_ascii=False)

            except Exception as e:
                print(f"Error in loop iteration: {e}")
                time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopped by user.")
