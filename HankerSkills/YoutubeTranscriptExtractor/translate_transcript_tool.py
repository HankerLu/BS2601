import os
from deep_translator import GoogleTranslator

def translate_file(input_path, output_path):
    print(f"Reading from {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    header = lines[:4]
    content = lines[4:]

    translator = GoogleTranslator(source='auto', target='zh-CN')
    
    translated_lines = []
    
    # Process header (optional, but let's keep it clean)
    translated_lines.extend(header)

    # Process content
    # We can batch lines to reduce requests, but we need to respect character limits (usually 5000 chars)
    batch = []
    batch_length = 0
    MAX_BATCH_CHARS = 2000 # Safety margin below 5000

    print(f"Translating {len(content)} lines of content...")
    
    for i, line in enumerate(content):
        line = line.strip()
        if not line:
            continue
            
        # If adding this line exceeds limit, process batch
        if batch_length + len(line) > MAX_BATCH_CHARS:
            try:
                text_to_translate = "\n".join(batch)
                translated = translator.translate(text_to_translate)
                translated_lines.append(translated + "\n")
                print(f"Translated batch ending at line {i+4}")
            except Exception as e:
                print(f"Error translating batch: {e}")
                # Fallback: keep original or mark error
                translated_lines.append(text_to_translate + "\n")
            
            batch = []
            batch_length = 0
        
        batch.append(line)
        batch_length += len(line) + 1 # +1 for newline

    # Process final batch
    if batch:
        try:
            text_to_translate = "\n".join(batch)
            translated = translator.translate(text_to_translate)
            translated_lines.append(translated + "\n")
            print("Translated final batch")
        except Exception as e:
            print(f"Error translating final batch: {e}")
            translated_lines.append(text_to_translate + "\n")

    print(f"Writing to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(translated_lines)

if __name__ == "__main__":
    base_dir = "/Users/hankerlu/Desktop/BS2601/HankerSkills/YoutubeTranscriptExtractor"
    input_file = os.path.join(base_dir, "transcript_CQlTmOFM4Qs.txt")
    output_file = os.path.join(base_dir, "transcript_CQlTmOFM4Qs_zh.txt")
    
    translate_file(input_file, output_file)
