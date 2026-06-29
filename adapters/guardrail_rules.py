"""Phase 1-1: 护栏规则引擎 — 从B2 guardrail_rules.json提取并重构
9条GR规则: GR001-GR009，含BLOCK/WARN两级"""
from dataclasses import dataclass, field
from typing import List, Optional

COMPLEXITY_LEVELS = {"L1","L2","L3","L4","L5"}
SLOT_LIMITS = {"L1":1, "L2":2, "L3":4, "L4":5, "L5":5}
SEEDANCE_MODELS = {"doubao-视频生成模型-2-0-260128","视频生成模型"}

@dataclass
class GuardRule:
    id: str; name: str; severity: str  # BLOCK or WARN
    description: str
    check_fn: callable = field(repr=False)


def _gr010(prompt: str) -> tuple:
    """Prompt 超长检查 — 视频生成模型 限制 5000 字符"""
    if len(prompt) > 5000:
        return False, f"GR010违规: prompt超长 {len(prompt)} > 5000"
    return True, ""

def _gr011(image_count: int) -> tuple:
    """图片数量超限 — 视频生成模型 最多 9 张"""
    if image_count > 9:
        return False, f"GR011违规: 图片数量超限 {image_count} > 9"
    return True, ""

def _gr012(video_count: int) -> tuple:
    """视频数量超限 — 视频生成模型 最多 3 个"""
    if video_count > 3:
        return False, f"GR012违规: 视频数量超限 {video_count} > 3"
    return True, ""

def _gr013(audio_count: int) -> tuple:
    """音频数量超限 — 视频生成模型 最多 3 个"""
    if audio_count > 3:
        return False, f"GR013违规: 音频数量超限 {audio_count} > 3"
    return True, ""

def _gr014(total_files: int) -> tuple:
    """总文件数超限 — 视频生成模型 最多 12 个"""
    if total_files > 12:
        return False, f"GR014违规: 总文件数超限 {total_files} > 12"
    return True, ""

GR_RULES = []

def _gr001(level: str, model: str) -> tuple:
    "L4+禁止视频生成模型"
    if level in ("L4","L5") and model in SEEDANCE_MODELS:
        return False, f"GR001违规: {level}复杂度禁止{model}"
    return True, ""

def _gr002(ref_count: int, level: str) -> tuple:
    "Reference超槽位"
    limit = SLOT_LIMITS.get(level, 5)
    if ref_count > limit:
        return False, f"GR002违规: {level}最多{limit}张Reference，当前{ref_count}张"
    return True, ""

def _gr003(prompt: str, mode: str = "FLF2V") -> tuple:
    "未编译阻断 — 检查prompt是否包含@图片标签"
    if mode == "FLF2V" and "@图片" not in prompt:
        return False, "GR003违规: FLF2V模式prompt缺少@图片标签绑定"
    return True, ""

def _gr004(prompt_desc: str, dna_block: str) -> tuple:
    "角色描述非DNA原文 — prompt中的角色描述必须源自dna_block"
    if dna_block and prompt_desc:
        key_chars = dna_block.strip()[:50]
        if key_chars not in prompt_desc:
            return False, "GR004违规: 角色描述与DNA block不匹配"
    return True, ""

def _gr005(active_variation) -> tuple:
    "衣橱未锁定"
    if active_variation is None:
        return False, "GR005违规: 衣橱active_variation为null，未锁定"
    return True, ""

def _gr006(scene_desc: str) -> tuple:
    "背景未锚定 — 缺空间锚定或前景/中景/背景声明"
    if scene_desc and not any(kw in scene_desc for kw in ["前景","中景","背景","[空间锚定]"]):
        return False, "GR006警告: 场景描述缺空间锚定声明"
    return True, ""

def _gr007(char_count: int, props: list) -> tuple:
    "多角色道具穿模"
    if char_count >= 2 and len(props) >= 3:
        return False, "GR007违规: 多角色+多道具可能穿模，建议拆分镜头"
    return True, ""

def _gr008(prompt: str, mode: str = "FLF2V") -> tuple:
    "FLF2V模式注入外观描述 — L1层不能含外貌词"
    if mode == "FLF2V":
        appearance_words = {"红色","白色","黑色","蓝色","金色","银发","长发","短发"}
        found = [w for w in appearance_words if w in prompt]
        if found:
            return False, f"GR008违规: FLF2V模式L1含外貌词{found}"
    return True, ""

def _gr009(ref_type: str) -> tuple:
    "使用角色三视图Reference — 官方警告多视图→双胞胎"
    if "三视图" in ref_type or "multi" in ref_type.lower():
        return False, "GR009违规: 禁止使用角色三视图Reference"
    return True, ""


def _gr010(prompt: str) -> tuple:
    """Prompt 超长检查 — 视频生成模型 限制 5000 字符"""
    if len(prompt) > 5000:
        return False, f"GR010违规: prompt超长 {len(prompt)} > 5000"
    return True, ""

def _gr011(image_count: int) -> tuple:
    """图片数量超限 — 视频生成模型 最多 9 张"""
    if image_count > 9:
        return False, f"GR011违规: 图片数量超限 {image_count} > 9"
    return True, ""

def _gr012(video_count: int) -> tuple:
    """视频数量超限 — 视频生成模型 最多 3 个"""
    if video_count > 3:
        return False, f"GR012违规: 视频数量超限 {video_count} > 3"
    return True, ""

def _gr013(audio_count: int) -> tuple:
    """音频数量超限 — 视频生成模型 最多 3 个"""
    if audio_count > 3:
        return False, f"GR013违规: 音频数量超限 {audio_count} > 3"
    return True, ""

def _gr014(total_files: int) -> tuple:
    """总文件数超限 — 视频生成模型 最多 12 个"""
    if total_files > 12:
        return False, f"GR014违规: 总文件数超限 {total_files} > 12"
    return True, ""

GR_RULES = [
    GuardRule("GR001","L4+禁止视频生成模型","BLOCK","L4及以上禁止使用视频生成模型 2.0",_gr001),
    GuardRule("GR002","Reference超槽位","BLOCK","参考图不超过复杂度槽位上限",_gr002),
    GuardRule("GR003","未编译阻断","BLOCK","FLF2V模式prompt必须含@图片标签",_gr003),
    GuardRule("GR004","角色描述非DNA原文","BLOCK","prompt角色描述必须匹配DNA block",_gr004),
    GuardRule("GR005","衣橱未锁定","BLOCK","active_variation不能为null",_gr005),
    GuardRule("GR006","背景未锚定","WARN","场景缺空间锚定声明",_gr006),
    GuardRule("GR007","多角色道具穿模","BLOCK","多角色+多道具需拆分",_gr007),
    GuardRule("GR008","FLF2V注入外观描述","BLOCK","L1层不能含外貌词",_gr008),
    GuardRule("GR009","三视图Reference","BLOCK","禁止使用三视图",_gr009),
    GuardRule("GR010","Prompt超长检查","BLOCK","视频生成模型限制5000字符",_gr010),
    GuardRule("GR011","图片数量超限","BLOCK","视频生成模型最多9张图片",_gr011),
    GuardRule("GR012","视频数量超限","BLOCK","视频生成模型最多3个视频",_gr012),
    GuardRule("GR013","音频数量超限","BLOCK","视频生成模型最多3个音频",_gr013),
    GuardRule("GR014","总文件数超限","BLOCK","视频生成模型最多12个文件",_gr014),
]

def check_all_rules(**kwargs) -> list:
    """运行全部匹配的GR规则，返回[(rule_id, severity, passed, message)]"""
    results = []
    for rule in GR_RULES:
        try:
            fn = rule.check_fn
            # 从kwargs中提取函数需要的参数
            import inspect
            sig = inspect.signature(fn)
            params = {k: kwargs.get(k) for k in sig.parameters if k in kwargs}
            if len(params) == len(sig.parameters):
                passed, msg = fn(**params)
                results.append((rule.id, rule.severity, passed, msg))
        except Exception as e:
            results.append((rule.id, "ERROR", False, str(e)))
    return results

def check_rule(rule_id: str, **kwargs) -> tuple:
    """运行单条GR规则"""
    for rule in GR_RULES:
        if rule.id == rule_id:
            try:
                passed, msg = rule.check_fn(**kwargs)
                return (rule.id, rule.severity, passed, msg)
            except Exception as e:
                return (rule.id, "ERROR", False, str(e))
    return (rule_id, "UNKNOWN", False, "规则不存在")
