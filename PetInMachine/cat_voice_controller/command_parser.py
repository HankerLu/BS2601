from typing import Optional, Dict, List, Tuple
from enum import Enum
import logging

logger = logging.getLogger("CommandParser")

class CatCommandType(Enum):
    MEOW = "meow"           # 猫叫声
    WAKE_UP = "wake_up"     # 唤醒/名字
    SIT = "sit"             # 坐下
    STAND = "stand"         # 站起来/起立
    COME = "come"           # 过来
    LICK = "lick"           # 舔毛
    STOP = "stop"           # 停止
    UNKNOWN = "unknown"     # 未知

class CommandParser:
    def __init__(self, cat_names: List[str] = None):
        if cat_names is None:
            cat_names = ["咪咪", "小猫", "kitty", "cat"]
        self.cat_names = cat_names
        
        # 定义指令关键词映射
        # 关键词 -> 指令类型
        self.command_map: Dict[CatCommandType, List[str]] = {
            CatCommandType.MEOW: ["喵", "呜", "meow"],
            CatCommandType.SIT: ["坐下", "坐", "sit", "蹲下"],
            CatCommandType.STAND: ["站起来", "起立", "站好", "stand"],
            CatCommandType.COME: ["过来", "来", "come", "过来一下"],
            CatCommandType.LICK: ["舔", "舔毛", "lick", "洗脸"],
            CatCommandType.STOP: ["停", "停止", "别动", "stop", "安静"],
        }

    def parse(self, text: str) -> Tuple[CatCommandType, str]:
        """
        解析文本中的指令
        返回: (指令类型, 原始匹配文本)
        """
        if not text:
            return CatCommandType.UNKNOWN, ""
            
        text_lower = text.lower()
        # print(f"Parsed text: {text_lower}")
        
        # 1. 检查是否在叫名字 (唤醒词)
        for name in self.cat_names:
            if name.lower() in text_lower:
                # logger.info(f"Detected wake word: {name}")  <-- 移除或改为 debug
                logger.debug(f"Detected wake word: {name}")
                # 如果只有名字，返回唤醒；如果名字后跟指令，优先处理指令但标记上下文可能比较好
                # 这里简单处理：如果包含指令则返回指令，否则返回唤醒
                command, match = self._find_command_in_text(text_lower)
                if command != CatCommandType.UNKNOWN:
                    return command, match
                return CatCommandType.WAKE_UP, name

        # 2. 检查普通指令
        return self._find_command_in_text(text_lower)

    def _find_command_in_text(self, text: str) -> Tuple[CatCommandType, str]:
        for cmd_type, keywords in self.command_map.items():
            for keyword in keywords:
                if keyword in text:
                    return cmd_type, keyword
        return CatCommandType.UNKNOWN, ""

