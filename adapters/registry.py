"""适配器注册表 — 管理所有API适配器"""
from typing import Dict, Optional, List
from .base import BaseAdapter


class AdapterRegistry:
    """全局适配器注册中心"""

    def __init__(self):
        self._adapters: Dict[str, BaseAdapter] = {}
        self._fallback_chain: List[str] = []

    def register(self, adapter: BaseAdapter, name: str = None) -> bool:
        """注册一个适配器"""
        n = name or adapter.name
        if n in self._adapters:
            return False
        self._adapters[n] = adapter
        return True

    def get(self, name: str) -> Optional[BaseAdapter]:
        return self._adapters.get(name)

    def list_available(self) -> List[str]:
        return [n for n, a in self._adapters.items() if a.health_check()["available"]]

    def set_fallback_chain(self, chain: List[str]):
        """设置fallback优先级链"""
        self._fallback_chain = chain

    def get_fallback_chain(self) -> List[str]:
        return self._fallback_chain or list(self._adapters.keys())
