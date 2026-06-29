"""
video_calibration.py — 视频前置校准层 (基于 开源视频生成框架 video_calibration.json 标准)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class GenerationMode(str, Enum):
    I2V_SINGLE_FIRST_FRAME = "I2V_SINGLE_FIRST_FRAME"
    I2V_FIRST_AND_LAST_FRAME = "I2V_FIRST_AND_LAST_FRAME"
    FLF2V = "FLF2V"
    TEXT_TO_VIDEO = "TEXT_TO_VIDEO"


class GateStatus(str, Enum):
    BLOCKED_FOR_PAID_BATCH = "BLOCKED_FOR_PAID_BATCH"
    ALLOW_DRY_RUN = "ALLOW_DRY_RUN"
    ALLOW_PAID_PILOT = "ALLOW_PAID_PILOT"
    ALLOW_BATCH = "ALLOW_BATCH"


@dataclass
class PresenceMap:
    """人物可见性约束"""
    humans_allowed: bool
    visible_characters_first_frame: List[str] = field(default_factory=list)
    visible_characters_last_frame: List[str] = field(default_factory=list)
    forbidden_entities: List[str] = field(default_factory=lambda: [
        "human", "cultivator", "monk", "sitting figure",
        "meditating person", "cross-legged pose",
        "new character", "new prop"
    ])

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ModeRecommendation:
    """生成模式推荐"""
    mode: GenerationMode
    forbidden_mode: Optional[GenerationMode] = None
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode.value,
            "forbidden_mode": self.forbidden_mode.value if self.forbidden_mode else None,
            "reason": self.reason
        }


@dataclass
class PromptLayers:
    """四层 prompt 结构"""
    asset_instruction: str = ""
    motion_layer: str = ""
    camera_layer: str = ""
    negative_guard_layer: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def compose(self) -> str:
        parts = []
        if self.asset_instruction:
            parts.append(self.asset_instruction)
        if self.motion_layer:
            parts.append(self.motion_layer)
        if self.camera_layer:
            parts.append(self.camera_layer)
        if self.negative_guard_layer:
            parts.append(self.negative_guard_layer)
        return "\n".join(parts)


@dataclass
class 视频生成模型LimitsCheck:
    """视频生成模型 2.0 限制检查"""
    prompt_chars: int = 0
    prompt_within_5000: bool = True
    image_count: int = 0
    video_count: int = 0
    audio_count: int = 0
    total_file_count: int = 0
    within_multimodal_limits: bool = True

    MAX_PROMPT_CHARS = 5000
    MAX_IMAGES = 9
    MAX_VIDEOS = 3
    MAX_AUDIO = 3
    MAX_TOTAL_FILES = 12

    def check(self, prompt: str, images: int = 0, videos: int = 0, audio: int = 0) -> bool:
        self.prompt_chars = len(prompt)
        self.prompt_within_5000 = self.prompt_chars <= self.MAX_PROMPT_CHARS
        self.image_count = images
        self.video_count = videos
        self.audio_count = audio
        self.total_file_count = images + videos + audio
        self.within_multimodal_limits = (
            self.image_count <= self.MAX_IMAGES and
            self.video_count <= self.MAX_VIDEOS and
            self.audio_count <= self.MAX_AUDIO and
            self.total_file_count <= self.MAX_TOTAL_FILES
        )
        return self.prompt_within_5000 and self.within_multimodal_limits

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prompt_chars": self.prompt_chars,
            "prompt_within_5000": self.prompt_within_5000,
            "image_count": self.image_count,
            "video_count": self.video_count,
            "audio_count": self.audio_count,
            "total_file_count": self.total_file_count,
            "within_multimodal_limits": self.within_multimodal_limits,
            "limits": {
                "MAX_PROMPT_CHARS": self.MAX_PROMPT_CHARS,
                "MAX_IMAGES": self.MAX_IMAGES,
                "MAX_VIDEOS": self.MAX_VIDEOS,
                "MAX_AUDIO": self.MAX_AUDIO,
                "MAX_TOTAL_FILES": self.MAX_TOTAL_FILES
            }
        }


@dataclass
class Gate:
    """付费提交前 Gate 状态"""
    status: GateStatus
    allow_dry_run: bool = True
    allow_paid_single_pilot_after_human_asset_and_ratio_gate: bool = False
    failure_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "allow_dry_run": self.allow_dry_run,
            "allow_paid_single_pilot_after_human_asset_and_ratio_gate": self.allow_paid_single_pilot_after_human_asset_and_ratio_gate,
            "failure_reasons": self.failure_reasons
        }


@dataclass
class VideoCalibration:
    """视频前置校准数据类"""
    schema_version: str = "video_calibration_v0.1"
    segment_id: str = ""
    root_cause_diagnosis: Dict[str, Any] = field(default_factory=dict)

    mode_recommendation: Optional[ModeRecommendation] = None
    duration_seconds: int = 5
    aspect_ratio: str = "9:16"
    expected_size: str = "720x1280"

    first_frame_path: Optional[str] = None
    last_frame_path: Optional[str] = None

    presence_map: Optional[PresenceMap] = None
    prompt_layers: Optional[PromptLayers] = None
    final_prompt: str = ""

    视频生成模型_limits_check: Optional[视频生成模型LimitsCheck] = field(default_factory=视频生成模型LimitsCheck)
    gate: Optional[Gate] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "segment_id": self.segment_id,
            "root_cause_diagnosis": self.root_cause_diagnosis,
            "duration_seconds": self.duration_seconds,
            "aspect_ratio": self.aspect_ratio,
            "expected_size": self.expected_size,
            "first_frame_path": self.first_frame_path,
            "last_frame_path": self.last_frame_path,
            "final_prompt": self.final_prompt,
        }
        if self.mode_recommendation:
            result["mode_recommendation"] = self.mode_recommendation.to_dict()
        if self.presence_map:
            result["presence_map"] = self.presence_map.to_dict()
        if self.prompt_layers:
            result["prompt_layers"] = self.prompt_layers.to_dict()
        if self.视频生成模型_limits_check:
            result["视频生成模型_limits_check"] = self.视频生成模型_limits_check.to_dict()
        if self.gate:
            result["gate"] = self.gate.to_dict()
        return result

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str | Path) -> VideoCalibration:
        path = Path(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        mode_rec = None
        if "mode_recommendation" in data and data["mode_recommendation"]:
            mr = data["mode_recommendation"]
            mode_rec = ModeRecommendation(
                mode=GenerationMode(mr["mode"]),
                forbidden_mode=GenerationMode(mr["forbidden_mode"]) if mr.get("forbidden_mode") else None,
                reason=mr.get("reason", "")
            )

        presence_map = None
        if "presence_map" in data and data["presence_map"]:
            pm = data["presence_map"]
            presence_map = PresenceMap(
                humans_allowed=pm["humans_allowed"],
                visible_characters_first_frame=pm.get("visible_characters_first_frame", []),
                visible_characters_last_frame=pm.get("visible_characters_last_frame", []),
                forbidden_entities=pm.get("forbidden_entities", [])
            )

        prompt_layers = None
        if "prompt_layers" in data and data["prompt_layers"]:
            pl = data["prompt_layers"]
            prompt_layers = PromptLayers(
                asset_instruction=pl.get("asset_instruction", ""),
                motion_layer=pl.get("motion_layer", ""),
                camera_layer=pl.get("camera_layer", ""),
                negative_guard_layer=pl.get("negative_guard_layer", "")
            )

        limits_check = None
        if "视频生成模型_limits_check" in data and data["视频生成模型_limits_check"]:
            lc = data["视频生成模型_limits_check"]
            limits_check = 视频生成模型LimitsCheck(
                prompt_chars=lc.get("prompt_chars", 0),
                prompt_within_5000=lc.get("prompt_within_5000", True),
                image_count=lc.get("image_count", 0),
                video_count=lc.get("video_count", 0),
                audio_count=lc.get("audio_count", 0),
                total_file_count=lc.get("total_file_count", 0),
                within_multimodal_limits=lc.get("within_multimodal_limits", True)
            )

        gate = None
        if "gate" in data and data["gate"]:
            g = data["gate"]
            gate = Gate(
                status=GateStatus(g["status"]),
                allow_dry_run=g.get("allow_dry_run", True),
                allow_paid_single_pilot_after_human_asset_and_ratio_gate=g.get("allow_paid_single_pilot_after_human_asset_and_ratio_gate", False),
                failure_reasons=g.get("failure_reasons", [])
            )

        return cls(
            schema_version=data.get("schema_version", "video_calibration_v0.1"),
            segment_id=data.get("segment_id", ""),
            root_cause_diagnosis=data.get("root_cause_diagnosis", {}),
            mode_recommendation=mode_rec,
            duration_seconds=data.get("duration_seconds", 5),
            aspect_ratio=data.get("aspect_ratio", "9:16"),
            expected_size=data.get("expected_size", "720x1280"),
            first_frame_path=data.get("first_frame_path"),
            last_frame_path=data.get("last_frame_path"),
            presence_map=presence_map,
            prompt_layers=prompt_layers,
            final_prompt=data.get("final_prompt", ""),
            视频生成模型_limits_check=limits_check,
            gate=gate
        )

    def validate_for_paid_batch(self) -> List[str]:
        failures = []

        if not self.segment_id:
            failures.append("segment_id is empty")

        if self.视频生成模型_limits_check and not self.视频生成模型_limits_check.prompt_within_5000:
            failures.append(f"prompt too long: {self.视频生成模型_limits_check.prompt_chars} > 5000")

        if self.视频生成模型_limits_check and not self.视频生成模型_limits_check.within_multimodal_limits:
            failures.append(
                f"file count exceeded: image={self.视频生成模型_limits_check.image_count}, "
                f"video={self.视频生成模型_limits_check.video_count}, "
                f"audio={self.视频生成模型_limits_check.audio_count}, "
                f"total={self.视频生成模型_limits_check.total_file_count}"
            )

        if self.presence_map and not self.presence_map.humans_allowed:
            if self.mode_recommendation and self.mode_recommendation.mode == GenerationMode.FLF2V:
                failures.append("landscape with humans_allowed=false but mode is FLF2V")

        if self.presence_map and not self.presence_map.humans_allowed:
            if self.last_frame_path:
                failures.append("landscape has end_image_path, violates landscape rules")

        if self.presence_map and not self.presence_map.humans_allowed:
            if self.mode_recommendation and self.mode_recommendation.mode == GenerationMode.FLF2V:
                failures.append("landscape mode cannot be FLF2V")

        if self.expected_size != "720x1280":
            failures.append(f"expected_size is not 720x1280: {self.expected_size}")

        return failures

    def compute_gate(self) -> Gate:
        failures = self.validate_for_paid_batch()

        if not failures:
            return Gate(
                status=GateStatus.ALLOW_BATCH,
                allow_dry_run=True,
                allow_paid_single_pilot_after_human_asset_and_ratio_gate=True
            )

        dry_run_ok = True
        for failure in failures:
            if "too long" in failure or "exceeded" in failure:
                dry_run_ok = False
                break

        return Gate(
            status=GateStatus.BLOCKED_FOR_PAID_BATCH,
            allow_dry_run=dry_run_ok,
            allow_paid_single_pilot_after_human_asset_and_ratio_gate=False,
            failure_reasons=failures
        )


def make_empty_calibration(segment_id: str) -> VideoCalibration:
    return VideoCalibration(
        segment_id=segment_id,
        presence_map=PresenceMap(humans_allowed=True),
        mode_recommendation=ModeRecommendation(
            mode=GenerationMode.I2V_SINGLE_FIRST_FRAME,
            reason="default: single first frame I2V"
        ),
        gate=Gate(status=GateStatus.BLOCKED_FOR_PAID_BATCH)
    )


def make_landscape_calibration(segment_id: str, duration: int = 5) -> VideoCalibration:
    return VideoCalibration(
        segment_id=segment_id,
        presence_map=PresenceMap(
            humans_allowed=False,
            forbidden_entities=[
                "human", "cultivator", "monk", "sitting figure",
                "meditating person", "cross-legged pose",
                "new character", "new prop"
            ]
        ),
        mode_recommendation=ModeRecommendation(
            mode=GenerationMode.I2V_SINGLE_FIRST_FRAME,
            forbidden_mode=GenerationMode.FLF2V,
            reason="landscape, forbid human jump"
        ),
        prompt_layers=PromptLayers(
            negative_guard_layer="Landscape-only. No humans, no cultivators, no monks, "
                                 "no sitting figure, no meditating person, no cross-legged pose, "
                                 "no new characters, no new props."
        ),
        duration_seconds=duration,
        aspect_ratio="9:16",
        expected_size="720x1280",
        gate=Gate(status=GateStatus.BLOCKED_FOR_PAID_BATCH)
    )


def make_human_asset_calibration(
    segment_id: str,
    first_frame_path: str,
    character_ids: List[str],
    duration: int = 5
) -> VideoCalibration:
    return VideoCalibration(
        segment_id=segment_id,
        presence_map=PresenceMap(
            humans_allowed=True,
            visible_characters_first_frame=character_ids,
            visible_characters_last_frame=character_ids
        ),
        mode_recommendation=ModeRecommendation(
            mode=GenerationMode.I2V_SINGLE_FIRST_FRAME,
            reason="human-asset single first frame I2V"
        ),
        prompt_layers=PromptLayers(
            asset_instruction=f"参考<图片1>中的角色，保持外貌一致。",
            motion_layer="",
            camera_layer="",
            negative_guard_layer=""
        ),
        first_frame_path=first_frame_path,
        duration_seconds=duration,
        aspect_ratio="9:16",
        expected_size="720x1280",
        gate=Gate(status=GateStatus.BLOCKED_FOR_PAID_BATCH)
    )
