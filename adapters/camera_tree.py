"""
Camera Tree 机制 — 基于 开源视频生成框架 camera_image_generator.py 吸收

管理同一场景内连续镜头的机位继承关系，确保跨镜头视觉连续性。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class CameraParentItem:
    """相机父子关系"""
    parent_cam_idx: Optional[int] = None
    parent_shot_idx: Optional[int] = None
    reason: str = ""
    is_parent_fully_covers_child: Optional[bool] = None
    missing_info: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Camera:
    """相机节点"""
    idx: int
    parent_cam_idx: Optional[int] = None
    parent_shot_idx: Optional[int] = None
    active_shot_idxs: List[int] = field(default_factory=list)
    reason: str = ""
    is_parent_fully_covers_child: Optional[bool] = None
    missing_info: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CameraTree:
    """相机树"""
    cameras: List[Camera] = field(default_factory=list)
    root_idx: int = 0  # 第一镜头为根

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cameras": [c.to_dict() for c in self.cameras],
            "root_idx": self.root_idx,
        }

    def get_camera(self, idx: int) -> Optional[Camera]:
        for cam in self.cameras:
            if cam.idx == idx:
                return cam
        return None

    def get_parent_chain(self, cam_idx: int) -> List[int]:
        """获取从根到当前相机的链"""
        chain = []
        cur = cam_idx
        visited = set()
        while cur is not None and cur not in visited:
            chain.append(cur)
            visited.add(cur)
            cam = self.get_camera(cur)
            cur = cam.parent_cam_idx if cam else None
        return list(reversed(chain))

    def get_priority_shot_idxs(self) -> List[int]:
        """获取其他机位依赖的镜头索引"""
        return [
            cam.parent_shot_idx for cam in self.cameras 
            if cam.parent_shot_idx is not None
        ]


def _group_shots_into_cameras(shot_descriptions: List[Dict]) -> List[Camera]:
    """将镜头按机位分组"""
    cameras_by_idx: Dict[int, Camera] = {}
    for shot_desc in shot_descriptions:
        cam_idx = shot_desc.get("cam_idx", 0)
        shot_idx = shot_desc.get("idx", 0)
        
        if cam_idx not in cameras_by_idx:
            cameras_by_idx[cam_idx] = Camera(idx=cam_idx, active_shot_idxs=[])
        
        cameras_by_idx[cam_idx].active_shot_idxs.append(shot_idx)
    
    return sorted(cameras_by_idx.values(), key=lambda c: c.idx)


def _validate_camera_tree(cameras: List[Camera]) -> List[str]:
    """验证相机树，防止循环和自引用"""
    errors = []
    
    # 检查自引用
    for cam in cameras:
        if cam.parent_cam_idx == cam.idx:
            errors.append(f"Camera {cam.idx} references itself")
    
    # 检查循环
    for i in range(len(cameras)):
        visited = set()
        cur = i
        while cur is not None:
            if cur in visited:
                errors.append(f"Cycle detected at camera {cur}")
                break
            visited.add(cur)
            cam = next((c for c in cameras if c.idx == cur), None)
            cur = cam.parent_cam_idx if cam else None
    
    return errors


def build_camera_tree(
    shot_descriptions: List[Dict],
    parent_cam_idx: Optional[int] = None,
    parent_shot_idx: Optional[int] = None,
) -> CameraTree:
    """
    构建相机树
    
    Args:
        shot_descriptions: 镜头描述列表，每个包含 idx, cam_idx, ff_desc, lf_desc
        parent_cam_idx: 父机位索引（用于递归构建）
        parent_shot_idx: 父镜头索引
    
    Returns:
        CameraTree 对象
    """
    # 1. 按机位分组
    cameras = _group_shots_into_cameras(shot_descriptions)
    
    # 2. 设置父子关系（简化版：每个机位的第一个镜头指向根机位的第一个镜头）
    root_cam = cameras[0] if cameras else None
    for i, cam in enumerate(cameras[1:], 1):
        if root_cam and root_cam.active_shot_idxs:
            cam.parent_cam_idx = root_cam.idx
            cam.parent_shot_idx = root_cam.active_shot_idxs[0]
            cam.reason = "Root camera provides context"
    
    # 3. 验证
    errors = _validate_camera_tree(cameras)
    if errors:
        raise ValueError(f"Camera tree validation failed: {errors}")
    
    # 4. 构建树
    tree = CameraTree(cameras=cameras, root_idx=0)
    return tree


def camera_tree_to_json(tree: CameraTree) -> str:
    """将 CameraTree 序列化为 JSON"""
    return json.dumps(tree.to_dict(), ensure_ascii=False, indent=2)


def load_camera_tree(path: str | Path) -> CameraTree:
    """从 JSON 文件加载 CameraTree"""
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    cameras = [Camera(**c) for c in data.get("cameras", [])]
    return CameraTree(cameras=cameras, root_idx=data.get("root_idx", 0))


def save_camera_tree(tree: CameraTree, path: str | Path):
    """保存 CameraTree 到 JSON 文件"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(camera_tree_to_json(tree))


# ── 工厂函数 ──

def make_simple_camera_tree(
    shot_count: int,
    cam_count: int = 1,
) -> CameraTree:
    """创建简单相机树（单机位或多机位）"""
    cameras = []
    shots_per_cam = shot_count // max(cam_count, 1)
    
    for cam_idx in range(cam_count):
        start_shot = cam_idx * shots_per_cam
        end_shot = start_shot + shots_per_cam if cam_idx < cam_count - 1 else shot_count
        active_shots = list(range(start_shot, end_shot))
        
        cam = Camera(
            idx=cam_idx,
            active_shot_idxs=active_shots,
        )
        
        # 非根机位指向根机位
        if cam_idx > 0:
            cam.parent_cam_idx = 0
            cam.parent_shot_idx = 0
            cam.reason = "Inherits from root camera"
        
        cameras.append(cam)
    
    return CameraTree(cameras=cameras, root_idx=0)


def validate_and_fix_camera_tree(tree: CameraTree) -> CameraTree:
    """验证并修复相机树"""
    errors = _validate_camera_tree(tree.cameras)
    if not errors:
        return tree
    
    # 修复：移除循环引用
    fixed_cameras = []
    for cam in tree.cameras:
        if cam.parent_cam_idx == cam.idx:
            cam.parent_cam_idx = None
            cam.parent_shot_idx = None
        fixed_cameras.append(cam)
    
    return CameraTree(cameras=fixed_cameras, root_idx=tree.root_idx)
