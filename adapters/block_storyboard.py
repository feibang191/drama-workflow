"""
P2-1 Block分镜系统 — 1Block=3Shot, 8条铁律
"""
from dataclasses import dataclass, field
from typing import List, Optional
from .shot_connector import extract_ending_state, detect_pose_break

@dataclass
class Shot:
    shot_id: str
    duration: float = 3.3
    description: str = ""
    first_frame_prompt: str = ""
    video_prompt: str = ""
    last_frame_prompt: str = ""
    dialogue: str = ""
    scene_id: str = ""
    camera: str = ""
    characters: list = field(default_factory=list)
    ending_pose: str = ""

@dataclass
class Block:
    block_id: str
    shots: List[Shot] = field(default_factory=list)
    scene_id: str = ""
    characters: list = field(default_factory=list)
    total_duration: float = 0.0

    def add_shot(self, shot):
        self.shots.append(shot)
        self.total_duration = sum(s.duration for s in self.shots)

    def is_complete(self):
        return len(self.shots) >= 3

    def audit(self):
        warnings = []
        if len(self.shots) < 3:
            warnings.append(f"Block不足3Shot(当前{len(self.shots)})")
        if self.total_duration > 12:
            warnings.append(f"超时: {self.total_duration:.0f}s")
        if len(self.shots) >= 2:
            for i in range(len(self.shots)-1):
                changes = detect_pose_break(self.shots[i].description, self.shots[i+1].description)
                warnings.extend(changes)
        return {"block_id": self.block_id, "shot_count": len(self.shots),
                "total_duration": self.total_duration, "complete": self.is_complete(),
                "warnings": warnings, "passed": len(warnings) == 0}

class BlockStoryboard:
    def __init__(self, blocks=None):
        self.blocks = blocks or []

    def add_block(self, block):
        self.blocks.append(block)

    def generate_blocks(self):
        return self.blocks

    def audit_blocks(self):
        return [b.audit() for b in self.blocks]

    def to_clip_contracts(self, project_id=""):
        from .schemas import make_clip_contract
        contracts = []
        for bi, block in enumerate(self.blocks):
            for si, shot in enumerate(block.shots):
                contracts.append(make_clip_contract(
                    project_id=project_id, clip_id=shot.shot_id,
                    sequence_index=si+1, narrative_job=shot.description[:60],
                    target_duration_sec=shot.duration, generation_mode="t2v",
                    shot_structure="compact_single_take", status="planned"))
        return contracts
