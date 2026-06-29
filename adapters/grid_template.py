"""
P2-2 宫格模板系统 — 6种模板
"""
from typing import List, Optional

IRON_LAWS = [
    "1. 文案忠实度: 严格对应剧本原文，不得增删情节",
    "2. 对白铁律: videoPrompt必须逐字完整引用原文对白",
    "3. 台词清单核对: 每个分镜开头输出所有检测到的对白",
    "4. 角色外貌锁: firstFrame禁止描写外貌，仅允许姓名+性别+年龄+姿态+情绪",
    "5. 图文分离: 宫格画面中绝对无文字",
    "6. 动作惯性: 后一镜起始姿态=前一镜结束姿态",
    "7. 严格映射: 角色/场景/物品必须来自信息库",
    "8. 纯视觉描述: 禁止抽象情绪词，转化为物理动作",
    "9. 单一空间: 每条videoPrompt指向一个全屏物理空间",
    "10. 禁止虚构: 绝不允许添加文案中未提及的情节",
]

class SixGridTemplate:
    def __init__(self, style="anime"):
        self.style = style

    def render(self, shots, script_text=""):
        lines = []
        lines.append("【系统身份】工业级AI漫剧视效总监")
        lines.append("【画布规格】3行x2列竖屏六宫格")
        lines.append("【总格数】6格")
        lines.append("【画幅比】9:16")
        lines.append(f"【风格】{self.style}，8K高清，HDR")
        lines.append("")
        lines.append("【宫格铁律】")
        for l in IRON_LAWS:
            lines.append("  " + l)
        lines.append("")
        lines.append("【分镜序列】")
        for i, shot in enumerate(shots[:6]):
            sid = shot.get("shot_id", f"S{i+1:02d}")
            desc = shot.get("description", "")[:60]
            lines.append("")
            lines.append(f"【格{i+1} | {sid}】")
            lines.append(f"  firstFramePrompt: {shot.get('first_frame_prompt','')[:60]}")
            lines.append(f"  videoPrompt: {desc}")
        return "\n".join(lines)

class KeyframesTemplate:
    def __init__(self, style="anime"):
        self.style = style

    def render(self, shot, prev_shot=None, next_shot=None, script_text=""):
        lines = []
        lines.append("【系统身份】AI漫剧首尾帧生成器")
        lines.append("【画幅】9:16")
        lines.append(f"【风格】{self.style}，8K高清，HDR")
        lines.append("")
        lines.append("【宫格铁律】")
        for l in IRON_LAWS:
            lines.append("  " + l)
        lines.append("")
        sid = shot.get("shot_id", "?")
        desc = shot.get("description", "")
        lines.append(f"【分镜 {sid}】")
        if prev_shot:
            lines.append(f"【前镜衔接】{prev_shot.get('description','')[:40]}")
        lines.append("【本镜首帧】")
        lines.append(f"  firstFramePrompt: {sid}首帧 | 从上一镜结尾自然过渡")
        lines.append("【本镜视频】")
        lines.append(f"  videoPrompt: {desc}")
        if next_shot:
            lines.append(f"【下镜衔接】{next_shot.get('description','')[:40]}")
        lines.append("【本镜尾帧】")
        lines.append(f"  lastFramePrompt: {sid}尾帧 | 自然过渡")
        return "\n".join(lines)
