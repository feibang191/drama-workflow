"""
Reference Role System — 从 视频生成模型 2.0 参考素材角色分离吸收

每个参考素材（图片/视频/音频）在生成prompt时扮演特定角色。
同一段视频不能既是"身份参考"又是"运动参考"——角色必须分离。

参考角色类型（摘自 视频生成模型 2.0 reference-workflow.md）：
  - identity    : 角色身份（外貌/服装/妆容），跨clip不可变
  - environment : 场景环境（空间/光照/氛围）
  - motion      : 物体运动模式/节奏
  - camera_rhythm : 镜头运镜风格/剪辑节奏
  - audio_tempo   : 音频节奏/BGM情绪
  - style       : 整体视觉风格
  - endpoint    : 首帧/尾帧锁定参考
"""

from dataclasses import dataclass, field
from typing import Optional, List

# 参考角色定义
REFERENCE_ROLES = {
    "identity": {
        "label": "身份",
        "icon": "👤",
        "description": "角色外貌/服装/妆容，跨clip不可变",
        "allowed_media": ["image"],
        "persistence": "permanent",      # 整个项目不变
        "embed_position": "L1_L2",        # 主体定义层
    },
    "environment": {
        "label": "场景",
        "icon": "🏠",
        "description": "场景空间/光照/氛围",
        "allowed_media": ["image", "video"],
        "persistence": "per_scene",
        "embed_position": "L2",
    },
    "motion": {
        "label": "运动",
        "icon": "🏃",
        "description": "物体运动模式/节奏",
        "allowed_media": ["video"],
        "persistence": "per_clip",
        "embed_position": "L4",
    },
    "camera_rhythm": {
        "label": "镜头",
        "icon": "🎥",
        "description": "运镜风格/剪辑节奏参考",
        "allowed_media": ["video"],
        "persistence": "per_sequence",
        "embed_position": "L5",
    },
    "audio_tempo": {
        "label": "音频",
        "icon": "🎵",
        "description": "BGM节奏/情绪基调",
        "allowed_media": ["audio"],
        "persistence": "per_clip",
        "embed_position": "L6",
    },
    "style": {
        "label": "风格",
        "icon": "🎨",
        "description": "整体视觉风格参考",
        "allowed_media": ["image", "video"],
        "persistence": "per_project",
        "embed_position": "L5_L6",
    },
    "endpoint": {
        "label": "端点",
        "icon": "🔗",
        "description": "首帧/尾帧锁定",
        "allowed_media": ["image"],
        "persistence": "per_clip",
        "embed_position": "L3",
    },
}


@dataclass
class ReferenceAsset:
    """单个参考素材"""
    asset_id: str
    role: str               # 参考角色：identity/environment/motion/camera_rhythm/audio_tempo/style/endpoint
    media_type: str         # image/video/audio
    path: str               # 本地路径或URL
    description: str = ""   # 简短描述
    clip_id: str = ""       # 绑定的clip
    character_id: str = ""  # 绑定的角色（identity角色专用）
    active: bool = True

    def validate_role(self) -> bool:
        """检查媒体类型与角色是否匹配"""
        role_def = REFERENCE_ROLES.get(self.role)
        if not role_def:
            return False
        return self.media_type in role_def["allowed_media"]


class ReferenceRegistry:
    """参考素材注册表——追踪所有参考素材及其角色"""

    def __init__(self):
        self._assets: List[ReferenceAsset] = []

    def register(self, asset: ReferenceAsset) -> bool:
        """注册参考素材，角色不匹配时拒绝"""
        if not asset.validate_role():
            return False
        self._assets.append(asset)
        return True

    def get_by_role(self, role: str, clip_id: str = "") -> List[ReferenceAsset]:
        """按角色获取参考素材，可过滤clip"""
        results = []
        for a in self._assets:
            if a.role == role and a.active:
                if not clip_id or a.clip_id == clip_id:
                    results.append(a)
        return results

    def get_identity_refs(self, character_id: str = "") -> List[ReferenceAsset]:
        """获取角色身份参考"""
        results = self.get_by_role("identity")
        if character_id:
            results = [r for r in results if r.character_id == character_id]
        return results

    def get_scene_refs(self) -> List[ReferenceAsset]:
        """获取场景环境参考"""
        return self.get_by_role("environment")

    def get_motion_refs(self) -> List[ReferenceAsset]:
        """获取运动参考"""
        return self.get_by_role("motion")

    def get_endpoint_refs(self) -> List[ReferenceAsset]:
        """获取首尾帧参考"""
        return self.get_by_role("endpoint")

    def build_reference_block(self, clip_id: str = "") -> str:
        """生成prompt中的参考素材块"""
        lines = []
        for role_name, role_def in REFERENCE_ROLES.items():
            assets = self.get_by_role(role_name, clip_id)
            if not assets:
                continue
            for a in assets:
                tag = f"[{role_def['icon']}{role_def['label']}{a.asset_id}]"
                if a.description:
                    tag += f"({a.description})"
                lines.append(tag)
        return "\n".join(lines) if lines else ""

    def all_active(self) -> List[ReferenceAsset]:
        """所有活跃的参考素材"""
        return [a for a in self._assets if a.active]


# ---- 与metadata.py的集成接口 ----
def embed_reference_roles(registry: ReferenceRegistry, prompt_meta: dict) -> dict:
    """将参考角色信息嵌入到prompt元数据中"""
    prompt_meta["reference_roles"] = []
    for a in registry.all_active():
        prompt_meta["reference_roles"].append({
            "asset_id": a.asset_id,
            "role": a.role,
            "media_type": a.media_type,
            "clip_id": a.clip_id,
        })
    return prompt_meta


def role_match_check(asset: ReferenceAsset, clip_contract: dict) -> list:
    """检查参考素材与clip合同中的角色声明是否一致"""
    warnings = []
    contract_roles = clip_contract.get("reference_roles", [])
    if asset.role not in contract_roles:
        warnings.append(f"Asset {asset.asset_id} role={asset.role} not declared in clip contract")
    return warnings


def check_identity_persistence(registry: ReferenceRegistry, character_id: str, clip_id_a: str, clip_id_b: str) -> bool:
    """检查同一角色的身份参考在前后clip中是否一致"""
    refs_a = registry.get_identity_refs(character_id)
    refs_b = registry.get_identity_refs(character_id)
    ids_a = {r.asset_id for r in refs_a}
    ids_b = {r.asset_id for r in refs_b}
    return ids_a == ids_b
