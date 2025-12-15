"""
统一异常体系
提供结构化的异常处理，便于调试和错误追踪
"""

from typing import Dict, Optional


class AppException(Exception):
    """
    应用基础异常
    
    所有自定义异常的基类，提供结构化的错误信息
    """
    
    def __init__(self, message: str, code: str, details: Optional[Dict] = None):
        """
        初始化异常
        
        Args:
            message: 人类可读的错误消息
            code: 机器可读的错误代码（如 WEATHER_NO_DATA）
            details: 额外的错误详情
        """
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict:
        """转换为字典格式，用于API响应"""
        return {
            "message": self.message,
            "code": self.code,
            "details": self.details,
            "type": self.__class__.__name__
        }
    
    def __str__(self):
        return f"[{self.code}] {self.message}"


# ============================================================================
# 数据层异常
# ============================================================================

class DataSourceException(AppException):
    """数据源异常基类"""
    pass


class POIDatabaseException(DataSourceException):
    """POI数据库异常"""
    pass


class GaodeAPIException(DataSourceException):
    """高德API异常"""
    pass


class WeatherServiceException(DataSourceException):
    """天气服务异常"""
    pass


# ============================================================================
# 业务逻辑异常
# ============================================================================

class BusinessLogicException(AppException):
    """业务逻辑异常基类"""
    pass


class InvalidSessionException(BusinessLogicException):
    """无效会话异常"""
    pass


class PlanningException(BusinessLogicException):
    """规划异常"""
    pass


class NoCandidatesException(PlanningException):
    """无候选异常"""
    pass


class InvalidStateException(BusinessLogicException):
    """无效状态异常"""
    pass


class InvalidInputException(BusinessLogicException):
    """无效输入异常"""
    pass


# ============================================================================
# 外部服务异常
# ============================================================================

class ExternalServiceException(AppException):
    """外部服务异常基类"""
    pass


class LLMServiceException(ExternalServiceException):
    """LLM服务异常"""
    pass


class APIRateLimitException(ExternalServiceException):
    """API速率限制异常"""
    pass


class NetworkException(ExternalServiceException):
    """网络异常"""
    pass


# ============================================================================
# 验证异常
# ============================================================================

class ValidationException(AppException):
    """验证异常基类"""
    pass


class VerificationFailedException(ValidationException):
    """验证失败异常"""
    pass
