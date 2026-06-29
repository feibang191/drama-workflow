"""
Novel Compressor — 基于 开源视频生成框架 NovelCompressor 吸收

小说→分集智能压缩引擎。
保留核心情节，去除冗余描写，适配视频时长约束。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class CompressedScene:
    """压缩后的场景"""
    scene_id: str
    original_length: int  # 原文字数
    compressed_length: int  # 压缩后字数
    compression_ratio: float
    key_points: List[str]
    removed_details: List[str]
    video_duration_estimate: float  # 预估视频时长(秒)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CompressionResult:
    """压缩结果"""
    original_text: str
    compressed_text: str
    scenes: List[CompressedScene]
    total_original_chars: int
    total_compressed_chars: int
    overall_ratio: float
    episodes: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_text": self.original_text,
            "compressed_text": self.compressed_text,
            "scenes": [s.to_dict() for s in self.scenes],
            "total_original_chars": self.total_original_chars,
            "total_compressed_chars": self.total_compressed_chars,
            "overall_ratio": self.overall_ratio,
            "episodes": self.episodes,
        }


def compress_novel_to_episodes(
    novel_text: str,
    target_episode_count: int = 12,
    max_chars_per_episode: int = 3000,
) -> CompressionResult:
    """
    将小说压缩为分集剧本
    
    Args:
        novel_text: 原始小说文本
        target_episode_count: 目标集数
        max_chars_per_episode: 每集最大字数
    
    Returns:
        CompressionResult
    """
    # 1. 按段落分割
    paragraphs = [p.strip() for p in novel_text.split("\n") if p.strip()]
    
    # 2. 识别场景边界（按关键词或空行）
    scene_markers = ["第", "章", "节", "幕", "Scene"]
    scenes = []
    current_scene = []
    current_scene_id = 0
    
    for para in paragraphs:
        if any(para.startswith(m) for m in scene_markers):
            if current_scene:
                scenes.append(current_scene)
                current_scene_id += 1
            current_scene = [para]
        else:
            current_scene.append(para)
    
    if current_scene:
        scenes.append(current_scene)
    
    # 3. 分配场景到集数
    scenes_per_episode = len(scenes) // target_episode_count
    episodes = []
    
    for ep_idx in range(target_episode_count):
        start = ep_idx * scenes_per_episode
        end = start + scenes_per_episode if ep_idx < target_episode_count - 1 else len(scenes)
        episode_scenes = scenes[start:end]
        
        episode_text = "\n".join(["\n".join(s) for s in episode_scenes])
        compressed = compress_paragraphs(episode_scenes)
        
        episodes.append({
            "episode_id": f"EP{ep_idx+1:02d}",
            "scenes": episode_scenes,
            "original_text": episode_text,
            "compressed_text": compressed,
            "scene_count": len(episode_scenes),
        })
    
    total_original = sum(len("".join(s)) for s in scenes)
    total_compressed = sum(len(e["compressed_text"]) for e in episodes)
    
    return CompressionResult(
        original_text=novel_text,
        compressed_text="\n".join(e["compressed_text"] for e in episodes),
        scenes=[
            CompressedScene(
                scene_id=f"SC{i+1:02d}",
                original_length=sum(len(p) for p in scene),
                compressed_length=0,
                compression_ratio=0.7,
                key_points=[],
                removed_details=[],
                video_duration_estimate=len(scene) * 5.0,
            )
            for i, scene in enumerate(scenes)
        ],
        total_original_chars=total_original,
        total_compressed_chars=total_compressed,
        overall_ratio=total_compressed / total_original if total_original > 0 else 0,
        episodes=episodes,
    )


def compress_paragraphs(paragraphs: List[List[str]]) -> str:
    """压缩段落列表，去除冗余"""
    compressed = []
    for para_group in paragraphs:
        # 保留关键句，去除修饰性描写
        key_sentences = []
        for para in para_group:
            # 简单启发式：保留包含对话、动作、转折的句子
            if any(marker in para for marker in [":", "!", "?", "但是", "然而", "突然", "终于"]):
                key_sentences.append(para)
            elif len(para) > 50:  # 保留较长的叙述句
                key_sentences.append(para[:100])  # 截断过长句子
        
        if key_sentences:
            compressed.append(" ".join(key_sentences[:3]))  # 最多保留3句
    
    return "\n".join(compressed)


__all__ = [
    "CompressedScene",
    "CompressionResult",
    "compress_novel_to_episodes",
    "compress_paragraphs",
]
