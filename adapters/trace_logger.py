"""Phase 1-5: 结构化Trace引擎 — Stage级运行记录"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
import json, os
import time

MAX_TRACE_RECORDS = 200

@dataclass
class TraceRecord:
    stage_id: str
    stage_name: str
    start_at: float  # timestamp
    end_at: Optional[float] = None
    duration_ms: int = 0
    api_calls: List[Dict] = field(default_factory=list)
    total_cost: float = 0.0
    errors: List[str] = field(default_factory=list)
    status: str = "running"  # running/done/failed
    metadata: Dict = field(default_factory=dict)

class PipelineTracer:
    def __init__(self, project_path: str = ""):
        self.project_path = project_path
        self.records: List[TraceRecord] = []
        self._current: Optional[TraceRecord] = None
    
    def start_stage(self, stage_id: str, stage_name: str):
        self._current = TraceRecord(stage_id=stage_id, stage_name=stage_name,
                                     start_at=time.time())
        self.records.append(self._current)
        return self
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_stage("failed" if exc_type else "done")
        return False
    
    def end_stage(self, status: str = "done"):
        if self._current:
            self._current.end_at = time.time()
            self._current.duration_ms = int((self._current.end_at - self._current.start_at) * 1000)
            self._current.status = status
    
    def api_call(self, name: str, shot_id: str = "", status: str = "ok", cost: float = 0):
        if self._current:
            call = {"name": name, "shot_id": shot_id, "status": status, "cost": cost}
            self._current.api_calls.append(call)
            self._current.total_cost += cost
    
    def add_error(self, error: str):
        if self._current:
            self._current.errors.append(error)
    
    def add_meta(self, key: str, value):
        if self._current:
            self._current.metadata[key] = value
    
    def summary(self) -> Dict:
        """汇总统计"""
        total_cost = sum(r.total_cost for r in self.records)
        total_duration = sum(r.duration_ms for r in self.records)
        api_counts = sum(len(r.api_calls) for r in self.records)
        err_counts = sum(len(r.errors) for r in self.records)
        return {
            "stages": len(self.records),
            "total_cost": round(total_cost, 2),
            "total_duration_ms": total_duration,
            "api_calls": api_counts,
            "errors": err_counts,
            "statuses": {s: sum(1 for r in self.records if r.status == s) for s in {"done","failed","running"}},
        }
    
    def to_json(self) -> List[Dict]:
        records = []
        for r in self.records[-MAX_TRACE_RECORDS:]:
            records.append({
                "stage_id": r.stage_id, "stage_name": r.stage_name,
                "duration_ms": r.duration_ms, "api_calls": len(r.api_calls),
                "total_cost": r.total_cost, "errors": r.errors, "status": r.status,
            })
        return records
