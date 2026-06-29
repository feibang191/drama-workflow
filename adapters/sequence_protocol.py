"""
Sequence Protocol — 从 视频生成模型 2.0 连续性协议吸收

核心概念：
  1. 每 clip 有明确的状态契约（起始状态 → 结束状态）
  2. 下一 clip 的起始状态 = 已接受 clip 的**实际**结束状态（不是计划状态）
  3. 三级范围控制：already_happened / this_clip_only / reserved_for_later
  4. 连续性锁（continuity_locks）和 允许变化（allowed_changes）

与 shot_connector.py 的关系：
  shot_connector 处理单镜头内的动作惯性（P1级别）
  sequence_protocol 处理多clip间的叙事连续性和状态管理（P2+级别）
"""

from dataclasses import dataclass, field
from typing import Optional
from .schemas import make_clip_contract, make_prompt_spec, validate

# 参考角色类型（from 视频生成模型 2.0）
REFERENCE_ROLES = {
    "identity": "角色身份：外貌/服装/妆容，固定的跨clip不变",
    "environment": "环境：场景空间/光照/氛围",
    "motion": "运动：物体的运动模式/节奏",
    "camera_rhythm": "镜头节奏：运镜风格/剪辑节奏",
    "audio_tempo": "音频节奏：bgm节奏/情绪基调",
    "style": "视觉风格：整体视觉风格参考",
    "endpoint": "端点：首帧/尾帧锁定参考",
}

# Clip 状态机
CLIP_STATUS_FLOW = {
    "planned": ["ready"],
    "ready": ["generated"],
    "generated": ["reviewed", "repair"],
    "reviewed": ["accepted", "accepted_with_deviation", "rejected"],
    "accepted": ["planned"],          # 接受后可进入下一clip
    "accepted_with_deviation": ["planned"],  # 接受但有偏差
    "repair": ["generated"],
    "rejected": ["planned"],          # 拒绝后重新计划
}

# 连续性关系类型
SEQUENCE_RELATIONS = [
    "standalone",                    # 独立clip，无前后关系
    "sequence_first_clip",           # 序列的第一段
    "seamless_continuation",         # 无缝衔接（动作/空间连续）
    "intentional_next_shot",         # 有意的下一镜头（时间跳跃/场景切换）
    "bridge_between_known_states",   # 桥接两个已知状态之间的过渡
    "repair_tail",                   # 修复上一个clip的末尾
    "reanchor_after_drift",          # 角色/场景漂移后重新锚定
]

# 镜头结构类型
SHOT_STRUCTURES = [
    "compact_single_take",           # 紧凑单次拍摄
    "phased_single_take",            # 阶段性单次拍摄（如日出→正午）
    "dense_multishot",               # 密集多镜头
    "first_last_frame_transition",   # 首尾帧过渡
    "video_edit_contract",           # 视频编辑合同
]


@dataclass
class ClipContract:
    """单个镜头的拍摄合同"""
    project_id: str = ""
    clip_id: str = ""
    parent_clip_id: Optional[str] = None
    sequence_index: int = 1
    narrative_job: str = ""
    target_duration_sec: Optional[float] = None
    generation_mode: str = "t2v"
    shot_structure: str = "compact_single_take"
    already_happened: list = field(default_factory=list)
    this_clip_only: list = field(default_factory=list)
    reserved_for_later: list = field(default_factory=list)
    planned_start_state: dict = field(default_factory=dict)
    planned_end_state: dict = field(default_factory=dict)
    continuity_locks: list = field(default_factory=list)
    allowed_changes: list = field(default_factory=list)
    status: str = "planned"
    observed_end_state: dict = field(default_factory=dict)

    def to_dict(self):
        return make_clip_contract(
            project_id=self.project_id,
            clip_id=self.clip_id,
            parent_clip_id=self.parent_clip_id,
            sequence_index=self.sequence_index,
            narrative_job=self.narrative_job,
            target_duration_sec=self.target_duration_sec,
            generation_mode=self.generation_mode,
            shot_structure=self.shot_structure,
            already_happened=self.already_happened,
            this_clip_only=self.this_clip_only,
            reserved_for_later=self.reserved_for_later,
            planned_start_state=self.planned_start_state,
            planned_end_state=self.planned_end_state,
            continuity_locks=self.continuity_locks,
            allowed_changes=self.allowed_changes,
            status=self.status,
        )

    def accept(self, observed_end_state: dict = None):
        """接受此clip，记录实际结束状态"""
        self.status = "accepted"
        if observed_end_state:
            self.observed_end_state = observed_end_state

    def can_transition_to(self, target_status: str) -> bool:
        """检查状态转换是否合法"""
        return target_status in CLIP_STATUS_FLOW.get(self.status, [])


@dataclass
class SequenceProject:
    """多clip序列项目"""
    project_id: str = ""
    clips: list = field(default_factory=list)
    current_clip_index: int = 0
    state_revision: int = 1

    def add_clip(self, clip: ClipContract):
        """添加一个新clip"""
        clip.project_id = self.project_id
        clip.sequence_index = len(self.clips) + 1
        if self.clips:
            clip.parent_clip_id = self.clips[-1].clip_id
        self.clips.append(clip)

    def current_clip(self) -> Optional[ClipContract]:
        """获取当前正在处理的clip"""
        if 0 <= self.current_clip_index < len(self.clips):
            return self.clips[self.current_clip_index]
        return None

    def advance(self, observed_end_state: dict = None):
        """接受当前clip，前进到下一个"""
        cur = self.current_clip()
        if cur:
            cur.accept(observed_end_state)
            self.state_revision += 1
        self.current_clip_index += 1

    def write_next_prompt(self, next_action: str, **kw) -> dict:
        """基于已接受的clip状态，写下一clip的prompt-spec"""
        cur = self.current_clip()
        if not cur and self.clips:
            # 没有当前clip，用最后一个已接受的clip的状态
            last = self.clips[-1]
            opening_source = "observed_end_state" if last.observed_end_state else "planned_end_state"
        elif cur:
            # 当前clip还没生成，用它的计划状态
            opening_source = "planned_start_state"
        else:
            opening_source = "standalone"

        return make_prompt_spec(
            project_id=self.project_id,
            clip_id=cur.clip_id if cur else "",
            sequence_relation="seamless_continuation" if self.clips else "sequence_first_clip",
            generation_mode=cur.generation_mode if cur else "t2v",
            reference_roles=[],
            opening_state_source=opening_source,
            current_clip_action=next_action,
            endpoint="",
            completed_beat_exclusions=cur.already_happened if cur else [],
            reserved_future_exclusions=cur.reserved_for_later if cur else [],
            natural_language_prompt=next_action,
        )


# ---- P0质检扩展 ----
def check_continuity_locks(prev_ending: dict, next_start: dict, locks: list) -> list:
    """检查连续性锁是否被违反"""
    violations = []
    for lock in locks:
        if lock in prev_ending and lock in next_start:
            if prev_ending[lock] != next_start[lock]:
                violations.append(f"{lock}: {prev_ending[lock]} → {next_start[lock]}")
    return violations


def check_shot_structure_compliance(contract: ClipContract, actual_duration: float) -> list:
    """检查生成结果是否满足合同约束"""
    warnings = []
    if contract.target_duration_sec and actual_duration:
        ratio = actual_duration / contract.target_duration_sec
        if ratio < 0.8:
            warnings.append(f"时长不足: {actual_duration:.1f}s vs 目标{contract.target_duration_sec:.1f}s")
        elif ratio > 1.2:
            warnings.append(f"超时: {actual_duration:.1f}s vs 目标{contract.target_duration_sec:.1f}s")
    return warnings
