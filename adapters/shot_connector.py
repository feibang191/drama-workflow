"""
P1 动作惯性引擎 — 跨镜头姿态追踪 + 衔接约束 + 断裂检测
"""
import re
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class CharacterPose:
    body_pose: str = "standing"
    position: str = ""
    head_direction: str = "forward"
    arm_state: str = "relaxed"
    leg_state: str = "straight"
    emotion: str = "neutral"
    facing: str = ""
    holding: str = ""

    def diff(self, other):
        changes = []
        for fn in ["body_pose","position","head_direction","arm_state","leg_state","emotion","facing","holding"]:
            old = getattr(self, fn)
            new = getattr(other, fn)
            if old and new and old != new:
                changes.append(f"{fn}: {old} -> {new}")
        return changes

_pose_kw = {"坐":"sitting","站":"standing","躺":"lying","跪":"kneeling","蹲":"crouching","跑":"running","走":"walking","飞":"flying"}
_emo_kw = {"笑":"happy","哭":"sad","怒":"angry","惊":"surprised","恐":"fearful","悲":"sad","哀":"sad"}

def extract_ending_state(description: str) -> CharacterPose:
    pose = CharacterPose()
    for kw, val in _pose_kw.items():
        if kw in description:
            pose.body_pose = val; break
    for kw, val in _emo_kw.items():
        if kw in description:
            pose.emotion = val; break
    for m in re.finditer(r"(?:握[着住]?|拿[着住]?|持|手中)(.{1,6})", description):
        obj = m.group(1).strip().rstrip(".,!?")
        if len(obj) <= 6:
            pose.holding = obj; break
    if "低" in description or "俯" in description: pose.head_direction = "down"
    elif "抬" in description or "仰" in description: pose.head_direction = "up"
    elif "回" in description or "转" in description: pose.head_direction = "turned"
    return pose

def build_inertia_chain(prev_end: CharacterPose, current_desc: str = "") -> str:
    clauses = []
    if prev_end.body_pose and prev_end.body_pose != "standing":
        clauses.append(f"延续{prev_end.body_pose}姿态")
    if prev_end.holding:
        clauses.append(f"手中{prev_end.holding}")
    if prev_end.emotion and prev_end.emotion != "neutral":
        clauses.append(f"延续{prev_end.emotion}情绪")
    return "，".join(clauses) + "。" if clauses else ""

def detect_pose_break(prev_desc: str, current_desc: str) -> List[str]:
    prev_end = extract_ending_state(prev_desc)
    cur_start = extract_ending_state(current_desc)
    changes = prev_end.diff(cur_start)
    severe = []
    for c in changes:
        if c.startswith("body_pose"):
            old = c.split("->")[0].split(": ")[1].strip()
            new = c.split("->")[1].strip()
            if old in ["sitting","lying","kneeling"] and new in ["running","jumping"]:
                severe.append(f"严重断裂: {c}")
            else:
                severe.append(f"姿态变化: {c}")
        elif "holding" in c:
            severe.append(f"物品变化: {c}")
    return severe

class ShotState:
    def __init__(self):
        self._states = {}
    def record_ending(self, shot_id, description):
        self._states[shot_id] = extract_ending_state(description)
    def get_ending(self, shot_id):
        return self._states.get(shot_id)
    def check_transition(self, prev_shot_id, current_desc):
        prev = self._states.get(prev_shot_id)
        if not prev: return []
        return detect_pose_break("", current_desc)
