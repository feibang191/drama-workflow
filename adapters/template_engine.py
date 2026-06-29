"""
模板引擎 — 变量替换 + 角色/场景/道具prompt构建
"""
import re

def substitute_vars(template: str, vars_dict: dict) -> str:
    result = template
    for key, val in vars_dict.items():
        result = result.replace("{" + key + "}", str(val))
    result = re.sub(r',\s*,', ',', result)
    result = re.sub(r'\s{2,}', ' ', result)
    return result.strip()

def clean_prompt(text: str) -> str:
    text = re.sub(r',\s*,', ',', text)
    text = re.sub(r'\s{2,}', ' ', text)
    text = re.sub(r'[，]+', '，', text)
    return text.strip()

def build_char_prompt(char: "Character", age: bool = True, gender: bool = True) -> str:
    parts = []
    if char.name: parts.append(char.name)
    if gender: parts.append(char.gender)
    if age: parts.append(char.age_range)
    if char.appearance: parts.append(char.appearance)
    return ", ".join(parts)

def build_scene_prompt(scene: "Scene") -> str:
    parts = []
    if scene.name: parts.append(scene.name)
    if scene.description: parts.append(scene.description)
    if scene.lighting: parts.append(scene.lighting)
    if scene.color_tone: parts.append(scene.color_tone)
    return ", ".join(parts)
