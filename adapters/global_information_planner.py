"""
Global Information Planner — 基于 开源视频生成框架 GlobalInformationPlanner 吸收

全局信息规划，统筹角色/场景/道具/情绪，生成全局一致性约束。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class GlobalConstraint:
    """全局约束"""
    constraint_id: str
    constraint_type: str  # character / scene / prop / emotion / style
    description: str
    scope: str  # episode / scene / shot
    value: str
    priority: str  # high / medium / low

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GlobalPlan:
    """全局规划"""
    project_id: str
    constraints: List[GlobalConstraint]
    character_consistency: Dict[str, Any]
    scene_consistency: Dict[str, Any]
    prop_consistency: Dict[str, Any]
    emotion_curve: List[Dict[str, Any]]
    style_guide: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "constraints": [c.to_dict() for c in self.constraints],
            "character_consistency": self.character_consistency,
            "scene_consistency": self.scene_consistency,
            "prop_consistency": self.prop_consistency,
            "emotion_curve": self.emotion_curve,
            "style_guide": self.style_guide,
        }


def create_global_plan(
    project_id: str,
    characters: List[Dict],
    scenes: List[Dict],
    props: List[Dict],
    emotion_curve: List[Dict],
    style_guide: Dict,
) -> GlobalPlan:
    """
    创建全局规划
    
    Args:
        project_id: 项目ID
        characters: 角色列表
        scenes: 场景列表
        props: 道具列表
        emotion_curve: 情绪曲线
        style_guide: 风格指南
    
    Returns:
        GlobalPlan
    """
    constraints = []
    
    # 角色一致性约束
    for char in characters:
        constraints.append(GlobalConstraint(
            constraint_id=f"CHAR_{char.get('id', '')}",
            constraint_type="character",
            description=f"角色 {char.get('name', '')} 外貌一致性",
            scope="episode",
            value=json.dumps(char.get('appearance', {})),
            priority="high",
        ))
    
    # 场景一致性约束
    for scene in scenes:
        constraints.append(GlobalConstraint(
            constraint_id=f"SCENE_{scene.get('id', '')}",
            constraint_type="scene",
            description=f"场景 {scene.get('name', '')} 空间一致性",
            scope="scene",
            value=json.dumps(scene.get('layout', {})),
            priority="medium",
        ))
    
    # 道具一致性约束
    for prop in props:
        constraints.append(GlobalConstraint(
            constraint_id=f"PROP_{prop.get('id', '')}",
            constraint_type="prop",
            description=f"道具 {prop.get('name', '')} 形态一致性",
            scope="shot",
            value=json.dumps(prop.get('description', {})),
            priority="medium",
        ))
    
    return GlobalPlan(
        project_id=project_id,
        constraints=constraints,
        character_consistency={c.constraint_id: c.value for c in constraints if c.constraint_type == "character"},
        scene_consistency={c.constraint_id: c.value for c in constraints if c.constraint_type == "scene"},
        prop_consistency={c.constraint_id: c.value for c in constraints if c.constraint_type == "prop"},
        emotion_curve=emotion_curve,
        style_guide=style_guide,
    )


__all__ = [
    "GlobalConstraint",
    "GlobalPlan",
    "create_global_plan",
]
