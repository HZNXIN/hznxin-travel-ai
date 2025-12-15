"""
测试不同的模型，找出可用的
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.core.llm_client import create_llm_client


API_KEY = "sk-UZp1D3qeRaYeDhDUVX55tHXjZfVW8qJHCJtgwmFJHuFAWKKN"
API_BASE = "https://hone.vvvv.ee/v1"

# 尝试不同的模型名称
models_to_try = [
    "gpt-3.5-turbo",
    "gpt-4",
    "gpt-4-turbo",
    "gpt-4o",
    "claude-3-opus",
    "claude-3-sonnet",
    "claude-3-haiku",
    "claude-3.5-sonnet",
    "deepseek-chat",
    "gemini-pro",
]

print("="*70)
print("  测试不同模型")
print("="*70)
print()

for model in models_to_try:
    print(f"📡 测试模型: {model}")
    
    try:
        llm_client = create_llm_client(
            provider='openai',
            api_key=API_KEY,
            model=model,
            api_base=API_BASE
        )
        
        response = llm_client.generate(
            prompt="你好，请回复'收到'",
            temperature=0.7,
            max_tokens=50
        )
        
        if response and "LLM服务暂时不可用" not in response:
            print(f"  ✅ {model} 可用！")
            print(f"  响应: {response}")
            print()
            print(f"🎯 找到可用模型: {model}")
            break
        else:
            print(f"  ❌ {model} 不可用")
    
    except Exception as e:
        error_msg = str(e)
        print(f"  ❌ {model} 错误: {error_msg[:100]}")
    
    print()
