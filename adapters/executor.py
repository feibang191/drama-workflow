"""适配器执行器 — fallback链 + 重试逻辑"""
from typing import Optional
from .registry import AdapterRegistry
from .base import BaseAdapter, AdapterError, AuthError, RateLimitError, TimeoutError
import time


class AdapterExecutor:
    """执行器：沿fallback链尝试，失败时自动切换到下一个"""

    def __init__(self, registry: AdapterRegistry):
        self.registry = registry
        self.attempt_count = 0
        self.last_error = None

    def execute(self, prompt: str, preferred: str = None, **kwargs) -> dict:
        """执行生成，支持fallback"""
        chain = self.registry.get_fallback_chain()
        if preferred and preferred in chain:
            chain = [preferred] + [c for c in chain if c != preferred]

        for adapter_name in chain:
            adapter = self.registry.get(adapter_name)
            if not adapter or not adapter.health_check()["available"]:
                continue
            try:
                result = adapter.generate(prompt, **kwargs)
                self.attempt_count += 1
                return result
            except (AuthError, RateLimitError) as e:
                self.last_error = e
                continue
            except TimeoutError as e:
                self.last_error = e
                continue
            except AdapterError as e:
                self.last_error = e
                if hasattr(e, "status_code") and e.status_code >= 500:
                    continue
                raise

        raise AdapterError(f"All {len(chain)} adapters failed. Last: {self.last_error}")
