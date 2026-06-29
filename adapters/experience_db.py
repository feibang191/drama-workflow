"""Phase 1-3: 跨项目经验库 — 成功/失败样本 + 模型能力边界"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
import json, os

@dataclass
class ExperienceSample:
    project_id: str; shot_id: str
    complexity_level: str; model: str; mode: str  # T2V/I2V/FLF2V
    result: str  # success/failure
    scores: Dict[str, float] = field(default_factory=dict)
    fail_category: str = ""
    severity: str = ""
    recovery_action: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class ExperienceDB:
    def __init__(self, db_path: str = ""):
        self.db_path = db_path or ""
        self.success_patterns: List[ExperienceSample] = []
        self.failure_patterns: List[ExperienceSample] = []
        self.model_capability: Dict[str, Dict] = {}
    
    def record(self, sample: ExperienceSample):
        if sample.result == "success":
            self.success_patterns.append(sample)
        else:
            self.failure_patterns.append(sample)
    
    def query(self, model: str = "", level: str = "", motion: str = "",
              limit: int = 5) -> Dict:
        """查询经验库"""
        results = {"success_rate": 0, "total": 0, "samples": [], "warnings": []}
        
        # 匹配成功样本
        matched = []
        for s in self.success_patterns + self.failure_patterns:
            if model and s.model != model: continue
            if level and s.complexity_level != level: continue
            matched.append(s)
        
        if matched:
            successes = sum(1 for s in matched if s.result == "success")
            results["total"] = len(matched)
            results["success_rate"] = round(successes / len(matched) * 100, 1)
            results["samples"] = matched[:limit]
        
        return results
    
    def to_json(self) -> Dict:
        return {
            "success_count": len(self.success_patterns),
            "failure_count": len(self.failure_patterns),
            "model_capability": self.model_capability,
        }
    
    def save(self, path: str = ""):
        path = path or self.db_path
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.to_json(), f, ensure_ascii=False, indent=2)
    
    def load(self, path: str = ""):
        path = path or self.db_path
        if path and os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
