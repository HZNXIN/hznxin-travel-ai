"""
LLM配置文件
集中管理LLM相关配置
"""
import os

# LLM提供商配置
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "deepseek")  # 'deepseek', 'openai', 'qwen', 'mock'

# API配置 - DeepSeek
LLM_API_KEY = os.getenv("DEEPSEEK_API_KEY", "your-deepseek-api-key-here")
LLM_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
LLM_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# 备用配置（如果主配置不可用）
FALLBACK_PROVIDER = "mock"  # 降级到Mock模式

# LLM参数
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 500

# 启用/禁用LLM
ENABLE_LLM = True  # ✅ DeepSeek已成功接入

# 超时设置
LLM_TIMEOUT = 30  # 秒

# 重试设置
LLM_MAX_RETRIES = 2
LLM_RETRY_DELAY = 2  # 秒
