from typing import Union, Tuple, List
import pyautogui
import time
import platform
import os

from qwen_agent.tools.base import BaseTool, register_tool

# Set pyautogui safety delay
pyautogui.PAUSE = 0.5
pyautogui.FAILSAFE = True

@register_tool("mobile_use")
class MobileUse(BaseTool):
    @property
    def description(self):
        return f"""
Use a touchscreen to interact with a mobile device, and take screenshots.
* This is an interface to a mobile device with touchscreen. You can perform actions like clicking, typing, swiping, etc.
* Some applications may take time to start or process actions, so you may need to wait and take successive screenshots to see the results of your actions.
* The screen's resolution is {self.display_width_px}x{self.display_height_px}.
* Make sure to click any buttons, links, icons, etc with the cursor tip in the center of the element. Don't click boxes on their edges unless asked.
""".strip()

    parameters = {
        "properties": {
            "action": {
                "description": """
The action to perform. The available actions are:
* `key`: Perform a key event on the mobile device.
    - This supports adb's `keyevent` syntax.
    - Examples: "volume_up", "volume_down", "power", "camera", "clear".
* `click`: Click the point on the screen with coordinate (x, y).
* `long_press`: Press the point on the screen with coordinate (x, y) for specified seconds.
* `swipe`: Swipe from the starting point with coordinate (x, y) to the end point with coordinates2 (x2, y2).
* `type`: Input the specified text into the activated input box.
* `system_button`: Press the system button.
* `open`: Open an app on the device.
* `wait`: Wait specified seconds for the change to happen.
* `terminate`: Terminate the current task and report its completion status.
""".strip(),
                "enum": [
                    "key",
                    "click",
                    "long_press",
                    "swipe",
                    "type",
                    "system_button",
                    "open",
                    "wait",
                    "terminate",
                ],
                "type": "string",
            },
            "coordinate": {
                "description": "(x, y): The x (pixels from the left edge) and y (pixels from the top edge) coordinates to move the mouse to. Required only by `action=click`, `action=long_press`, and `action=swipe`.",
                "type": "array",
            },
            "coordinate2": {
                "description": "(x, y): The x (pixels from the left edge) and y (pixels from the top edge) coordinates to move the mouse to. Required only by `action=swipe`.",
                "type": "array",
            },
            "text": {
                "description": "Required only by `action=key`, `action=type`, and `action=open`.",
                "type": "string",
            },
            "time": {
                "description": "The seconds to wait. Required only by `action=long_press` and `action=wait`.",
                "type": "number",
            },
            "button": {
                "description": "Back means returning to the previous interface, Home means returning to the desktop, Menu means opening the application background menu, and Enter means pressing the enter. Required only by `action=system_button`",
                "enum": [
                    "Back",
                    "Home",
                    "Menu",
                    "Enter",
                ],
                "type": "string",
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
        self.display_width_px = cfg["display_width_px"]
        self.display_height_px = cfg["display_height_px"]
        super().__init__(cfg)

    def call(self, params: Union[str, dict], **kwargs):
        params = self._verify_json_format_args(params)
        action = params["action"]
        if action == "key":
            return self._key(params["text"])
        elif action == "click":
            return self._click(
                coordinate=params["coordinate"]
            )
        elif action == "long_press":
            return self._long_press(
                coordinate=params["coordinate"], time=params["time"]
            )
        elif action == "swipe":
            return self._swipe(
                coordinate=params["coordinate"], coordinate2=params["coordinate2"]
            )
        elif action == "type":
            return self._type(params["text"])
        elif action == "system_button":
            return self._system_button(params["button"])
        elif action == "open":
            return self._open(params["text"])
        elif action == "wait":
            return self._wait(params["time"])
        elif action == "terminate":
            return self._terminate(params["status"])
        else:
            raise ValueError(f"Unknown action: {action}")

    def _key(self, text: str):
        raise NotImplementedError()
        
    def _click(self, coordinate: Tuple[int, int]):
        raise NotImplementedError()

    def _long_press(self, coordinate: Tuple[int, int], time: int):
        raise NotImplementedError()

    def _swipe(self, coordinate: Tuple[int, int], coordinate2: Tuple[int, int]):
        raise NotImplementedError()

    def _type(self, text: str):
        raise NotImplementedError()

    def _system_button(self, button: str):
        raise NotImplementedError()

    def _open(self, text: str):
        raise NotImplementedError()

    def _wait(self, time: int):
        raise NotImplementedError()

    def _terminate(self, status: str):
        raise NotImplementedError()
    
@register_tool("computer_use")
class ComputerUse(BaseTool):
    @property
    def description(self):
        return f"""
Use a mouse and keyboard to interact with a computer, and take screenshots.
* This is an interface to a desktop GUI. You do not have access to a terminal or applications menu. You must click on desktop icons to start applications.
* Some applications may take time to start or process actions, so you may need to wait and take successive screenshots to see the results of your actions. E.g. if you click on Firefox and a window doesn't open, try wait and taking another screenshot.
* The screen's resolution is {self.display_width_px}x{self.display_height_px}.
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
* `answer`: Answer a question.
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
                    "answer",
                ],
                "type": "string",
            },
            "keys": {
                "description": "Required only by `action=key`.",
                "type": "array",
            },
            "text": {
                "description": "Required only by `action=type` and `action=answer`.",
                "type": "string",
            },
            "coordinate": {
                "description": "(x, y): The x (pixels from the left edge) and y (pixels from the top edge) coordinates to move the mouse to.",
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
        self.display_width_px = cfg["display_width_px"]
        self.display_height_px = cfg["display_height_px"]
        
        # 获取实际屏幕尺寸
        try:
            self.screen_width, self.screen_height = pyautogui.size()
        except Exception:
            self.screen_width, self.screen_height = 1920, 1080  # Default fallback
            
        super().__init__(cfg)

    def _map_coordinates(self, x, y):
        """Map normalized coordinates (if model uses them) or logical coordinates to actual screen coordinates"""
        # 如果模型输出是基于 1000x1000 的归一化坐标，这里需要映射
        # 假设传入的 x, y 是基于 self.display_width_px, self.display_height_px 的
        
        # 计算比例
        scale_x = self.screen_width / self.display_width_px
        scale_y = self.screen_height / self.display_height_px
        
        real_x = int(x * scale_x)
        real_y = int(y * scale_y)
        
        # 边界检查
        real_x = max(0, min(real_x, self.screen_width - 1))
        real_y = max(0, min(real_y, self.screen_height - 1))
        
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
            elif action == "answer":
                return self._answer(params.get("text", ""))
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

    def _answer(self, text: str):
        print(f"ANSWER: {text}")
        return f"Answered: {text}"

    def _wait(self, time_sec: float):
        time.sleep(time_sec)
        return f"Waited {time_sec} seconds"

    def _terminate(self, status: str):
        print(f"TERMINATING TASK: {status}")
        return f"Terminated with status: {status}"
