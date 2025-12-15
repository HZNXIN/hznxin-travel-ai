"""
系统配置
使用Pydantic Settings管理配置，支持环境变量
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

# 尝试加载.env文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv不是必需的


class Settings(BaseSettings):
    """
    应用配置
    
    所有配置项都可以通过环境变量覆盖
    例如：export GAODE_API_KEY="your_key"
    """
    
    # ========================================================================
    # 应用配置
    # ========================================================================
    app_env: str = Field(default="development", description="应用环境")
    log_level: str = Field(default="INFO", description="日志级别")
    log_file: str = Field(default="logs/app.log", description="日志文件")
    data_dir: str = Field(default="data", description="数据目录")
    
    # ========================================================================
    # 高德地图API
    # ========================================================================
    gaode_api_key: str = Field(
        default="your-gaode-api-key-here",
        description="高德API密钥 - 请通过环境变量GAODE_API_KEY设置"
    )
    gaode_private_key: Optional[str] = Field(
        default=None,
        description="高德私钥（可选）"
    )
    request_timeout: int = Field(default=10, description="API请求超时（秒）")
    
    # ========================================================================
    # LLM配置
    # ========================================================================
    llm_provider: str = Field(default="openai", description="LLM提供商")
    llm_api_key: str = Field(
        default="",
        description="LLM API密钥"
    )
    llm_api_base: str = Field(
        default="https://api.deepseek.com/v1",
        description="LLM API基础URL"
    )
    llm_model: str = Field(default="deepseek-chat", description="LLM模型名称")
    llm_temperature: float = Field(default=0.7, description="LLM温度参数")
    llm_max_tokens: int = Field(default=500, description="LLM最大token数")
    
    # ========================================================================
    # 数据库配置
    # ========================================================================
    database_url: str = Field(
        default="sqlite:///./data/gaode.db",
        description="数据库URL"
    )
    
    # ========================================================================
    # Redis配置（可选）
    # ========================================================================
    redis_url: Optional[str] = Field(
        default=None,
        description="Redis URL"
    )
    
    # ========================================================================
    # AI模型配置
    # ========================================================================
    bert_model_path: str = Field(
        default="bert-base-chinese",
        description="BERT模型路径"
    )
    use_gpu: bool = Field(default=False, description="是否使用GPU")
    
    # ========================================================================
    # 业务配置
    # ========================================================================
    max_candidates: int = Field(default=10, description="最多返回候选数")
    max_distance_km: int = Field(default=50, description="最大距离（km）")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # 允许从环境变量读取，环境变量优先级高于.env文件
        env_nested_delimiter = "__"


# 创建全局配置实例
settings = Settings()

# ============================================================================
# 向后兼容 - 旧代码可以继续使用这些变量
# 逐步迁移到 settings 对象
# ============================================================================
GAODE_API_KEY = settings.gaode_api_key
GAODE_PRIVATE_KEY = settings.gaode_private_key
DATABASE_URL = settings.database_url
REDIS_URL = settings.redis_url
BERT_MODEL_PATH = settings.bert_model_path
USE_GPU = settings.use_gpu
MAX_CANDIDATES = settings.max_candidates
MAX_DISTANCE_KM = settings.max_distance_km
REQUEST_TIMEOUT = settings.request_timeout
LOG_LEVEL = settings.log_level
LOG_FILE = settings.log_file
