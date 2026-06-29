"""Phase 1-6: 本地回退引擎 — 4级降级策略 + 指数退避 + 缓存"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json, os, time

# 4级降级
DEGRADE_LEVELS = [
    {"level": "L0", "resolution": "720p", "duration": 10, "label": "标准"},
    {"level": "L1", "resolution": "480p", "duration": 8, "label": "降分辨率"},
    {"level": "L2", "resolution": "480p", "duration": 5, "label": "降分辨率+时长"},
    {"level": "L3", "resolution": "360p", "duration": 5, "label": "最低画质"},
]

# 指数退避: 5s -> 10s -> 20s -> 40s -> 80s -> 120s(max)
BACKOFF_SCHEDULE = [5, 10, 20, 40, 80, 120]

@dataclass
class FallbackJob:
    shot_id: str
    prompt_data: Dict = field(default_factory=dict)
    retry_count: int = 0
    current_degrade: int = 0  # index into DEGRADE_LEVELS
    status: str = "pending"  # pending/running/exhausted/success
    error_log: List[str] = field(default_factory=list)

class FallbackManager:
    def __init__(self, project_path: str = ""):
        self.project_path = project_path
        self.queue: List[FallbackJob] = []
    
    def enqueue(self, shot_id: str, prompt_data: Optional[Dict] = None):
        """将失败shot加入回退队列"""
        self.queue.append(FallbackJob(shot_id=shot_id, prompt_data=prompt_data or {}))
        return len(self.queue)
    
    def get_next(self) -> Optional[FallbackJob]:
        """获取下一个待处理任务"""
        for job in self.queue:
            if job.status == "pending":
                return job
        return None
    
    def get_degrade_config(self, job: FallbackJob) -> Dict:
        """获取当前降级配置"""
        idx = min(job.current_degrade, len(DEGRADE_LEVELS) - 1)
        return DEGRADE_LEVELS[idx]
    
    def get_backoff_seconds(self, retry_count: int) -> int:
        """指数退避"""
        idx = min(retry_count, len(BACKOFF_SCHEDULE) - 1)
        return BACKOFF_SCHEDULE[idx]
    
    def retry(self, job: FallbackJob) -> bool:
        """执行一次重试，返回True=继续 False=耗尽"""
        if job.retry_count >= 6:  # 6次 = exhaust
            job.status = "exhausted"
            return False
        
        wait = self.get_backoff_seconds(job.retry_count)
        job.retry_count += 1
        
        # 每2次重试升一级降级
        if job.retry_count % 2 == 0:
            job.current_degrade = min(job.current_degrade + 1, len(DEGRADE_LEVELS) - 1)
        
        return True
    
    def mark_success(self, job: FallbackJob):
        job.status = "success"
    
    def mark_exhausted(self, job: FallbackJob, reason: str):
        job.status = "exhausted"
        job.error_log.append(reason)
    
    def status_summary(self) -> Dict:
        return {
            "total": len(self.queue),
            "pending": sum(1 for j in self.queue if j.status == "pending"),
            "running": sum(1 for j in self.queue if j.status == "running"),
            "success": sum(1 for j in self.queue if j.status == "success"),
            "exhausted": sum(1 for j in self.queue if j.status == "exhausted"),
        }
