"""Phase 1-8: Pipeline仪表盘 — 扫描项目状态+终端友好输出"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import os

@dataclass
class ProjectStatus:
    name: str
    gate_phase: str = ""      # 0a-7
    gate_status: str = ""     # done/running/blocked/pending
    shot_count: int = 0
    video_count: int = 0
    total_cost: float = 0.0
    stages: Dict[str, str] = field(default_factory=dict)

class PipelineDashboard:
    def __init__(self, projects_root: str = ""):
        self.projects_root = projects_root
        self.projects: List[ProjectStatus] = []
    
    def scan(self) -> List[ProjectStatus]:
        """扫描目录下的所有项目"""
        self.projects = []
        if not self.projects_root or not os.path.exists(self.projects_root):
            return self.projects
        
        for item in sorted(os.listdir(self.projects_root)):
            proj_dir = os.path.join(self.projects_root, item)
            if not os.path.isdir(proj_dir):
                continue
            ps = ProjectStatus(name=item)
            # 尝试读取gate
            gate_path = os.path.join(proj_dir, "ctl", "gate.json")
            if os.path.exists(gate_path):
                import json
                with open(gate_path, 'r', encoding='utf-8') as f:
                    try:
                        gate = json.load(f)
                        ps.gate_phase = gate.get("phase", "")
                        ps.gate_status = gate.get("status", "")
                    except: pass
            
            # 统计shot/视频
            storyboard_dir = os.path.join(proj_dir, "shot_analysis")
            if os.path.exists(storyboard_dir):
                ps.shot_count = len([f for f in os.listdir(storyboard_dir) if f.endswith('.json')])
            vid_dir = os.path.join(proj_dir, "vid", "out")
            if os.path.exists(vid_dir):
                ps.video_count = len([f for f in os.listdir(vid_dir) if f.endswith(('.mp4','.webm'))])
            
            self.projects.append(ps)
        
        return self.projects
    
    def render_terminal(self) -> str:
        """生成终端友好输出"""
        if not self.projects:
            return "╔══ Pipeline Dashboard (空) ══╗\n\n  没有项目数据\n"
        
        lines = []
        lines.append("╔══ Pipeline Dashboard ══╗")
        lines.append(f"  项目数: {len(self.projects)}")
        lines.append("")
        
        for ps in self.projects:
            status_icon = {"done":"✅","running":"🔄","blocked":"⛔","pending":"⏳","":"❓"}.get(ps.gate_status,"❓")
            lines.append(f"  {status_icon} {ps.name}")
            lines.append(f"     Phase: {ps.gate_phase or '-'} | Shots: {ps.shot_count} | Videos: {ps.video_count} | Cost: ¥{ps.total_cost:.2f}") 
        
        return "\n".join(lines)
    
    def json(self) -> List[Dict]:
        return [{
            "name": p.name, "gate_phase": p.gate_phase,
            "gate_status": p.gate_status, "shots": p.shot_count,
            "videos": p.video_count, "cost": p.total_cost,
        } for p in self.projects]
