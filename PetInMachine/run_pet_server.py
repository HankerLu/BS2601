import asyncio
import logging
import json
import os
import sys
from aiohttp import web
from cat_voice_controller.core import CatVoiceController, CatCommandType

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PetServer")

# 保存所有连接的 WebSocket 客户端
connected_websockets = set()

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    logger.info("New WebSocket connection")
    connected_websockets.add(ws)
    
    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                # 可以在这里处理前端发来的消息（如果有）
                pass
            elif msg.type == web.WSMsgType.ERROR:
                logger.error(f'ws connection closed with exception {ws.exception()}')
    finally:
        connected_websockets.remove(ws)
        logger.info("WebSocket connection closed")
    
    return ws

async def index_handler(request):
    return web.FileResponse('./pet.html')

async def static_handler(request):
    # 处理静态资源 (webp 图片等)
    filename = request.match_info['filename']
    filepath = os.path.join('.', filename)
    if os.path.exists(filepath) and os.path.isfile(filepath):
        return web.FileResponse(filepath)
    return web.Response(status=404)

def broadcast_command(cmd_type: str, raw_text: str, loop):
    """
    将指令广播给所有连接的客户端
    这个函数在 ASR 线程中被调用，所以需要用 run_coroutine_threadsafe
    """
    if not connected_websockets:
        return

    message = json.dumps({
        "type": "command",
        "command": cmd_type,
        "text": raw_text
    })

    logger.info(f"Broadcasting command: {cmd_type}")

    for ws in connected_websockets:
        asyncio.run_coroutine_threadsafe(ws.send_str(message), loop)

def on_voice_command(cmd: CatCommandType, text: str):
    """
    语音控制器回调
    """
    print(f"\n[Voice] Detected: {cmd.name} (Text: {text})")
    
    # 获取主事件循环
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # 如果当前线程没有 loop (通常是 callback 线程)，我们需要引用主线程的 loop
        # 这里我们通过全局变量或者闭包传递 loop，但在 server 启动前 loop 不存在。
        # 更好的方式是在 main 中传递 loop。
        pass

async def start_server():
    app = web.Application()
    app.add_routes([
        web.get('/', index_handler),
        web.get('/ws', websocket_handler),
        web.get('/{filename}', static_handler) # 简单的静态文件服务
    ])
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    
    print("=================================================")
    print("🐱 Pet Server running at http://localhost:8080")
    print("=================================================")
    
    await site.start()
    
    # 保持运行
    while True:
        await asyncio.sleep(3600)

def main():
    # 获取事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # 定义回调函数，使用闭包捕获 loop
    def on_command(cmd: CatCommandType, text: str):
        print(f"[Callback] {cmd.name}")
        broadcast_command(cmd.name, text, loop)

    # 初始化语音控制器
    print("Initializing Voice Controller...")
    controller = CatVoiceController(on_command_callback=on_command)
    
    try:
        controller.start()
        # 运行 Web 服务器
        loop.run_until_complete(start_server())
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        controller.stop()
        loop.close()

if __name__ == "__main__":
    main()

