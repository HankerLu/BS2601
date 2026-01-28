import json
import sys
import os
import glob

def find_latest_log(log_dir="api_logs"):
    list_of_files = glob.glob(os.path.join(log_dir, "*.jsonl"))
    if not list_of_files:
        return None
    return max(list_of_files, key=os.path.getctime)

def print_readable_log(file_path):
    print(f"正在读取日志文件: {file_path}\n")
    print("=" * 80)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    print(f"[Error] 第 {line_num} 行无法解析为 JSON")
                    continue
                
                # 提取关键信息
                timestamp = entry.get("timestamp", "N/A")
                mode = entry.get("mode", "Unknown Mode")
                request = entry.get("request", {})
                response = entry.get("response", {})
                
                # 打印标题
                print(f"【{mode}】 @ {timestamp}")
                print("-" * 80)
                
                # 打印请求 (Messages)
                messages = request.get("messages", [])
                print("📝 [Request / Prompt]")
                for msg in messages:
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    print(f"  [{role.upper()}]:")
                    # 缩进内容以便阅读
                    for content_line in content.split('\n'):
                        print(f"    {content_line}")
                    print()
                
                # 打印响应 (Response)
                print("🤖 [Response / AI Output]")
                if response:
                    choices = response.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
                        try:
                            # 尝试解析响应中的 JSON 字符串以便更漂亮地打印
                            content_json = json.loads(content)
                            print(json.dumps(content_json, indent=4, ensure_ascii=False))
                        except (json.JSONDecodeError, TypeError):
                            # 如果不是 JSON 或解析失败，直接打印
                            print(content)
                    else:
                        # 可能是错误或其他类型的响应
                        print(json.dumps(response, indent=2, ensure_ascii=False))
                else:
                    error = entry.get("error")
                    if error:
                        print(f"❌ [Error]: {error}")
                    else:
                        print("(No response content)")
                
                print("=" * 80)
                print("\n")
                
    except FileNotFoundError:
        print(f"错误: 找不到文件 {file_path}")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
    else:
        log_file = find_latest_log()
        
    if log_file:
        print_readable_log(log_file)
    else:
        print("未找到日志文件或未指定文件。")
