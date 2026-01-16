from typing import Union, Tuple, List
import pyautogui
import time
import platform
import os
from datetime import datetime

from qwen_agent.tools.base import BaseTool, register_tool

from computer_agent_utils.config import Config, Utils

# Set pyautogui safety delay
pyautogui.PAUSE = 0.5
pyautogui.FAILSAFE = True

    
@register_tool("computer_use")
class ComputerUse(BaseTool):
    @property
    def description(self):
        return f"""
使用鼠标和键盘与电脑进行交互，并截取屏幕截图。
* 你正在分析的当前屏幕内容来自一张分辨率为 {Config.SCREENSHOT_WIDTH}x{Config.SCREENSHOT_HEIGHT} 的截图。
* 这是一个桌面 GUI 界面。你没有终端或应用程序菜单的访问权限。你必须点击桌面图标来启动应用程序。
* 某些应用程序可能需要时间启动或处理操作，因此你可能需要等待并连续截图以查看操作结果。例如，如果你点击了 Firefox 但窗口没有打开，请尝试等待并再次截图。
* 重要：所有坐标 (x, y) 必须是 0.0 到 1.0 之间的归一化值，其中 (0.0, 0.0) 是左上角，(1.0, 1.0) 是右下角。
* 每当你打算移动光标点击像图标这样的元素时，你应该在移动光标之前参考截图来确定元素的坐标。
* 如果你尝试点击程序或链接但加载失败，即使在等待后也是如此，请尝试调整你的光标位置，使光标尖端在视觉上落在你想要点击的元素上。
* 确保用光标尖端点击任何按钮、链接、图标等的中心。不要点击框的边缘。
""".strip()

    parameters = {
        "properties": {
            "action": {
                "description": """
要执行的操作。可用的操作包括：
* `key`：按顺序按下参数中传入的按键，然后按相反顺序释放按键。
* `type`：在键盘上输入一串文本。
* `mouse_move`：将光标移动到屏幕上指定的 (x, y) 像素坐标。
* `left_click`：在屏幕上指定的 (x, y) 像素坐标处单击鼠标左键。
* `left_click_drag`：点击并将光标拖动到屏幕上指定的 (x, y) 像素坐标。
* `right_click`：在屏幕上指定的 (x, y) 像素坐标处单击鼠标右键。
* `middle_click`：在屏幕上指定的 (x, y) 像素坐标处单击鼠标中键。
* `double_click`：在屏幕上指定的 (x, y) 像素坐标处双击鼠标左键。
* `triple_click`：在屏幕上指定的 (x, y) 像素坐标处三击鼠标左键（模拟为双击，因为它是最接近的操作）。
* `scroll`：执行鼠标滚轮滚动。
* `hscroll`：执行水平滚动（映射到常规滚动）。
* `wait`：等待指定的秒数以使更改发生。
* `terminate`：终止当前任务并报告其完成状态。
""".strip(),
                "enum": [
                    "key",
                    "type",
                    "mouse_move",
                    "left_click",
                    "left_click_drag",
                    "right_click",
                    "middle_click",
                    "double_click",
                    "triple_click",
                    "scroll",
                    "hscroll",
                    "wait",
                    "terminate",
                ],
                "type": "string",
            },
            "thought": {
                "description": "简要描述你进行此操作的思路和原因，例如“我看到了微信图标，所以点击它以打开应用”",
                "type": "string",
            },
            "keys": {
                "description": "仅在 `action=key` 时需要。",
                "type": "array",
            },
            "text": {
                "description": "仅在 `action=type` 时需要。",
                "type": "string",
            },
            "coordinate": {
                "description": "(x, y): 移动鼠标到的归一化 x (0.0-1.0) 和 y (0.0-1.0) 坐标。",
                "type": "array",
            },
            "pixels": {
                "description": "要滚动的像素量。正值向上滚动，负值向下滚动。仅在 `action=scroll` 和 `action=hscroll` 时需要。",
                "type": "number",
            },
            "time": {
                "description": "等待的秒数。仅在 `action=wait` 时需要。",
                "type": "number",
            },
            "status": {
                "description": "任务的状态。仅在 `action=terminate` 时需要。",
                "type": "string",
                "enum": ["success", "failure"],
            },
        },
        "required": ["action"],
        "type": "object",
    }

    def __init__(self, cfg=None):
        # 获取实际屏幕尺寸
        self.screen_width = Config.SCREEN_WIDTH
        self.screen_height = Config.SCREEN_HEIGHT
        
        log_msg = f"Screen width: {self.screen_width}, Screen height: {self.screen_height}"
        print(log_msg)
        # Save to local log
        try:
            with open("screen_log.txt", "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()} - {log_msg}\n")
        except Exception as e:
            print(f"Failed to write to screen_log.txt: {e}")
            
        super().__init__(cfg)

    def _map_coordinates(self, x, y):
        """Map normalized coordinates (0.0-1.0) to actual screen coordinates"""
        # 使用统一的 Utils 进行转换
        real_x, real_y = Utils.normalize_to_pixel(x, y, self.screen_width, self.screen_height)
        
        # 边界检查
        real_x, real_y = Utils.ensure_safe_coordinates(real_x, real_y)
        
        return real_x, real_y

    def call(self, params: Union[str, dict], **kwargs):
        params = self._verify_json_format_args(params)
        action = params["action"]
        
        try:
            if action in ["left_click", "right_click", "middle_click", "double_click", "triple_click"]:
                return self._mouse_click(action, params.get("coordinate"))
            elif action == "key":
                return self._key(params.get("keys", []))
            elif action == "type":
                return self._type(params.get("text", ""))
            elif action == "mouse_move":
                return self._mouse_move(params.get("coordinate"))
            elif action == "left_click_drag":
                return self._left_click_drag(params.get("coordinate"))
            elif action == "scroll":
                return self._scroll(params.get("pixels", 0))
            elif action == "hscroll":
                return self._hscroll(params.get("pixels", 0))
            elif action == "wait":
                return self._wait(params.get("time", 0.5))
            elif action == "terminate":
                return self._terminate(params.get("status", "success"))
            else:
                raise ValueError(f"Invalid action: {action}")
        except Exception as e:
            return f"Error executing action {action}: {str(e)}"

    def _mouse_click(self, button_action: str, coordinate: Tuple[int, int] = None):
        if coordinate:
            real_x, real_y = self._map_coordinates(coordinate[0], coordinate[1])
            pyautogui.moveTo(real_x, real_y)
            
        button_map = {
            "left_click": "left",
            "right_click": "right",
            "middle_click": "middle",
            "double_click": "left",
            "triple_click": "left"
        }
        
        btn = button_map.get(button_action, "left")
        
        if button_action == "double_click":
            pyautogui.doubleClick(button=btn)
        elif button_action == "triple_click":
            pyautogui.tripleClick(button=btn)
        else:
            pyautogui.click(button=btn)
            
        return f"Performed {button_action} at {coordinate if coordinate else 'current position'}"

    def _key(self, keys: List[str]):
        # 处理按键映射，pyautogui 的键名可能与传入的不同
        # 这里假设 keys 是 standard keys
        for key in keys:
            # 特殊处理 mac 的 command 键
            if key.lower() in ["meta", "super", "command", "cmd"]:
                if platform.system() == "Darwin":
                    key = "command"
                else:
                    key = "win" # Windows key
            
            pyautogui.press(key)
        return f"Pressed keys: {keys}"

    def _type(self, text: str):
        pyautogui.write(text, interval=0.01)
        return f"Typed text: {text}"

    def _mouse_move(self, coordinate: Tuple[int, int]):
        if coordinate:
            real_x, real_y = self._map_coordinates(coordinate[0], coordinate[1])
            pyautogui.moveTo(real_x, real_y)
            return f"Moved mouse to {coordinate}"
        return "No coordinate provided for move"

    def _left_click_drag(self, coordinate: Tuple[int, int]):
        if coordinate:
            real_x, real_y = self._map_coordinates(coordinate[0], coordinate[1])
            pyautogui.dragTo(real_x, real_y, button='left')
            return f"Dragged mouse to {coordinate}"
        return "No coordinate provided for drag"

    def _scroll(self, pixels: int):
        # pyautogui scroll amounts differ by OS
        # On Mac, scroll amount is small?
        if pixels:
            pyautogui.scroll(int(pixels))
            return f"Scrolled {pixels} pixels"
        return "No scroll amount provided"

    def _hscroll(self, pixels: int):
        if pixels:
            # Windows/Linux doesn't strictly support hscroll in base pyautogui without specific drivers sometimes, 
            # but usually hscroll() exists for horizontal
            try:
                pyautogui.hscroll(int(pixels))
                return f"Horizontally scrolled {pixels} pixels"
            except AttributeError:
                return "Horizontal scroll not supported on this platform/pyautogui version"
        return "No hscroll amount provided"

    def _wait(self, time_sec: float):
        time.sleep(time_sec)
        return f"Waited {time_sec} seconds"

    def _terminate(self, status: str):
        print(f"TERMINATING TASK: {status}")
        return f"Terminated with status: {status}"
