"""
角色数据库 — 角色圣经/场景圣经的数据结构
"""
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Character:
    char_id: str; name: str; gender: str = "无"
    age_range: str = "成年"; appearance: str = ""
    personality: str = ""; arc: str = ""
    visual_anchors: list = field(default_factory=list)

@dataclass
class Scene:
    scene_id: str; name: str = ""; description: str = ""
    lighting: str = ""; color_tone: str = ""
    props: list = field(default_factory=list)

@dataclass
class Prop:
    prop_id: str; name: str = ""; description: str = ""
    visual_anchors: list = field(default_factory=list)

class CharacterDB:
    def __init__(self):
        self.characters: dict[str, Character] = {}
        self.scenes: dict[str, Scene] = {}
        self.props: dict[str, Prop] = {}
    def add_character(self, c: Character): self.characters[c.char_id] = c
    def add_scene(self, s: Scene): self.scenes[s.scene_id] = s
    def add_prop(self, p: Prop): self.props[p.prop_id] = p
    def get_character(self, cid: str) -> Optional[Character]: return self.characters.get(cid)
    def get_scene(self, sid: str) -> Optional[Scene]: return self.scenes.get(sid)
