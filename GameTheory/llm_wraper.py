import os
import json
import requests
import base64
import time
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# --- 全局配置 ---
# 所有的密钥、模型名称和URL设置
ARK_API_KEY = os.environ.get("ARK_API_KEY", "e3d02106-4976-445b-9356-f9e8fe440a6c") 
BASE_URL  = "https://ark.cn-beijing.volces.com/api/v3"

# 【将所有 chat/completions 任务统一使用一个URL
COMPLETIONS_URL = f"{BASE_URL}/chat/completions"

# 将模型名称作为独立的常量管理
TEXT_MODEL  = "deepseek-v3-250324"

# 控制是否是演示模式 (已移除 Embedding 相关功能，此模式目前无实际效果)
SHOW_MODE = False 

class LLMWrapper:
    """
    封装了与云端多模态大模型API交互的AI功能。
    完全适配嵌入式系统部署场景，不依赖本地大模型。
    """
    def __init__(self, db_conn=None, db_cursor=None, api_key=None, log_dir="api_logs"):
        self.api_key = api_key or ARK_API_KEY
        if self.api_key == "YOUR_ARK_API_KEY_HERE":
            raise ValueError("API密钥没有设置。 请在环境变量设置API密钥。")
        self.headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
        
        # 将模型名称作为实例属性，方便外部调用
        self.TEXT_MODEL = TEXT_MODEL
        
        self.db_conn = db_conn
        self.db_cursor = db_cursor
        self.show_mode = SHOW_MODE # 将全局设置赋给实例变量

        # 创建日志目录
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 创建会话日志文件（记录本次运行的所有API调用）
        session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_log_file = os.path.join(self.log_dir, f"session_{session_timestamp}.jsonl")
        
        self.session = requests.Session()
        # 定义重试策略
        retry_strategy = Retry(
            total=3,  # 总共重试3次
            backoff_factor=1,  # 退避因子，第一次等1s，第二次等2s，第三次等4s
            status_forcelist=[429, 500, 502, 503, 504],  # 对这些服务器错误状态码也进行重试
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"],
            respect_retry_after_header=True
        )
        # 创建一个适配器，并将重试策略应用上去
        adapter = HTTPAdapter(max_retries=retry_strategy)
        # 为 session 的 http 和 https 请求都挂载这个适配器
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        print(f"云端多模态API客户端初始化成功。日志文件: {self.session_log_file}")

    def _clean_and_parse_json(self, response_str: str):
        """
        一个更健壮的JSON解析器，能够从包含额外字符的字符串中提取出第一个完整的JSON对象。
        它通过括号匹配来确定JSON的准确边界。
        """
        if not response_str:
            return None

        # 1. 预处理：去除Markdown代码块标记和首尾空白
        cleaned_str = response_str.strip()
        if cleaned_str.startswith('```json'):
            cleaned_str = cleaned_str[7:]
        if cleaned_str.endswith('```'):
            cleaned_str = cleaned_str[:-3]
        if cleaned_str.endswith('...'):
            cleaned_str = cleaned_str[:-3]
        cleaned_str = cleaned_str.strip()

        # 修复模型常见的结尾错误
        if cleaned_str.endswith('])}'):
            print("  - [JSON Cleanup] 发现并修正了常见的 '])}' 结尾错误。")
            cleaned_str = cleaned_str[:-3] + '}]}'

        # 2. 智能提取：使用括号匹配算法找到第一个完整的JSON对象
        try:
            # 找到第一个有效的JSON起始字符
            start_pos = -1
            first_curly = cleaned_str.find('{')
            first_square = cleaned_str.find('[')

            if first_curly == -1 and first_square == -1:
                return None # 没有找到JSON的开始
            
            if first_curly != -1 and (first_square == -1 or first_curly < first_square):
                start_pos = first_curly
                open_bracket, close_bracket = '{', '}'
            else:
                start_pos = first_square
                open_bracket, close_bracket = '[', ']'

            # 括号计数器
            bracket_counter = 0
            in_string = False
            
            for i in range(start_pos, len(cleaned_str)):
                char = cleaned_str[i]

                # 检查是否在字符串内部，忽略字符串中的括号
                if char == '"' and (i == 0 or cleaned_str[i-1] != '\\'):
                    in_string = not in_string
                
                if not in_string:
                    if char == open_bracket:
                        bracket_counter += 1
                    elif char == close_bracket:
                        bracket_counter -= 1
                
                # 当计数器归零时，我们找到了完整的JSON对象
                if bracket_counter == 0:
                    json_str_candidate = cleaned_str[start_pos : i + 1]
                    # 最后的尝试解析
                    return json.loads(json_str_candidate)

            # 如果循环结束计数器还没归零，说明JSON不完整
            print(f"JSON括号不匹配，解析失败。清理后的字符串: '{cleaned_str}'")
            return None

        except (json.JSONDecodeError, IndexError) as e:
            # 如果即使在智能提取后仍然失败，打印错误
            print(f"最终JSON解析失败: {e}\n原始字符串: '{response_str}'\n清理后字符串: '{cleaned_str}'")
            return None


    def _save_api_log(self, log_entry):
        """保存API调用日志到文件"""
        try:
            with open(self.session_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"  - [Warning] 日志保存失败: {e}")

    def _call_api(self, data, stream=False, mode=None):
        """通用的底层API调用函数，现在使用带有重试逻辑的session。"""
        call_timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": call_timestamp,
            "mode": mode,
            "request": data,
            "response": None,
            "error": None,
            "status_code": None,
            "request_id": None
        }
        
        try:
            # 【核心修改】使用 self.session.post 替换 requests.post
            response = self.session.post(COMPLETIONS_URL, headers=self.headers, json=data, timeout=60, stream=stream)
            
            request_id = response.headers.get('x-request-id', 'N/A')
            log_entry["status_code"] = response.status_code
            log_entry["request_id"] = request_id
            
            print(f"  - [API Call] Status: {response.status_code} | Request ID: {request_id}")
            
            response.raise_for_status()
            
            # 如果不是流式调用，记录响应内容
            if not stream:
                try:
                    response_json = response.json()
                    log_entry["response"] = response_json
                except:
                    log_entry["response"] = {"raw": response.text}
            
            # 保存日志
            self._save_api_log(log_entry)
            
            return response
        except requests.exceptions.RequestException as e:
            # 异常处理现在能更好地反映重试后的最终失败
            log_entry["error"] = str(e)
            self._save_api_log(log_entry)
            print(f"API请求在多次重试后最终失败: {e}")
            return None

    # 函数签名保持不变，但移除了内部的缓存/embedding逻辑
    def generate_text(self, messages, temperature=0.7, stream=False, mode=None, cache_key_query: str | None = None):
        """
        生成文本或文本流。
        (已移除 Embedding 相关缓存功能)
        """
        # --- 正常API调用 ---
        print(f"  - [API Call] 正在为 {mode or '功能性调用'} 生成文本...")
        data = {"model": TEXT_MODEL, "messages": messages, "temperature": temperature, "stream": stream}
        response = self._call_api(data, stream=stream, mode=mode)
        if not response:
            return None if not stream else iter([]) # 返回一个空迭代器
        
        if stream:
            # 流式调用直接返回响应流
            return response
        else:
            try:
                content = response.json()["choices"][0]["message"]["content"]
                return content
            except (KeyError, IndexError):
                return None

    # 函数签名保持不变，但移除了内部的缓存/embedding逻辑
    def generate_json(self, messages, model=None, temperature=0.0, mode=None, cache_key_query: str | None = None):
        """
        生成JSON对象。
        (已移除 Embedding 相关缓存功能)
        """
        # --- 正常API调用 ---
        print(f"  - [API Call] 正在为 {mode or '功能性调用'} 生成JSON...")
        target_model = model or TEXT_MODEL
        data = { "model": target_model, "messages": messages, "temperature": temperature, "response_format": {"type": "json_object"} }
        response = self._call_api(data, stream=False, mode=mode)
        if not response: return None
        
        try:
            content_str = response.json()["choices"][0]["message"]["content"]
            return self._clean_and_parse_json(content_str)
        except (KeyError, IndexError):
            return None
