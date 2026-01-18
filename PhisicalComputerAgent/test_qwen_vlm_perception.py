import os
import json
import base64
import time
from datetime import datetime
from openai import OpenAI
from PIL import Image, ImageDraw, ImageColor
import sys

# 添加当前目录到 sys.path 以确保能导入模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from transformers.models.qwen2_vl.image_processing_qwen2_vl_fast import smart_resize
except ImportError:
    # 如果导入失败，定义一个简单的替代函数或忽略缩放
    print("Warning: Could not import smart_resize. Using fallback or no resize.")
    def smart_resize(h, w, factor=32, min_pixels=3136, max_pixels=12845056):
        return h, w

from computer_agent_utils.config import Config, Utils
from computer_agent_utils.cv_utils import capture_screen_and_save

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def draw_point_with_label(image: Image.Image, point: list, label: str, color='red'):
    """在图片上绘制点和标签"""
    if isinstance(color, str):
        try:
            pil_color = ImageColor.getrgb(color)
            fill_color = pil_color + (128,)  # 半透明
            text_color = pil_color
        except ValueError:
            fill_color = (255, 0, 0, 128)
            text_color = (255, 0, 0)
    else:
        fill_color = (255, 0, 0, 128)
        text_color = (255, 0, 0)

    overlay = Image.new('RGBA', image.size, (255, 255, 255, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    # 绘制点
    radius = min(image.size) * 0.01 # 稍微小一点的点
    x, y = point 
    
    overlay_draw.ellipse(
        [(x - radius, y - radius), (x + radius, y + radius)],
        fill=fill_color,
        outline=text_color
    )
    
    # 中心点
    center_radius = radius * 0.2
    overlay_draw.ellipse(
        [(x - center_radius, y - center_radius), 
         (x + center_radius, y + center_radius)],
        fill=(0, 255, 0, 255)
    )
    
    # 绘制标签背景
    font_size = 12
    # 注意：Pillow 默认字体可能不支持中文，如果乱码可以尝试加载系统字体，这里简单处理
    text_position = (x + radius + 2, y - radius)
    
    # 简单的文本绘制
    overlay_draw.text(text_position, label, fill=text_color)

    image = image.convert('RGBA')
    combined = Image.alpha_composite(image, overlay)

    return combined.convert('RGB')

def run_perception_test():
    print("=== 开始运行 Qwen VLM 感知测试脚本 ===")
    
    # 1. 获取截图
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = os.path.join("logs", f"perception_test_{timestamp}")
    os.makedirs(log_dir, exist_ok=True)
    
    screenshot_path = os.path.join(log_dir, "screen.png")
    print(f"正在截屏，保存至 {screenshot_path}...")
    
    # 使用 cv_utils 中的截图功能
    success, _ = capture_screen_and_save(save_path=screenshot_path)
    if not success:
        print("截图失败，无法继续。")
        return

    # 2. 准备图像处理
    input_image = Image.open(screenshot_path)
    base64_image = encode_image(screenshot_path)
    
    print(f"原始图像尺寸: {input_image.width}x{input_image.height}")
    
    # 智能缩放 (保持与 agent 逻辑一致)
    min_pixels = 3136
    max_pixels = 12845056
    
    resized_height, resized_width = smart_resize(
        input_image.height,
        input_image.width,
        factor=32,
        min_pixels=min_pixels,
        max_pixels=max_pixels,
    )
    
    print(f"处理后图像尺寸: {resized_width}x{resized_height}")

    # 3. 配置 OpenAI 客户端
    client = OpenAI(
        api_key=Config.API_KEY,
        base_url=Config.API_BASE_URL,
    )

    # 4. 构建 Prompt
    # 这里的 Prompt 专门用于感知任务，不涉及 tool call
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
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                },
                {"type": "text", "text": user_query},
            ],
        }
    ]

    print("正在发送请求给 VLM 模型...")
    try:
        completion = client.chat.completions.create(
            model=Config.MODEL_ID,
            messages=messages,
            temperature=0.1, # 降低随机性
            # max_tokens=2048,
        )
        
        output_text = completion.choices[0].message.content
        print("\n=== 模型原始输出 ===")
        print(output_text)
        print("==================\n")

        # 5. 解析输出并可视化
        try:
            # 尝试清理 markdown 标记
            json_str = output_text.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.startswith("```"):
                json_str = json_str[3:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            
            elements = json.loads(json_str)
            
            if not isinstance(elements, list):
                print("错误：模型输出的不是列表格式。")
                return

            print(f"成功识别到 {len(elements)} 个元素。正在绘制可视化结果...")
            
            # 在 resize 后的尺寸上进行绘制计算（如果使用了 resize）
            # 或者直接在原图上绘制，因为坐标是归一化的
            display_image = input_image.copy() # 使用原图
            
            for i, el in enumerate(elements):
                name = el.get("element_name", "Unknown")
                etype = el.get("element_type", "Unknown")
                coord = el.get("coordinate")
                
                if coord and len(coord) == 2:
                    # 使用 Utils.normalize_to_pixel 转换坐标
                    # 注意：Utils 默认使用 Config.SCREEN_WIDTH，但我们是在图片上画，应该用图片尺寸
                    # 所以我们手动转换，参考 Utils 的逻辑
                    
                    norm_x, norm_y = coord
                    
                    # 处理幻觉绝对坐标
                    if norm_x > 1.0: norm_x /= Config.SCREENSHOT_WIDTH
                    if norm_y > 1.0: norm_y /= Config.SCREENSHOT_HEIGHT
                    
                    # 限制范围
                    norm_x = max(0.0, min(1.0, norm_x))
                    norm_y = max(0.0, min(1.0, norm_y))
                    
                    pixel_x = int(norm_x * display_image.width)
                    pixel_y = int(norm_y * display_image.height)
                    
                    label = f"{i+1}. {name}"
                    display_image = draw_point_with_label(display_image, [pixel_x, pixel_y], label)
                    
                    print(f"  - [{i+1}] {name} ({etype}): ({norm_x:.3f}, {norm_y:.3f}) -> ({pixel_x}, {pixel_y})")

            # 保存结果
            result_path = os.path.join(log_dir, "perception_result.png")
            display_image.save(result_path)
            print(f"\n可视化结果已保存至: {result_path}")
            
            # 同时也保存一份 JSON 结果
            json_path = os.path.join(log_dir, "perception_result.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(elements, f, indent=4, ensure_ascii=False)
            print(f"JSON 结果已保存至: {json_path}")

        except json.JSONDecodeError as e:
            print(f"JSON 解析失败: {e}")
            print("可能模型没有输出合法的 JSON 格式。")

    except Exception as e:
        print(f"API 调用或处理发生错误: {e}")

if __name__ == "__main__":
    run_perception_test()
