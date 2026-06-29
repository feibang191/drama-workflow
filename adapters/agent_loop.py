"""
Agent Loop — 基于 开源视频生成框架 AgentLoop 吸收

Agent 状态机调度，支持重试/回退/持久化，增强渲染鲁棒性。
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


@dataclass
class AgentState:
    """Agent 状态"""
    state: str  # idle / running / paused / failed / completed
    step: int
    total_steps: int
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentStep:
    """Agent 步骤"""
    step_id: str
    step_name: str
    status: str  # pending / running / completed / failed
    input_data: Optional[Dict] = None
    output_data: Optional[Dict] = None
    error: Optional[str] = None
    duration_ms: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AgentLoop:
    """Agent 状态机"""
    
    def __init__(self, agent_id: str, steps: List[Callable]):
        self.agent_id = agent_id
        self.steps = steps
        self.state = AgentState(
            state="idle",
            step=0,
            total_steps=len(steps),
        )
        self.step_results: List[AgentStep] = []
        self.context: Dict[str, Any] = {}
    
    def run(self, initial_context: Optional[Dict] = None) -> Dict[str, Any]:
        """执行 Agent 循环"""
        if initial_context:
            self.context.update(initial_context)
        
        self.state.state = "running"
        self.state.started_at = time.time()
        
        for i, step_func in enumerate(self.steps):
            self.state.step = i + 1
            step_name = getattr(step_func, "__name__", f"step_{i}")
            
            step = AgentStep(
                step_id=f"step_{i:02d}",
                step_name=step_name,
                status="running",
                input_data=dict(self.context),
            )
            
            try:
                result = step_func(self.context)
                step.status = "completed"
                step.output_data = result
                self.context.update(result if isinstance(result, dict) else {})
            except Exception as e:
                step.status = "failed"
                step.error = str(e)
                step.duration_ms = int((time.time() - (self.state.started_at or time.time())) * 1000)
                
                if self.state.retry_count < self.state.max_retries:
                    self.state.retry_count += 1
                    step.status = "retrying"
                    continue
                
                self.state.state = "failed"
                self.state.error = str(e)
                self.state.completed_at = time.time()
                self.step_results.append(step)
                return self._build_result()
            
            step.duration_ms = int((time.time() - (self.state.started_at or time.time())) * 1000)
            self.step_results.append(step)
        
        self.state.state = "completed"
        self.state.completed_at = time.time()
        return self._build_result()
    
    def _build_result(self) -> Dict[str, Any]:
        """构建结果"""
        return {
            "agent_id": self.agent_id,
            "state": self.state.state,
            "step": self.state.step,
            "total_steps": self.state.total_steps,
            "retry_count": self.state.retry_count,
            "steps": [s.to_dict() for s in self.step_results],
            "context": self.context,
        }


__all__ = [
    "AgentState",
    "AgentStep",
    "AgentLoop",
]
