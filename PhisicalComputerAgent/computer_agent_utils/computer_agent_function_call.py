from typing import Union, Tuple, List
import pyautogui
import time
import platform
import os
from datetime import datetime

from qwen_agent.tools.base import BaseTool, register_tool

# Set pyautogui safety delay
pyautogui.PAUSE = 0.5
pyautogui.FAILSAFE = True

    
@register_tool("computer_use")
class ComputerUse(BaseTool):
    @property
    def description(self):
        return f"""
Use a mouse and keyboard to interact with a computer, and take screenshots.
* The current screen content you are analyzing comes from a screenshot with a resolution of 1280x831.
* This is an interface to a desktop GUI. You do not have access to a terminal or applications menu. You must click on desktop icons to start applications.
* Some applications may take time to start or process actions, so you may need to wait and take successive screenshots to see the results of your actions. E.g. if you click on Firefox and a window doesn't open, try wait and taking another screenshot.
* IMPORTANT: All coordinates (x, y) MUST be normalized values between 0.0 and 1.0, where (0.0, 0.0) is the top-left and (1.0, 1.0) is the bottom-right.
* Whenever you intend to move the cursor to click on an element like an icon, you should consult a screenshot to determine the coordinates of the element before moving the cursor.
* If you tried clicking on a program or link but it failed to load, even after waiting, try adjusting your cursor position so that the tip of the cursor visually falls on the element that you want to click.
* Make sure to click any buttons, links, icons, etc with the cursor tip in the center of the element. Don't click boxes on their edges.
""".strip()

    parameters = {
        "properties": {
            "action": {
                "description": """
The action to perform. The available actions are:
* `key`: Performs key down presses on the arguments passed in order, then performs key releases in reverse order.
* `type`: Type a string of text on the keyboard.
* `mouse_move`: Move the cursor to a specified (x, y) pixel coordinate on the screen.
* `left_click`: Click the left mouse button at a specified (x, y) pixel coordinate on the screen.
* `left_click_drag`: Click and drag the cursor to a specified (x, y) pixel coordinate on the screen.
* `right_click`: Click the right mouse button at a specified (x, y) pixel coordinate on the screen.
* `middle_click`: Click the middle mouse button at a specified (x, y) pixel coordinate on the screen.
* `double_click`: Double-click the left mouse button at a specified (x, y) pixel coordinate on the screen.
* `triple_click`: Triple-click the left mouse button at a specified (x, y) pixel coordinate on the screen (simulated as double-click since it's the closest action).
* `scroll`: Performs a scroll of the mouse scroll wheel.
* `hscroll`: Performs a horizontal scroll (mapped to regular scroll).
* `wait`: Wait specified seconds for the change to happen.
* `terminate`: Terminate the current task and report its completion status.
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
            "keys": {
                "description": "Required only by `action=key`.",
                "type": "array",
            },
            "text": {
                "description": "Required only by `action=type`.",
                "type": "string",
            },
            "coordinate": {
                "description": "(x, y): The normalized x (0.0-1.0) and y (0.0-1.0) coordinates to move the mouse to.",
                "type": "array",
            },
            "pixels": {
                "description": "The amount of scrolling to perform. Positive values scroll up, negative values scroll down. Required only by `action=scroll` and `action=hscroll`.",
                "type": "number",
            },
            "time": {
                "description": "The seconds to wait. Required only by `action=wait`.",
                "type": "number",
            },
            "status": {
                "description": "The status of the task. Required only by `action=terminate`.",
                "type": "string",
                "enum": ["success", "failure"],
            },
        },
        "required": ["action"],
        "type": "object",
    }

    def __init__(self, cfg=None):
        # 获取实际屏幕尺寸
        try:
            self.screen_width, self.screen_height = pyautogui.size()
            log_msg = f"Screen width: {self.screen_width}, Screen height: {self.screen_height}"
            print(log_msg)
            # Save to local log
            try:
                with open("screen_log.txt", "a", encoding="utf-8") as f:
                    f.write(f"{datetime.now().isoformat()} - {log_msg}\n")
            except Exception as e:
                print(f"Failed to write to screen_log.txt: {e}")
        except Exception:
            self.screen_width, self.screen_height = 1920, 1080  # Default fallback
            
        super().__init__(cfg)

    def _map_coordinates(self, x, y):
        """Map normalized coordinates (0.0-1.0) to actual screen coordinates"""
        # 模型输出是 0.0-1.0 的归一化坐标
        
        # 处理 VLM 幻觉导致的非归一化坐标
        # 如果坐标值大于1，说明模型输出的是像素坐标，需要基于截图分辨率(1280x831)进行归一化
        SCREENSHOT_WIDTH = 1280
        SCREENSHOT_HEIGHT = 831
        
        if x > 1.0:
            x = x / SCREENSHOT_WIDTH
        if y > 1.0:
            y = y / SCREENSHOT_HEIGHT

        # 直接映射到实际屏幕分辨率
        real_x = int(x * self.screen_width)
        real_y = int(y * self.screen_height)
        
        # 边界检查
        safe_margin = 5  # 距离边缘5像素的安全边距
        real_x = max(safe_margin, min(real_x, self.screen_width - safe_margin))
        real_y = max(safe_margin, min(real_y, self.screen_height - safe_margin))
        
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
