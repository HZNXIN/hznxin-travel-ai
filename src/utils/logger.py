"""
结构化日志系统
提供统一的日志记录和监控
"""

import logging
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import traceback


class StructuredLogger:
    """
    结构化日志记录器
    
    特性：
    1. 统一的日志格式
    2. 多级别日志（DEBUG, INFO, WARNING, ERROR, CRITICAL）
    3. 文件和控制台双输出
    4. JSON格式日志（便于解析）
    5. 性能监控埋点
    """
    
    def __init__(self, 
                 name: str,
                 log_dir: str = "logs",
                 console_level: int = logging.INFO,
                 file_level: int = logging.DEBUG):
        """
        初始化日志器
        
        Args:
            name: 日志器名称
            log_dir: 日志目录
            console_level: 控制台日志级别
            file_level: 文件日志级别
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # 清除已有的handler
        self.logger.handlers = []
        
        # 创建日志目录
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)
        
        # 控制台Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_level)
        console_formatter = ColoredFormatter(
            '%(levelname_colored)s [%(name)s] %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # 文件Handler（JSON格式）
        log_file = log_path / f"{name}_{datetime.now().strftime('%Y%m%d')}.jsonl"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(file_level)
        file_formatter = JSONFormatter()
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
    
    def debug(self, message: str, **kwargs):
        """调试日志"""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """信息日志"""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """警告日志"""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """错误日志"""
        if error:
            kwargs['error_type'] = type(error).__name__
            kwargs['error_message'] = str(error)
            kwargs['traceback'] = traceback.format_exc()
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """严重错误日志"""
        self._log(logging.CRITICAL, message, **kwargs)
    
    def metric(self, metric_name: str, value: float, unit: str = "", **tags):
        """
        记录性能指标
        
        Args:
            metric_name: 指标名称
            value: 指标值
            unit: 单位
            **tags: 标签
        """
        self._log(logging.INFO, f"METRIC: {metric_name}", 
                 metric_name=metric_name, 
                 metric_value=value,
                 metric_unit=unit,
                 **tags)
    
    def _log(self, level: int, message: str, **kwargs):
        """内部日志记录方法"""
        extra = {
            'timestamp': datetime.now().isoformat(),
            'data': kwargs
        }
        self.logger.log(level, message, extra=extra)


class ColoredFormatter(logging.Formatter):
    """带颜色的控制台日志格式化器"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[32m',      # 绿色
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 红色
        'CRITICAL': '\033[35m',  # 紫色
    }
    RESET = '\033[0m'
    
    def format(self, record):
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname_colored = (
                f"{self.COLORS[levelname]}{levelname}{self.RESET}"
            )
        else:
            record.levelname_colored = levelname
        
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """JSON格式日志格式化器"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # 添加extra数据
        if hasattr(record, 'timestamp'):
            log_data['timestamp'] = record.timestamp
        if hasattr(record, 'data'):
            log_data['data'] = record.data
        
        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


class PerformanceMonitor:
    """
    性能监控器
    
    用于监控函数执行时间和资源使用
    """
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.metrics = {}
    
    def track_time(self, operation: str):
        """
        装饰器：追踪函数执行时间
        
        Usage:
            @monitor.track_time('poi_search')
            def search_poi(city):
                ...
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = datetime.now()
                
                try:
                    result = func(*args, **kwargs)
                    success = True
                    error = None
                except Exception as e:
                    success = False
                    error = e
                    raise
                finally:
                    duration = (datetime.now() - start_time).total_seconds()
                    
                    self.logger.metric(
                        f"{operation}_duration",
                        duration,
                        "seconds",
                        operation=operation,
                        success=success,
                        function=func.__name__
                    )
                    
                    if not success:
                        self.logger.error(
                            f"Operation failed: {operation}",
                            error=error,
                            operation=operation,
                            function=func.__name__
                        )
                
                return result
            return wrapper
        return decorator
    
    def record_metric(self, name: str, value: float, **tags):
        """记录指标"""
        self.logger.metric(name, value, **tags)
    
    def get_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        return self.metrics.copy()


# ========== 全局日志器实例 ==========

# 系统主日志
system_logger = StructuredLogger("system")

# API日志
api_logger = StructuredLogger("api")

# 性能日志
perf_logger = StructuredLogger("performance")

# 错误日志
error_logger = StructuredLogger("error", file_level=logging.ERROR)

# 性能监控器
performance_monitor = PerformanceMonitor(perf_logger)


# ========== 便捷函数 ==========

def log_api_request(endpoint: str, method: str, params: Dict):
    """记录API请求"""
    api_logger.info(
        f"API Request: {method} {endpoint}",
        endpoint=endpoint,
        method=method,
        params=params
    )


def log_api_response(endpoint: str, status: int, duration: float):
    """记录API响应"""
    api_logger.info(
        f"API Response: {endpoint}",
        endpoint=endpoint,
        status=status,
        duration=duration
    )


def log_error(message: str, error: Exception, context: Dict = None):
    """记录错误"""
    error_logger.error(
        message,
        error=error,
        context=context or {}
    )


def log_system_event(event: str, **details):
    """记录系统事件"""
    system_logger.info(
        f"System Event: {event}",
        event=event,
        **details
    )


def log_performance(operation: str, duration: float, **metrics):
    """记录性能指标"""
    perf_logger.metric(
        f"{operation}_time",
        duration,
        "seconds",
        operation=operation,
        **metrics
    )


# ========== 使用示例 ==========
"""
# 1. 基本日志
from src.utils.logger import system_logger

system_logger.info("系统启动", version="2.0.0")
system_logger.error("配置加载失败", error=e, config_file="config.yaml")

# 2. API日志
from src.utils.logger import log_api_request, log_api_response

log_api_request("/api/session/start", "POST", {"city": "苏州"})
log_api_response("/api/session/start", 200, 0.15)

# 3. 性能监控
from src.utils.logger import performance_monitor

@performance_monitor.track_time('poi_search')
def search_poi(city):
    # ... 搜索逻辑
    pass

# 4. 手动记录指标
performance_monitor.record_metric("poi_count", 150, city="苏州")

# 5. 错误日志
from src.utils.logger import log_error

try:
    result = risky_operation()
except Exception as e:
    log_error("操作失败", e, {"user_id": "123", "operation": "search"})
"""
