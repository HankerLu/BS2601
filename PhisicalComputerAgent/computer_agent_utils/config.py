import os
import platform
import pyautogui

class Config:
    # API Configuration
    # 建议使用环境变量，如果不存在则使用默认值（这里暂时保留硬编码作为默认值，但建议用户修改）
    API_KEY = os.environ.get("DASHSCOPE_API_KEY", "sk-5171c051fdbc42bd96d466d7158ff2f0")
    API_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    MODEL_ID = "qwen-vl-max-latest"
    
    # Screen Configuration
    try:
        SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()
    except Exception:
        SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080 # Fallback
        
    # Screenshot Configuration (The resolution fed to the VLM)
    # 某些VLM模型可能基于特定的截图分辨率输出坐标，这里保留原有逻辑中的参考分辨率
    # 如果截图被 resize 了，这里需要对应调整。
    # 目前代码中截图虽然 resize，但 VLM 是基于图像理解，通常输出归一化坐标。
    # 下面的常量用于处理模型偶尔输出绝对像素坐标（基于截图尺寸）的情况。
    SCREENSHOT_WIDTH = 1280
    SCREENSHOT_HEIGHT = 831

class Utils:
    @staticmethod
    def normalize_to_pixel(x, y, target_width=None, target_height=None):
        """
        将归一化坐标 (0.0-1.0) 转换为目标分辨率的像素坐标。
        同时也处理模型幻觉输出绝对坐标的情况（如果 > 1.0，则先归一化）。
        
        Args:
            x (float): x 坐标
            y (float): y 坐标
            target_width (int, optional): 目标宽度。默认为真实屏幕宽度。
            target_height (int, optional): 目标高度。默认为真实屏幕高度。
            
        Returns:
            tuple: (int, int) 实际像素坐标 (x, y)
        """
        if target_width is None:
            target_width = Config.SCREEN_WIDTH
        if target_height is None:
            target_height = Config.SCREEN_HEIGHT
            
        # 1. 处理 VLM 幻觉导致的非归一化坐标 (假设是基于 SCREENSHOT_WIDTH/HEIGHT 的绝对坐标)
        if x > 1.0:
            x = x / Config.SCREENSHOT_WIDTH
        if y > 1.0:
            y = y / Config.SCREENSHOT_HEIGHT
            
        # 2. 限制范围在 0.0 - 1.0 之间 (容错)
        x = max(0.0, min(1.0, x))
        y = max(0.0, min(1.0, y))
        
        # 3. 映射到目标分辨率
        real_x = int(x * target_width)
        real_y = int(y * target_height)
        
        return real_x, real_y

    @staticmethod
    def ensure_safe_coordinates(x, y, margin=5):
        """确保坐标在屏幕安全范围内"""
        x = max(margin, min(x, Config.SCREEN_WIDTH - margin))
        y = max(margin, min(y, Config.SCREEN_HEIGHT - margin))
        return x, y
