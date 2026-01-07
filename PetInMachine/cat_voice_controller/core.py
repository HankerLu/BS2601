import logging
import time
import sys
import os
from typing import Callable, Optional

# 尝试导入上层目录的 ASR 引擎
# 假设运行目录是项目根目录
try:
    from realtime_asr_engine import VolcASRClient, AudioRecorder
except ImportError:
    # 如果作为包导入失败，尝试添加父目录到 path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        from realtime_asr_engine import VolcASRClient, AudioRecorder
    except ImportError:
        print("Error: Could not import realtime_asr_engine. Make sure you are in the project root.")
        raise

from .config import VOLC_APP_KEY, VOLC_ACCESS_KEY, VOLC_ASR_URL, DEBUG
from .command_parser import CommandParser, CatCommandType

# 配置日志
logging.basicConfig(level=logging.INFO if DEBUG else logging.WARNING, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("CatVoiceController")

class CatVoiceController:
    def __init__(self, on_command_callback: Callable[[CatCommandType, str], None] = None):
        """
        初始化猫语音控制器
        :param on_command_callback: 当识别到指令时的回调函数 func(command_type, raw_text)
        """
        self.parser = CommandParser()
        self.on_command_callback = on_command_callback
        
        # 初始化 ASR 客户端
        self.asr_client = VolcASRClient(
            app_key=VOLC_APP_KEY, 
            access_key=VOLC_ACCESS_KEY, 
            on_result_callback=self._on_asr_result, 
            on_error_callback=self._on_asr_error,
            url=VOLC_ASR_URL
        )
        
        # 初始化录音机
        self.recorder = AudioRecorder(self.asr_client.push_audio)
        
        self.is_running = False
        self.last_triggered_cmd = None # 用于去重，防止同一句话重复触发相同指令
        self.processed_text_length = 0 # 记录当前句子已处理的长度，避免重复解析

    def start(self):
        """启动控制器"""
        if self.is_running:
            return
        
        logger.info("Starting Cat Voice Controller...")
        self.last_triggered_cmd = None
        self.processed_text_length = 0
        self.asr_client.start()
        self.recorder.start()
        self.is_running = True
        logger.info("Controller started. Listening for commands...")

    def stop(self):
        """停止控制器"""
        if not self.is_running:
            return
            
        logger.info("Stopping Cat Voice Controller...")
        self.recorder.stop()
        self.asr_client.stop()
        self.is_running = False
        logger.info("Controller stopped.")

    def _on_asr_result(self, text: str, is_final: bool):
        """
        ASR 结果回调
        """
        log_prefix = "[Final]" if is_final else "[Partial]"
        logger.debug(f"ASR Result {log_prefix}: {text}")

        if not text:
            return

        # 增量解析逻辑：
        # 1. 只有比上次处理过的更长的部分才可能是新指令
        # 2. 如果 text 长度小于 processed_text_length，说明 ASR 可能修正了前面的内容，暂时重置或保守处理
        #    这里简化处理：如果 text 变短了，说明前面的识别可能有误，我们重置 index
        
        current_len = len(text)
        if current_len < self.processed_text_length:
            self.processed_text_length = 0
            
        # 截取新内容 (增量部分)
        # 注意：为了避免切断词语，稍微回退一点点可能更安全，但作为 Demo 先直接切片
        new_content = text[self.processed_text_length:]
        
        if not new_content:
            if is_final:
                # 句子结束，重置状态
                self.last_triggered_cmd = None
                self.processed_text_length = 0
            return

        # 解析指令 (只解析新内容)
        cmd_type, keyword = self.parser.parse(new_content)
        
        if cmd_type != CatCommandType.UNKNOWN:
            # 只有当新内容里真的有指令时，才触发
            # 移除了 last_triggered_cmd 检查，现在只要有新指令就触发
            logger.info(f"Command Detected: {cmd_type.name} (keyword: {keyword})")
            self.last_triggered_cmd = cmd_type
            
            # 触发回调
            if self.on_command_callback:
                self.on_command_callback(cmd_type, text) # 依然传完整 text 供调试
                
            # 关键：一旦识别出指令，就认为这段文本已经被消费了
            # 更新 processed_text_length 到当前位置，避免下次再解析这段
            self.processed_text_length = current_len

        # 如果是 Final 包，无论如何都要重置状态，为下一句话做准备
        if is_final:
            self.last_triggered_cmd = None
            self.processed_text_length = 0
            if cmd_type == CatCommandType.UNKNOWN:
                logger.debug(f"No command detected in final: {text}")

    def _on_asr_error(self, error_msg: str):
        logger.error(f"ASR Error: {error_msg}")

if __name__ == "__main__":
    # 简单的测试运行逻辑
    def test_callback(cmd: CatCommandType, text: str):
        print(f"\n>>> 触发指令: {cmd.name} (来源: {text})")
        if cmd == CatCommandType.MEOW:
            print(">>> 电子猫: 喵喵喵~")
        elif cmd == CatCommandType.SIT:
            print(">>> 电子猫: 正在坐下...")
        elif cmd == CatCommandType.WAKE_UP:
            print(">>> 电子猫: 歪头看你...")

    controller = CatVoiceController(on_command_callback=test_callback)
    
    try:
        controller.start()
        print("Listening... Press Ctrl+C to stop.")
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        controller.stop()

