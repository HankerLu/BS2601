import os
import sys

# 尝试导入 LLMWrapper，假设此脚本与 llm_wraper.py 在同一目录下
try:
    from llm_wraper import LLMWrapper
except ImportError:
    # 如果运行路径不一致，尝试添加当前目录到 sys.path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from llm_wraper import LLMWrapper

def test_text_generation(llm):
    print("\n" + "="*50)
    print("测试 1: 普通文本生成 (generate_text)")
    print("="*50)
    
    messages = [
        {"role": "system", "content": "你是一个简洁的科普助手。"},
        {"role": "user", "content": "请用一句话解释什么是囚徒困境。"}
    ]
    
    print(f"输入 Prompt: {messages[-1]['content']}")
    print("-" * 20)
    print("等待 API 响应中...")
    
    start_time = time.time()
    response = llm.generate_text(messages)
    duration = time.time() - start_time
    
    print("-" * 20)
    if response:
        print(f"✅ 调用成功 (耗时 {duration:.2f}s)")
        print(f"回复内容:\n{response}")
    else:
        print("❌ 调用失败: 未收到响应。")

def test_json_generation(llm):
    print("\n" + "="*50)
    print("测试 2: JSON 结构化输出 (generate_json)")
    print("="*50)
    
    messages = [
        {"role": "system", "content": "你是一个数据生成助手。请严格输出 JSON 格式。"},
        {"role": "user", "content": "生成一个包含 'game_name' (博弈名称) 和 'players' (玩家数量, int) 的 JSON 对象，以'剪刀石头布'为例。"}
    ]
    
    print(f"输入 Prompt: {messages[-1]['content']}")
    print("-" * 20)
    print("等待 API 响应中...")
    
    start_time = time.time()
    response = llm.generate_json(messages)
    duration = time.time() - start_time
    
    print("-" * 20)
    if response:
        print(f"✅ 调用成功 (耗时 {duration:.2f}s)")
        print(f"回复类型: {type(response)}")
        print(f"回复内容: {response}")
        
        # 简单的验证
        if isinstance(response, dict) and "game_name" in response:
            print("✅ JSON 结构验证通过")
        else:
            print("⚠️ JSON 结构可能不符合预期")
    else:
        print("❌ 调用失败: 未收到响应或解析失败。")

import time

def main():
    print("开始 LLMWrapper 功能测试...")
    
    # 检查 API Key
    if "ARK_API_KEY" not in os.environ:
        print("⚠️ 提示: 环境变量 'ARK_API_KEY' 未检测到。将尝试使用 llm_wraper.py 内部的默认 Key。")
    
    try:
        # 1. 初始化
        llm = LLMWrapper()
        
        # 2. 运行文本生成测试
        test_text_generation(llm)
        
        # 3. 运行 JSON 生成测试
        test_json_generation(llm)
        
    except Exception as e:
        print(f"\n❌ 发生未捕获的异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
