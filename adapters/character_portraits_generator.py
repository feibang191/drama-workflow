"""
Character Portraits Generator — 基于 开源视频生成框架 CharacterPortraitsGenerator 吸收

自动生成角色多视角肖像，支持 8 视图或 3in1 格式。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class PortraitView:
    """单个视角"""
    view_type: str  # front / side / back / three_quarter / close_up / action_pose
    description: str
    prompt: str
    image_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CharacterPortrait:
    """角色肖像"""
    character_id: str
    character_name: str
    views: List[PortraitView]
    style: str  # realistic / anime / watercolor / 3d
    format: str  # eight_view / three_in_one

    def to_dict(self) -> Dict[str, Any]:
        return {
            "character_id": self.character_id,
            "character_name": self.character_name,
            "views": [v.to_dict() for v in self.views],
            "style": self.style,
            "format": self.format,
        }


def generate_eight_view_portrait(
    character_id: str,
    character_name: str,
    appearance: Dict[str, str],
) -> CharacterPortrait:
    """
    生成 8 视图角色肖像
    
    8 视图：
    - 正面 x2 (正常/特写)
    - 侧面 x2 (左/右)
    - 背面 x2 (正常/特写)
    - 3/4侧 x2
    - 面部特写 x2
    - 动作姿态 x2
    """
    views = [
        PortraitView(view_type="front_normal", description="正面全身", prompt=build_prompt(character_name, appearance, "front", "normal")),
        PortraitView(view_type="front_closeup", description="正面特写", prompt=build_prompt(character_name, appearance, "front", "closeup")),
        PortraitView(view_type="side_left", description="左侧面", prompt=build_prompt(character_name, appearance, "side", "left")),
        PortraitView(view_type="side_right", description="右侧面", prompt=build_prompt(character_name, appearance, "side", "right")),
        PortraitView(view_type="back_normal", description="背面全身", prompt=build_prompt(character_name, appearance, "back", "normal")),
        PortraitView(view_type="back_closeup", description="背面特写", prompt=build_prompt(character_name, appearance, "back", "closeup")),
        PortraitView(view_type="three_quarter", description="3/4侧面", prompt=build_prompt(character_name, appearance, "three_quarter", "normal")),
        PortraitView(view_type="action_pose", description="动作姿态", prompt=build_prompt(character_name, appearance, "action", "pose")),
    ]
    
    return CharacterPortrait(
        character_id=character_id,
        character_name=character_name,
        views=views,
        style="realistic",
        format="eight_view",
    )


def generate_three_in_one_portrait(
    character_id: str,
    character_name: str,
    appearance: Dict[str, str],
) -> CharacterPortrait:
    """生成 3in1 角色肖像（正面+侧面+背面）"""
    views = [
        PortraitView(view_type="front", description="正面", prompt=build_prompt(character_name, appearance, "front", "normal")),
        PortraitView(view_type="side", description="侧面", prompt=build_prompt(character_name, appearance, "side", "normal")),
        PortraitView(view_type="back", description="背面", prompt=build_prompt(character_name, appearance, "back", "normal")),
    ]
    
    return CharacterPortrait(
        character_id=character_id,
        character_name=character_name,
        views=views,
        style="realistic",
        format="three_in_one",
    )


def build_prompt(
    character_name: str,
    appearance: Dict[str, str],
    view: str,
    detail: str,
) -> str:
    """构建角色肖像提示词"""
    parts = [
        f"{character_name} character portrait",
        f"{view} view, {detail}",
        f"hair: {appearance.get('hair', '')}",
        f"eyes: {appearance.get('eyes', '')}",
        f"face: {appearance.get('face', '')}",
        f"clothing: {appearance.get('clothing', '')}",
        f"accessories: {appearance.get('accessories', '')}",
        "clean background, consistent style",
    ]
    return " | ".join(parts)


__all__ = [
    "PortraitView",
    "CharacterPortrait",
    "generate_eight_view_portrait",
    "generate_three_in_one_portrait",
    "build_prompt",
]
