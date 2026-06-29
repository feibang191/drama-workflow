"""API适配器基类 — 所有外部API的统一接口"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field


class AdapterError(Exception):
    """适配器基础异常"""
    def __init__(self, message: str, status_code: int = 0, details: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}


class AuthError(AdapterError):
    """认证失败"""
    pass


class RateLimitError(AdapterError):
    """频率限制"""
    pass


class TimeoutError(AdapterError):
    """超时"""
    pass


class ContentBlockedError(AdapterError):
    """内容被安全策略拦截"""
    pass


@dataclass
class AdapterConfig:
    """适配器配置"""
    api_key: str = ""
    base_url: str = ""
    timeout: int = 30
    max_retries: int = 3
    extra: dict = field(default_factory=dict)


class BaseAdapter:
    """所有API适配器的基类"""

    def __init__(self, name: str, config: AdapterConfig = None):
        self.name = name
        self.config = config or AdapterConfig()

    def generate(self, prompt: str, **kwargs) -> dict:
        """生成图片/视频。子类必须实现"""
        raise NotImplementedError

    def validate_config(self) -> bool:
        """检查配置是否有效"""
        return bool(self.config.api_key)

    def health_check(self) -> dict:
        """检查服务是否可用"""
        return {"available": self.validate_config(), "name": self.name}
