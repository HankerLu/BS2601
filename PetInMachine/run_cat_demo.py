import time
from cat_voice_controller.core import CatVoiceController, CatCommandType

def on_command(cmd: CatCommandType, text: str):
    print(f"\n[DEMO] 收到指令: {cmd.value} (原文: {text})")
    
    # 这里是具体的控制逻辑实现接口
    if cmd == CatCommandType.MEOW:
        print(" -> 动作: 播放猫叫音效")
    elif cmd == CatCommandType.SIT:
        print(" -> 动作: 执行坐下舵机指令")
    elif cmd == CatCommandType.STAND:
        print(" -> 动作: 执行站立舵机指令")
    elif cmd == CatCommandType.COME:
        print(" -> 动作: 向声源移动")
    elif cmd == CatCommandType.WAKE_UP:
        print(" -> 动作: 唤醒并进入指令接收模式")
    elif cmd == CatCommandType.STOP:
        print(" -> 动作: 紧急停止所有运动")

def main():
    print("正在初始化电子猫语音控制器...")
    controller = CatVoiceController(on_command_callback=on_command)
    
    try:
        controller.start()
        print("系统就绪。请说话... (尝试说: '咪咪', '坐下', '喵')")
        print("按 Ctrl+C 退出")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n用户退出")
    finally:
        controller.stop()

if __name__ == "__main__":
    main()

