"""
Event Extractor — 基于 开源视频生成框架 EventExtractor 吸收

从剧本提取事件链，识别关键转折点和高潮，辅助分镜规划。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Event:
    """事件"""
    event_id: str
    event_type: str  # setup / confrontation / climax / resolution
    description: str
    characters_involved: List[str]
    location: str
    emotional_tone: str  # tension / relief / joy / sorrow
    importance: float  # 0.0 - 1.0
    timestamp: Optional[float] = None  # 剧本时间戳(秒)
    preceding_event: Optional[str] = None
    following_event: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EventChain:
    """事件链"""
    events: List[Event]
    key_turning_points: List[str]
    climax_event_id: str
    total_duration: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "events": [e.to_dict() for e in self.events],
            "key_turning_points": self.key_turning_points,
            "climax_event_id": self.climax_event_id,
            "total_duration": self.total_duration,
        }


def extract_events_from_script(
    script_text: str,
    scene_breakdown: Optional[List[Dict]] = None,
) -> EventChain:
    """
    从剧本提取事件链
    
    Args:
        script_text: 剧本文本
        scene_breakdown: 场景分解（可选）
    
    Returns:
        EventChain
    """
    events = []
    lines = script_text.split("\n")
    
    current_event_id = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 识别事件类型
        event_type = classify_event(line)
        if event_type:
            current_event_id += 1
            events.append(Event(
                event_id=f"EV{current_event_id:03d}",
                event_type=event_type,
                description=line[:200],
                characters_involved=[],
                location="",
                emotional_tone="neutral",
                importance=calculate_importance(event_type, line),
            ))
    
    # 识别关键转折点（降低阈值到 0.5，因为 classify_event 可能返回 None）
    turning_points = [
        e.event_id for e in events 
        if e.importance >= 0.5 and e.event_type in ("setup", "confrontation", "climax", "resolution")
    ]
    
    # 识别高潮
    climax = max(events, key=lambda e: e.importance) if events else None
    
    return EventChain(
        events=events,
        key_turning_points=turning_points,
        climax_event_id=climax.event_id if climax else "",
        total_duration=len(events) * 5.0,  # 估算
    )


def classify_event(line: str) -> Optional[str]:
    """分类事件类型"""
    setup_keywords = ["开始", "来到", "发现", "遇见", "走进"]
    confrontation_keywords = ["冲突", "争吵", "对抗", "战斗", "对决", "但是", "然而"]
    climax_keywords = ["高潮", "爆发", "决裂", "真相", "揭露", "逆转"]
    resolution_keywords = ["结束", "离开", "和解", "原谅", "告别"]
    
    for kw in setup_keywords:
        if kw in line:
            return "setup"
    for kw in confrontation_keywords:
        if kw in line:
            return "confrontation"
    for kw in climax_keywords:
        if kw in line:
            return "climax"
    for kw in resolution_keywords:
        if kw in line:
            return "resolution"
    
    return None


def calculate_importance(event_type: str, line: str) -> float:
    """计算事件重要性"""
    base_scores = {
        "setup": 0.3,
        "confrontation": 0.6,
        "climax": 0.9,
        "resolution": 0.4,
    }
    score = base_scores.get(event_type, 0.5)
    
    # 长句通常更重要
    if len(line) > 100:
        score += 0.1
    
    return min(1.0, score)


__all__ = [
    "Event",
    "EventChain",
    "extract_events_from_script",
    "classify_event",
    "calculate_importance",
]
