"""
Scene Extractor — 基于 开源视频生成框架 SceneExtractor 吸收

从剧本自动提取场景要素，识别场景转换节点，生成场景参考图。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class SceneElement:
    """场景要素"""
    element_id: str
    element_type: str  # location / time / lighting / mood / props
    description: str
    importance: float  # 0.0 - 1.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Scene:
    """场景"""
    scene_id: str
    scene_name: str
    location: str
    time_of_day: str
    lighting: str
    mood: str
    elements: List[SceneElement]
    props: List[str]
    characters_present: List[str]
    transition_from: Optional[str] = None
    transition_to: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "scene_name": self.scene_name,
            "location": self.location,
            "time_of_day": self.time_of_day,
            "lighting": self.lighting,
            "mood": self.mood,
            "elements": [e.to_dict() for e in self.elements],
            "props": self.props,
            "characters_present": self.characters_present,
            "transition_from": self.transition_from,
            "transition_to": self.transition_to,
        }


def extract_scenes_from_script(
    script_text: str,
) -> List[Scene]:
    """
    从剧本提取场景
    
    Args:
        script_text: 剧本文本
    
    Returns:
        场景列表
    """
    scenes = []
    lines = script_text.split("\n")
    
    current_scene = None
    scene_id = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 识别场景标题
        if line.startswith("[") and "场景" in line:
            if current_scene:
                scenes.append(current_scene)
            scene_id += 1
            current_scene = Scene(
                scene_id=f"SC{scene_id:02d}",
                scene_name=line,
                location="",
                time_of_day="",
                lighting="",
                mood="",
                elements=[],
                props=[],
                characters_present=[],
            )
        elif current_scene:
            # 提取场景要素
            if "白天" in line or "夜晚" in line or "黄昏" in line:
                current_scene.time_of_day = line[:50]
            if "灯光" in line or "光线" in line:
                current_scene.lighting = line[:50]
            if "氛围" in line or "情绪" in line:
                current_scene.mood = line[:50]
    
    if current_scene:
        scenes.append(current_scene)
    
    return scenes


def identify_scene_transitions(scenes: List[Scene]) -> List[Scene]:
    """识别场景转换节点"""
    for i in range(len(scenes)):
        if i > 0:
            scenes[i].transition_from = scenes[i-1].scene_id
        if i < len(scenes) - 1:
            scenes[i].transition_to = scenes[i+1].scene_id
    return scenes


__all__ = [
    "SceneElement",
    "Scene",
    "extract_scenes_from_script",
    "identify_scene_transitions",
]
