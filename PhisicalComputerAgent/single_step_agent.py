import os
import json
import base64
import argparse
import time
from datetime import datetime
from PIL import Image, ImageDraw
from openai import OpenAI

# 复用现有的工具类
from qwen_agent.llm.fncall_prompts.nous_fncall_prompt import (
    NousFnCallPrompt,
    Message,
    ContentItem,
)
from computer_agent_utils.computer_agent_function_call import ComputerUse

def encode_image(image_path):
    """将图片编码为Base64"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def draw_visualization(image_path, action_data, output_path):
    """
    在图片上可视化操作坐标 (画框)
    """
    try:
        img = Image.open(image_path)
        img_width, img_height = img.size
        draw = ImageDraw.Draw(img)
        
        # 检查是否有坐标信息
        coordinate = None
        if 'arguments' in action_data:
             args = action_data['arguments']
             if 'coordinate' in args:
                 coordinate = args['coordinate']
        elif 'coordinate' in action_data:
             coordinate = action_data['coordinate']
             
        if coordinate:
            # 模型输出的是 0.0-1.0 的归一化坐标
            norm_x, norm_y = coordinate
            
            # 映射回真实分辨率
            abs_x = norm_x * img_width
            abs_y = norm_y * img_height
            
            # 画一个红色的框 (20x20像素)
            box_size = 20
            x1 = abs_x - box_size // 2
            y1 = abs_y - box_size // 2
            x2 = abs_x + box_size // 2
            y2 = abs_y + box_size // 2
            
            # 绘制矩形框，红色，线宽3
            draw.rectangle([x1, y1, x2, y2], outline="red", width=3)
            
            # 绘制中心点
            draw.ellipse([abs_x-2, abs_y-2, abs_x+2, abs_y+2], fill="green")
            
            print(f"Mapped coordinates: ({norm_x}, {norm_y}) -> ({abs_x:.1f}, {abs_y:.1f})")
        
        # 保存可视化图片
        img.save(output_path)
        print(f"Visualization saved to: {output_path}")
        return True
        
    except Exception as e:
        print(f"Error during visualization: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run a single step test for Qwen-VL Computer Agent")
    parser.add_argument("--image", required=True, help="Path to the local image file")
    parser.add_argument("--query", default="Please click on the WeChat icon", help="User instruction query")
    parser.add_argument("--output_dir", default="test_results", help="Directory to save logs and images")
    
    args = parser.parse_args()
    
    # 检查图片是否存在
    if not os.path.exists(args.image):
        print(f"Error: Image file not found at {args.image}")
        return

    # 创建输出目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(args.output_dir, f"run_{timestamp}")
    os.makedirs(run_dir, exist_ok=True)
    
    print(f"--- Starting Single Step Test ---")
    print(f"Image: {args.image}")
    print(f"Query: {args.query}")
    print(f"Output Directory: {run_dir}")

    # 1. 准备图片数据
    base64_image = encode_image(args.image)
    
    # 自动检测格式
    file_ext = os.path.splitext(args.image)[1].lower()
    image_type = 'png' if file_ext == '.png' else 'jpeg'
    if file_ext == '.webp': image_type = 'webp'

    # 2. 初始化 API Client (复用 main.py 中的配置)
    client = OpenAI(
        # 使用代码库中现有的 Key
        api_key='sk-5171c051fdbc42bd96d466d7158ff2f0',
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    
    model_id = "qwen-vl-max-latest"

    # 3. 构建 Prompt
    # 初始化 ComputerUse 工具定义
    computer_use = ComputerUse()

    # 构建 System Message
    system_message = NousFnCallPrompt().preprocess_fncall_messages(
        messages=[
            Message(role="system", content=[ContentItem(text="You are a helpful assistant.")]),
        ],
        functions=[computer_use.function],
        lang=None,
    )
    system_message = system_message[0].model_dump()

    messages = [
        {
            "role": "system",
            "content": [
                {"type": "text", "text": msg["text"]} for msg in system_message["content"]
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/{image_type};base64,{base64_image}"},
                },
                {"type": "text", "text": args.query},
            ],
        }
    ]

    print("Sending request to Qwen-VL...")
    start_time = time.time()
    
    try:
        completion = client.chat.completions.create(
            model=model_id,
            messages=messages,
        )
        duration = time.time() - start_time
        print(f"Request completed in {duration:.2f} seconds.")

        output_text = completion.choices[0].message.content
        print(f"\nModel Output Raw:\n{output_text}\n")

        # 4. 解析结果 & 日志记录
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "image_path": args.image,
            "query": args.query,
            "raw_output": output_text,
            "parsed_action": None
        }

        # 解析 <tool_call>
        action_data = None
        if '<tool_call>' in output_text:
            try:
                tool_call_content = output_text.split('<tool_call>\n')[1].split('\n</tool_call>')[0]
                action_data = json.loads(tool_call_content)
                log_data["parsed_action"] = action_data
                print(f"Parsed Action: {json.dumps(action_data, indent=2)}")
                
                # 5. 可视化 (如果涉及坐标)
                vis_filename = f"result_vis.png"
                vis_path = os.path.join(run_dir, vis_filename)
                
                # 尝试可视化
                draw_visualization(args.image, action_data, vis_path)
                
            except Exception as e:
                print(f"Error parsing tool call: {e}")
                log_data["parse_error"] = str(e)
        else:
            print("No tool_call found in output.")

        # 保存日志
        log_path = os.path.join(run_dir, "log.json")
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=4, ensure_ascii=False)
        print(f"Log saved to: {log_path}")

    except Exception as e:
        print(f"Critical Error: {e}")

if __name__ == "__main__":
    main()
