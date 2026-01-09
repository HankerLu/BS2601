import torch
from transformers import AutoProcessor, AutoModelForVision2Seq

model_path = "Qwen/Qwen3-VL-30B-A3B-Instruct"
processor = AutoProcessor.from_pretrained(model_path)
model, output_loading_info = AutoModelForVision2Seq.from_pretrained(model_path, torch_dtype="auto", device_map="auto", output_loading_info=True)
print("output_loading_info", output_loading_info)

import json
from PIL import Image
from IPython.display import display
from qwen_agent.llm.fncall_prompts.nous_fncall_prompt import (
    NousFnCallPrompt,
    Message,
    ContentItem,
)
from transformers.models.qwen2_vl.image_processing_qwen2_vl_fast import smart_resize

from utils.agent_function_call import ComputerUse

def perform_gui_grounding(screenshot_path, user_query, model, processor):
    """
    Perform GUI grounding using Qwen model to interpret user query on a screenshot.
    
    Args:
        screenshot_path (str): Path to the screenshot image
        user_query (str): User's query/instruction
        model: Preloaded Qwen model
        processor: Preloaded Qwen processor
        
    Returns:
        tuple: (output_text, display_image) - Model's output text and annotated image
    """

    # Open and process image
    input_image = Image.open(screenshot_path)

    patch_size = processor.image_processor.patch_size
    merge_size = processor.image_processor.merge_size
    resized_height, resized_width = smart_resize(
        input_image.height,
        input_image.width,
        factor=patch_size * merge_size,
        min_pixels=patch_size * patch_size * merge_size * merge_size * 16,
        max_pixels=patch_size * patch_size * merge_size * merge_size * 6400,
    )
    
    # Initialize computer use function
    computer_use = ComputerUse(
        cfg={"display_width_px": 1000, "display_height_px": 1000}
    )

    # Build messages
    message = NousFnCallPrompt().preprocess_fncall_messages(
        messages=[
            Message(role="system", content=[ContentItem(text="You are a helpful assistant.")]),
            Message(role="user", content=[
                ContentItem(text=user_query),
                ContentItem(image=f"file://{screenshot_path}")
            ]),
        ],
        functions=[computer_use.function],
        lang=None,
    )
    message = [msg.model_dump() for msg in message]

    # Process input
    text = processor.apply_chat_template(message, tokenize=False, add_generation_prompt=True)
    inputs = processor(text=[text], images=[input_image], padding=True, return_tensors="pt").to('cuda')

    # Generate output
    output_ids = model.generate(**inputs, max_new_tokens=2048)
    generated_ids = [output_ids[len(input_ids):] for input_ids, output_ids in zip(inputs.input_ids, output_ids)]
    output_text = processor.batch_decode(generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True)[0]

    # Parse action and visualize
    action = json.loads(output_text.split('<tool_call>\n')[1].split('\n</tool_call>')[0])
    display_image = input_image.resize((resized_width, resized_height))
    display_x = action['arguments']['coordinate'][0] / 1000 * resized_width
    display_y = action['arguments']['coordinate'][1] / 1000 * resized_height
    display_image = draw_point(display_image, (display_x, display_y), color='green')
    
    return output_text, display_image

screenshot = "./computer_use1.jpeg"
user_query = 'Reload cache'
output_text, display_image = perform_gui_grounding(screenshot, user_query, model, processor)

# Display results
print(output_text)
display(display_image)

# Example usage
screenshot = "./computer_use2.jpeg"
user_query = 'open the first issue'
output_text, display_image = perform_gui_grounding(screenshot, user_query, model, processor)

# Display results
print(output_text)
display(display_image)