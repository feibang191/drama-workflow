"""元数据嵌入 — 将创作信息嵌入到生成文件(PNG/MP4)的元数据中

与 reference_role 打通：每个参考素材在元数据中标注其角色
"""
import json
from typing import Optional


def build_metadata(project_id: str, shot_id: str, prompt_spec: dict = None,
                   ref_assets: list = None, prompt_layers: dict = None) -> dict:
    """构建完整的元数据对象"""
    meta = {
        "schema": "drama-workflow/v4.3",
        "project_id": project_id,
        "shot_id": shot_id,
        "generated_at": "",
    }
    if prompt_spec:
        meta["prompt_spec"] = prompt_spec
    if ref_assets:
        meta["reference_roles"] = [
            {"asset_id": a.get("asset_id"), "role": a.get("role"),
             "media_type": a.get("media_type")}
            for a in ref_assets
        ]
    if prompt_layers:
        meta["prompt_layers"] = prompt_layers
    return meta


def embed_to_png(png_path: str, metadata: dict) -> str:
    """将元数据嵌入PNG文件(tEXt chunk) — TODO: 实际实现"""
    return png_path


def embed_to_mp4(mp4_path: str, metadata: dict) -> str:
    """将元数据嵌入MP4文件 — TODO: 实际实现"""
    return mp4_path
