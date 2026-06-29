"""
Reference Image Selector — 基于 开源视频生成框架 ReferenceImageSelector 吸收

从角色图、历史场景图、现有帧中挑选最相关的参考图，并生成"哪张图负责哪部分"的 prompt。
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ── 硬约束 ──

MAX_IMAGES = 9
MAX_VIDEOS = 3
MAX_AUDIO = 3
MAX_TOTAL_FILES = 12

# 实操建议：控制在 5-8 个文件，不要塞满
RECOMMENDED_MAX_FILES = 8


@dataclass
class ReferenceAsset:
    """参考素材"""
    asset_id: str
    role: str  # identity/environment/composition/motion/camera_rhythm/audio_tempo/style/endpoint
    media_type: str  # image/video/audio
    path: str
    description: str = ""
    clip_id: str = ""
    character_id: str = ""
    active: bool = True

    def validate_role(self) -> bool:
        """检查媒体类型与角色是否匹配"""
        role_def = REFERENCE_ROLES.get(self.role)
        if not role_def:
            return False
        return self.media_type in role_def["allowed_media"]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReferenceSet:
    """参考图集合"""
    assets: List[ReferenceAsset] = field(default_factory=list)
    scene_id: str = ""
    shot_id: str = ""

    def add_asset(self, asset: ReferenceAsset):
        """添加参考素材"""
        self.assets.append(asset)

    def validate_counts(self) -> Tuple[bool, str]:
        """验证数量约束"""
        images = sum(1 for a in self.assets if a.media_type == "image" and a.active)
        videos = sum(1 for a in self.assets if a.media_type == "video" and a.active)
        audio = sum(1 for a in self.assets if a.media_type == "audio" and a.active)
        total = images + videos + audio

        if images > MAX_IMAGES:
            return False, f"图片数量 {images} 超过上限 {MAX_IMAGES}"
        if videos > MAX_VIDEOS:
            return False, f"视频数量 {videos} 超过上限 {MAX_VIDEOS}"
        if audio > MAX_AUDIO:
            return False, f"音频数量 {audio} 超过上限 {MAX_AUDIO}"
        if total > MAX_TOTAL_FILES:
            return False, f"总文件数 {total} 超过上限 {MAX_TOTAL_FILES}"
        if total > RECOMMENDED_MAX_FILES:
            return True, f"警告：当前 {total} 个文件，建议不超过 {RECOMMENDED_MAX_FILES}"
        
        return True, "OK"

    def get_assets_by_role(self, role: str) -> List[ReferenceAsset]:
        """按角色获取素材"""
        return [a for a in self.assets if a.role == role and a.active]

    def to_prompt_instruction(self) -> str:
        """生成参考图说明（用于 prompt）"""
        lines = []
        
        # 按优先级排序：identity → environment → composition → motion → audio
        role_order = ["identity", "environment", "composition", "motion", "camera_rhythm", "audio_tempo", "style", "endpoint"]
        
        for role in role_order:
            assets = self.get_assets_by_role(role)
            if not assets:
                continue
            
            role_def = REFERENCE_ROLES.get(role, {})
            role_label = role_def.get("label", role)
            
            for asset in assets:
                idx = self.assets.index(asset) + 1
                if role == "identity":
                    lines.append(f"参考<图片{idx}>中的{asset.character_id}，保持外貌一致。")
                elif role == "environment":
                    lines.append(f"参考<图片{idx}>的场景构图和色调。")
                elif role == "composition":
                    lines.append(f"参考<图片{idx}>的构图方式。")
                elif role == "motion":
                    lines.append(f"参考<视频{idx}>的运动节奏。")
                elif role == "camera_rhythm":
                    lines.append(f"参考<视频{idx}>的运镜风格。")
                elif role == "audio_tempo":
                    lines.append(f"参考<音频{idx}>的节奏。")
                elif role == "style":
                    lines.append(f"参考<图片{idx}>的整体视觉风格。")
                elif role == "endpoint":
                    lines.append(f"参考<图片{idx}>锁定首帧/尾帧。")
        
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assets": [a.to_dict() for a in self.assets],
            "scene_id": self.scene_id,
            "shot_id": self.shot_id,
        }


# ── 选择器函数 ──

def select_reference_images_for_shot(
    available_assets: List[ReferenceAsset],
    shot_description: Dict,
    max_images: int = MAX_IMAGES,
) -> List[ReferenceAsset]:
    """
    为单个镜头选择参考图
    
    优先级：
    1. identity (必须有)
    2. environment (强烈建议)
    3. composition (建议)
    4. motion (可选)
    """
    selected = []
    
    # 1. 角色身份
    identity_assets = [a for a in available_assets if a.role == "identity" and a.active]
    if identity_assets:
        selected.extend(identity_assets[:1])  # 至少一个
    
    # 2. 场景环境
    env_assets = [a for a in available_assets if a.role == "environment" and a.active]
    if env_assets and len(selected) < max_images:
        selected.extend(env_assets[:1])
    
    # 3. 构图锚点
    comp_assets = [a for a in available_assets if a.role == "composition" and a.active]
    if comp_assets and len(selected) < max_images:
        selected.extend(comp_assets[:1])
    
    # 4. 运动参考
    motion_assets = [a for a in available_assets if a.role == "motion" and a.active]
    if motion_assets and len(selected) < max_images:
        selected.extend(motion_assets[:1])
    
    return selected[:max_images]


def create_reference_set_for_scene(
    character_portraits: List[ReferenceAsset],
    scene_references: List[ReferenceAsset],
    shot_description: Dict,
) -> ReferenceSet:
    """
    为场景创建参考图集合
    
    Args:
        character_portraits: 角色肖像列表
        scene_references: 场景参考图列表
        shot_description: 镜头描述
    
    Returns:
        ReferenceSet
    """
    ref_set = ReferenceSet(
        scene_id=shot_description.get("scene_id", ""),
        shot_id=shot_description.get("idx", ""),
    )
    
    # 添加角色身份参考
    for portrait in character_portraits:
        if portrait.active:
            asset = ReferenceAsset(
                asset_id=f"char_{portrait.asset_id}",
                role="identity",
                media_type=portrait.media_type,
                path=portrait.path,
                description=portrait.description,
                character_id=portrait.character_id,
            )
            ref_set.add_asset(asset)
    
    # 添加场景参考
    for scene_ref in scene_references:
        if scene_ref.active:
            ref_set.add_asset(scene_ref)
    
    return ref_set


def format_reference_instruction(reference_set: ReferenceSet) -> str:
    """
    生成参考图说明（用于 prompt）
    
    这是 开源视频生成框架 ReferenceImageSelector 的核心输出
    """
    return reference_set.to_prompt_instruction()


# ── 验证函数 ──

def validate_reference_count(
    images: int = 0,
    videos: int = 0,
    audio: int = 0,
) -> Tuple[bool, str]:
    """验证参考图数量"""
    total = images + videos + audio
    
    if images > MAX_IMAGES:
        return False, f"图片数量 {images} 超过上限 {MAX_IMAGES}"
    if videos > MAX_VIDEOS:
        return False, f"视频数量 {videos} 超过上限 {MAX_VIDEOS}"
    if audio > MAX_AUDIO:
        return False, f"音频数量 {audio} 超过上限 {MAX_AUDIO}"
    if total > MAX_TOTAL_FILES:
        return False, f"总文件数 {total} 超过上限 {MAX_TOTAL_FILES}"
    if total > RECOMMENDED_MAX_FILES:
        return True, f"警告：当前 {total} 个文件，建议不超过 {RECOMMENDED_MAX_FILES}"
    
    return True, "OK"


# ── 导出 ──

__all__ = [
    "ReferenceAsset", "ReferenceSet",
    "select_reference_images_for_shot",
    "create_reference_set_for_scene",
    "format_reference_instruction",
    "validate_reference_count",
    "MAX_IMAGES", "MAX_VIDEOS", "MAX_AUDIO", "MAX_TOTAL_FILES",
]
