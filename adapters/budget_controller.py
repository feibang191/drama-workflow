"""Phase 1-4: 预算控制引擎 — 费用/API/重试/时间四维预算"""
from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import datetime

DEFAULT_BUDGET = {
    "max_cost_per_run": 100.0,      # 单次运行最大费用(元)
    "max_api_calls_per_run": 200,    # 单次运行最大API调用
    "max_retries_per_shot": 3,       # 每shot最大重试
    "max_time_per_run_min": 120,     # 单次运行最大时间(分钟)
    "warn_threshold_pct": 80,        # 预算80%时警告
    "paid_ops_require_confirm": True,# 付费操作需confirm
}

@dataclass
class BudgetState:
    cost_used: float = 0.0
    api_calls_used: int = 0
    retries_used: int = 0
    time_used_min: float = 0.0
    is_paid_op: bool = False
    is_confirmed: bool = False

class BudgetController:
    def __init__(self, limits: Optional[Dict] = None):
        self.limits = {**DEFAULT_BUDGET, **(limits or {})}
        self.state = BudgetState()
        self.start_time = datetime.now()
    
    def check(self) -> Dict:
        """检查预算状态，返回警告/阻断"""
        result = {"passed": True, "warnings": [], "blockers": []}
        
        # 费用检查
        cost_pct = (self.state.cost_used / self.limits["max_cost_per_run"]) * 100
        if cost_pct >= self.limits["warn_threshold_pct"]:
            result["warnings"].append(f"费用已达{self.limits['max_cost_per_run']}元的{cost_pct:.0f}%")
        if self.state.cost_used >= self.limits["max_cost_per_run"]:
            result["blockers"].append("费用已超上限")
            result["passed"] = False
        
        # API调用检查
        api_pct = (self.state.api_calls_used / self.limits["max_api_calls_per_run"]) * 100
        if api_pct >= self.limits["warn_threshold_pct"]:
            result["warnings"].append(f"API调用已达{self.limits['max_api_calls_per_run']}次的{api_pct:.0f}%")
        if self.state.api_calls_used >= self.limits["max_api_calls_per_run"]:
            result["blockers"].append("API调用已超上限")
            result["passed"] = False
        
        # 付费操作检查
        if self.state.is_paid_op and self.limits["paid_ops_require_confirm"] and not self.state.is_confirmed:
            result["blockers"].append("付费操作需要--confirm确认")
            result["passed"] = False
        
        return result
    
    def record_api_call(self, cost: float = 0):
        self.state.api_calls_used += 1
        self.state.cost_used += cost
    
    def record_retry(self):
        self.state.retries_used += 1
        if self.state.retries_used > self.limits["max_retries_per_shot"]:
            return False
        return True
    
    def confirm_paid_op(self):
        self.state.is_confirmed = True
    
    def reset(self):
        self.state = BudgetState()
        self.start_time = datetime.now()
