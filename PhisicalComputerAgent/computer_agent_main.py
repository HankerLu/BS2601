import os
import json
import base64
import time
import shutil
from datetime import datetime
from openai import OpenAI
from PIL import Image
from qwen_agent.llm.fncall_prompts.nous_fncall_prompt import (
    NousFnCallPrompt,
    Message,
    ContentItem,
)
from transformers.models.qwen2_vl.image_processing_qwen2_vl_fast import smart_resize

from computer_agent_utils.computer_agent_function_call import ComputerUse
from computer_agent_utils.cv_utils import capture_screen_and_save

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def perform_gui_grounding_with_api(screenshot_path, user_query, model_id, min_pixels=3136, max_pixels=12845056):
    """
    Perform GUI grounding using Qwen model to interpret user query on a screenshot.
    
    Args:
        screenshot_path (str): Path to the screenshot image
        user_query (str): User's query/instruction
        model: Preloaded Qwen model
        min_pixels: Minimum pixels for the image
        max_pixels: Maximum pixels for the image
        
    Returns:
        tuple: (output_text, display_image) - Model's output text and annotated image
    """

    # Open and process image
    input_image = Image.open(screenshot_path)
    base64_image = encode_image(screenshot_path)
    
    # Auto-detect image format from file extension
    file_ext = os.path.splitext(screenshot_path)[1].lower()
    if file_ext == '.png':
        image_type = 'png'
    elif file_ext in ['.jpg', '.jpeg']:
        image_type = 'jpeg'
    elif file_ext == '.webp':
        image_type = 'webp'
    else:
        image_type = 'jpeg'  # Default to jpeg if unknown
    
    client = OpenAI(
        #If the environment variable is not configured, please replace the following line with the Dashscope API Key: api_key="sk-xxx". Access via https://bailian.console.alibabacloud.com/?apiKey=1 "
        api_key='sk-5171c051fdbc42bd96d466d7158ff2f0',
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    resized_height, resized_width = smart_resize(
        input_image.height,
        input_image.width,
        factor=32,
        min_pixels=min_pixels,
        max_pixels=max_pixels,
    )
    
    # Initialize computer use function
    img_width, img_height = input_image.size
    computer_use = ComputerUse(
        cfg={"display_width_px": img_width, "display_height_px": img_height}
    )

    # Build messages
    system_message = NousFnCallPrompt().preprocess_fncall_messages(
        messages=[
            Message(role="system", content=[ContentItem(text="You are a helpful assistant.")]),
        ],
        functions=[computer_use.function],
        lang=None,
    )
    system_message = system_message[0].model_dump()
    messages=[
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
                    # "min_pixels": 1024,
                    # "max_pixels": max_pixels,
                    # Pass in BASE64 image data. Note that the image format (i.e., image/{format}) must match the Content Type in the list of supported images. "f" is the method for string formatting.
                    # PNG image:  f"data:image/png;base64,{base64_image}"
                    # JPEG image: f"data:image/jpeg;base64,{base64_image}"
                    # WEBP image: f"data:image/webp;base64,{base64_image}"
                    # Auto-detected format based on file extension
                    "image_url": {"url": f"data:image/{image_type};base64,{base64_image}"},
                },
                {"type": "text", "text": user_query},
            ],
        }
    ]
    print(json.dumps(messages, indent=4))
    completion = client.chat.completions.create(
        model = model_id,
        messages = messages,
       
    )
    
    output_text = completion.choices[0].message.content


    # Parse action and visualize
    try:
        tool_call_content = output_text.split('<tool_call>\n')[1].split('\n</tool_call>')[0]
        action = json.loads(tool_call_content)
        
        display_image = input_image.resize((resized_width, resized_height))

        if 'arguments' in action and 'coordinate' in action['arguments']:
            coordinate_relative = action['arguments']['coordinate']
            coordinate_absolute = [coordinate_relative[0] / img_width * resized_width, coordinate_relative[1] / img_height * resized_height]
            display_image = draw_point(display_image, coordinate_absolute, color='green')
            
    except (IndexError, json.JSONDecodeError, KeyError) as e:
        print(f"Warning: Could not parse tool call or coordinates from output. Error: {e}")
        display_image = input_image.resize((resized_width, resized_height))
    
    return output_text, display_image


from PIL import Image, ImageDraw, ImageColor

def draw_point(image: Image.Image, point: list, color=None):
    if isinstance(color, str):
        try:
            color = ImageColor.getrgb(color)
            color = color + (128,)  
        except ValueError:
            color = (255, 0, 0, 128)  
    else:
        color = (255, 0, 0, 128)  

    overlay = Image.new('RGBA', image.size, (255, 255, 255, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    radius = min(image.size) * 0.05
    x, y = point 

    overlay_draw.ellipse(
        [(x - radius, y - radius), (x + radius, y + radius)],
        fill=color
    )
    
    center_radius = radius * 0.1
    overlay_draw.ellipse(
        [(x - center_radius, y - center_radius), 
         (x + center_radius, y + center_radius)],
        fill=(0, 255, 0, 255)
    )

    image = image.convert('RGBA')
    combined = Image.alpha_composite(image, overlay)

    return combined.convert('RGB')

def main():
    """
    Main function to execute GUI grounding example in a closed loop
    """
    # Load user query from config
    user_query = "Please click on the WeChat icon in the top macOS menu bar to open the main WeChat window." # Default
    try:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_queries.json")
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            selected_id = config.get("selected_query_id")
            for q in config.get("queries", []):
                if q["id"] == selected_id:
                    user_query = q["query"]
                    print(f"Loaded query ID {selected_id}: {q.get('description', '')}")
                    break
            else:
                print(f"Warning: Query ID {selected_id} not found in config, using default.")
    except Exception as e:
        print(f"Warning: Could not load user_queries.json: {e}. Using default query.")

    # Example usage
    # user_query = "Please click on the WeChat icon in the top macOS menu bar to open the main WeChat window."
    model_id = "qwen-vl-max-latest"
    
    print(f"Task: {user_query}")
    print("Starting closed loop agent. Press Ctrl+C to stop.")

    # Create log directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = os.path.join("logs", f"run_{timestamp}")
    os.makedirs(log_dir, exist_ok=True)
    print(f"Logging to: {log_dir}")
    
    # Initialize action history list
    action_history = []
    
    step_count = 0

    try:
        while True:
            step_count += 1
            step_prefix = f"step_{step_count:03d}"
            print(f"\n--- Step {step_count} ---")

            # 截图并保存
            screenshot_path = "imgs/screen.png"
            success, scale = capture_screen_and_save(save_path=screenshot_path)
            if not success:
                print("截图失败")
                time.sleep(1)
                continue
            
            # Save screenshot to log
            log_screenshot_path = os.path.join(log_dir, f"{step_prefix}_screen.png")
            shutil.copy(screenshot_path, log_screenshot_path)

            # screenshot = "./computer_use2.jpeg"
            # screenshot = "./test_pic_1.png"
            screenshot = screenshot_path
            
            with Image.open(screenshot) as img:
                img_width, img_height = img.size
            
            try:
                output_text, display_image = perform_gui_grounding_with_api(screenshot, user_query, model_id)

                # Display results
                print(f"Model Output: {output_text}")
                # display(display_image)
                # display_image.show()

                # Execute the action using ComputerUse
                action_data = None
                if '<tool_call>' in output_text:
                    tool_call_content = output_text.split('<tool_call>\n')[1].split('\n</tool_call>')[0]
                    action_data = json.loads(tool_call_content)
                    
                    print(f"Executing action: {action_data}")
                    
                    # Extract arguments if present
                    if 'arguments' in action_data:
                        action_params = action_data['arguments']
                    else:
                        action_params = action_data

                    # Initialize computer use tool with the same resolution config as used in prompt
                    computer_use = ComputerUse(cfg={"display_width_px": img_width, "display_height_px": img_height})
                    result = computer_use.call(action_params)
                    print(f"Execution Result: {result}")
                    
                    # Small delay to let the action take effect
                    time.sleep(1)
                else:
                    print("No tool call found in output.")
                    time.sleep(2)
                
                # Save log data
                log_data = {
                    "step": step_count,
                    "timestamp": datetime.now().isoformat(),
                    "model_output": output_text,
                    "action_data": action_data
                }
                
                # Update history and save to summary file
                action_history.append(log_data)
                with open(os.path.join(log_dir, "action_history.json"), "w", encoding="utf-8") as f:
                    json.dump(action_history, f, indent=4, ensure_ascii=False)
                
                with open(os.path.join(log_dir, f"{step_prefix}_log.json"), "w", encoding="utf-8") as f:
                    json.dump(log_data, f, indent=4, ensure_ascii=False)

            except Exception as e:
                print(f"Error in loop iteration: {e}")
                time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopped by user.")


if __name__ == "__main__":
    main()