"""camera_mapper — 镜头语言模块
Phase 2: 从B2 camera_language.py完整吸收
8种景别 + 7种角度 + 12种运镜 + 13种叙事节拍→镜头映射 + 23种情绪→灯光/色彩/强度 + 时间轴模板
"""

# ── 景别定义 ──
SHOT_SIZES = {
    "extreme_long": {"name": "大远景", "desc": "人物如蚂蚁，广阔环境叙事", "use": "开场定场", "subject_pct": "<5%"},
    "long":         {"name": "远景",   "desc": "人物小，环境占50%+",     "use": "环境展示", "subject_pct": "10-15%"},
    "full":         {"name": "全景",   "desc": "全身可见",               "use": "角色介绍", "subject_pct": "30-40%"},
    "medium":       {"name": "中景",   "desc": "腰部以上",               "use": "对话叙事", "subject_pct": "40-60%"},
    "medium_close": {"name": "中近景", "desc": "胸部以上",               "use": "情感交流", "subject_pct": "50-70%"},
    "close":        {"name": "近景",   "desc": "脖子以上",               "use": "强调情绪", "subject_pct": "60-80%"},
    "close_up":     {"name": "特写",   "desc": "只有脸",                 "use": "内心戏",   "subject_pct": "80%+"},
    "extreme_close":{"name": "大特写", "desc": "局部细节",               "use": "紧张感",   "subject_pct": "90%+"},
}

# ── 机位角度 ──
CAMERA_ANGLES = {
    "eye":           {"name": "平视",     "use": "共情/中性"},
    "high":          {"name": "高位俯拍", "use": "压迫/渺小"},
    "low":           {"name": "低位仰拍", "use": "英雄/威严"},
    "dutch":         {"name": "斜拍",     "use": "悬疑/不安"},
    "over_shoulder": {"name": "越肩",     "use": "对话/窥视"},
    "bird":          {"name": "鸟瞰",     "use": "地理/全局"},
    "pov":           {"name": "第一视角", "use": "沉浸/主观"},
}

# ── 运镜方式 ──
CAMERA_MOVEMENTS = {
    "static":     {"name": "固定",   "desc": "摄像机静止，角色运动产生变化"},
    "dolly_in":   {"name": "前推",   "desc": "稳定推进，渐进聚焦"},
    "dolly_out":  {"name": "后拉",   "desc": "稳定拉远，展示全景"},
    "arc":        {"name": "环绕",   "desc": "围绕主体旋转，增强动感"},
    "truck":      {"name": "横移",   "desc": "水平移动，展示横向空间"},
    "tilt":       {"name": "俯仰",   "desc": "垂直旋转，扫描纵向空间"},
    "pan":        {"name": "横摇",   "desc": "绕轴心旋转，扫描环境"},
    "tracking":   {"name": "跟拍",   "desc": "随主体移动，主体居中"},
    "steadicam":  {"name": "斯坦尼康", "desc": "手持跟拍，轻微晃动，临场感"},
    "zoom_push":  {"name": "急推",   "desc": "快速推进，情绪压缩感"},
    "crane_up":   {"name": "升镜",   "desc": "垂直升起，展示规模"},
    "crane_down": {"name": "降镜",   "desc": "垂直下降，聚焦主体"},
}

# ── 叙事节拍→镜头参数映射 ──
BEAT_CAMERA_MAP = {
    "establishing_wide":   {"shot_size": "extreme_long", "angle": "high",  "movement": "static",   "note": "超广角+俯压开场"},
    "threat_detail":       {"shot_size": "medium_close", "angle": "high",  "movement": "dolly_in", "note": "推近聚焦威胁细节"},
    "threat_escalation":   {"shot_size": "medium",       "angle": "eye",   "movement": "dolly_out","note": "微拉远展示威胁全景"},
    "golden_break":        {"shot_size": "medium",       "angle": "eye",   "movement": "static",   "note": "光影驱动叙事转折"},
    "hero_reveal":         {"shot_size": "medium",       "angle": "low",   "movement": "dolly_in", "note": "低位仰拍迎接亮相"},
    "confrontation":       {"shot_size": "medium",       "angle": "eye",   "movement": "static",   "note": "中景留冲突空间"},
    "action":              {"shot_size": "full",         "angle": "eye",   "movement": "arc",      "note": "全景环绕增强动感"},
    "victory_tableau":     {"shot_size": "full",         "angle": "low",   "movement": "dolly_out","note": "仰拍+微拉远展示胜利"},
    "afterglow":           {"shot_size": "long",         "angle": "high",  "movement": "static",   "note": "远景俯视情绪沉降"},
    "hook":                {"shot_size": "close_up",     "angle": "eye",   "movement": "dolly_in", "note": "特写抓注意力"},
    "suspense":            {"shot_size": "close",        "angle": "dutch", "movement": "static",   "note": "斜拍制造不安"},
    "reveal":              {"shot_size": "medium",       "angle": "low",   "movement": "dolly_in", "note": "仰拍揭示真相"},
    "default":             {"shot_size": "medium",       "angle": "eye",   "movement": "static",   "note": "默认中景平视固定"},
}

# ── 情绪→灯光映射 ──
EMOTION_LIGHTING = {
    "神秘": "阴冷幽暗，边缘勾勒光源，唯一亮源", "惊叹": "明亮柔和，金色温暖主光，自然光均匀",
    "敬畏": "金色强烈光源，氛围庄严，背光勾勒轮廓", "紧张": "低照度，补光不均匀，侧脸阴影压缩",
    "惊喜": "暖色高调，明亮干净，正面柔光", "震撼": "强烈戏剧光，暗部压缩，金色边缘光",
    "喜悦": "高调柔光，暖黄主调，正面均匀照明", "好奇": "自然光加柔，主光偏侧，略带阴影",
    "决意": "冷暖对比，蓝色边缘光勾勒轮廓", "希望": "明亮高调，暖色为主，柔光主光",
    "悲伤": "低饱和蓝灰，冷调低沉，侧光减少", "狂喜": "饱和霓虹，色彩丰富，变化光源",
    "平静": "中性色调，自然光均匀，无硬阴影", "圆满": "金色温暖高调，柔光，逆光金色边缘",
    "愤怒": "低照度红调，硬侧光，高对比阴影", "隐忍": "低调冷光，面部半明半暗",
    "霸气": "强背光勾勒轮廓，暗部压至近黑", "温柔": "暖色柔光，正面散射，低对比",
    "恐惧": "冷蓝底光，面部上方光源制造阴影", "庄严": "金色高位主光，正面均匀，氛围肃穆",
    "激动": "高饱和暖色，动态光源", "冷漠": "冷白平光，无情感色彩",
    "戏谑": "不均匀暖光，局部高光",
}

# ── 情绪→强度量化 ──
EMOTION_INTENSITY = {
    "神秘": 7, "惊叹": 6, "敬畏": 8, "紧张": 7, "惊喜": 7, "震撼": 9,
    "喜悦": 6, "好奇": 5, "决意": 6, "希望": 5, "悲伤": 6, "狂喜": 8,
    "平静": 3, "圆满": 7, "愤怒": 8, "隐忍": 7, "霸气": 9, "温柔": 4,
    "恐惧": 7, "庄严": 7, "激动": 7, "冷漠": 3, "戏谑": 5,
}

# ── 情绪→色彩方向 ──
EMOTION_COLOR = {
    "神秘": "低饱和蓝黑，偶现金光", "惊叹": "高饱和暖黄，明亮干净",
    "敬畏": "金色主调，暗部蓝紫补冷", "紧张": "低饱和蓝灰为主",
    "惊喜": "饱和暖色，明亮高调", "震撼": "强对比金色，暗部几乎全黑",
    "喜悦": "暖黄橙高调", "好奇": "自然色，偏低饱和",
    "决意": "冷暖分界，蓝色侧光", "希望": "明亮暖黄主调",
    "悲伤": "蓝灰低饱和", "狂喜": "饱和霓虹，色彩丰富",
    "平静": "中性灰白自然光", "圆满": "金色温暖高调",
    "愤怒": "暗红+黑，高对比", "隐忍": "冷灰蓝，低饱和",
    "霸气": "金+黑，强对比", "温柔": "暖粉+柔白",
    "恐惧": "冷蓝绿，暗调", "庄严": "金+深蓝，肃穆",
    "激动": "暖红+橙，高饱和", "冷漠": "灰白，去饱和",
    "戏谑": "不规则暖冷交替",
}

# ── 时间轴模板 ──
TIMELINE_BEATS = {
    "establishing_wide": {"time_flow": "slow_hold",        "beat_budget": 3, "modal_priority": ["scene", "motion", "sound"]},
    "threat_detail":     {"time_flow": "slow_increase",    "beat_budget": 3, "modal_priority": ["motion", "scene", "sound"]},
    "threat_escalation": {"time_flow": "rising",           "beat_budget": 4, "modal_priority": ["scene", "motion", "sound"]},
    "golden_break":      {"time_flow": "pause_then_burst", "beat_budget": 3, "modal_priority": ["light", "scene", "motion"]},
    "hero_reveal":       {"time_flow": "release",          "beat_budget": 4, "modal_priority": ["motion", "light", "scene"]},
    "confrontation":     {"time_flow": "balanced_tension", "beat_budget": 4, "modal_priority": ["relationship", "motion", "scene"]},
    "action":            {"time_flow": "accelerate",       "beat_budget": 4, "modal_priority": ["motion", "physics", "scene"]},
    "victory_tableau":   {"time_flow": "decay_to_hold",    "beat_budget": 3, "modal_priority": ["pose", "light", "scene"]},
    "afterglow":         {"time_flow": "slow_decay",       "beat_budget": 2, "modal_priority": ["emotion", "scene", "sound"]},
    "hook":              {"time_flow": "burst",            "beat_budget": 2, "modal_priority": ["motion", "scene", "emotion"]},
    "suspense":          {"time_flow": "slow_tension",     "beat_budget": 3, "modal_priority": ["scene", "emotion", "sound"]},
    "reveal":            {"time_flow": "slow_to_burst",    "beat_budget": 3, "modal_priority": ["light", "motion", "emotion"]},
    "default":           {"time_flow": "neutral",          "beat_budget": 3, "modal_priority": ["scene", "motion", "sound"]},
}


# ── 工具函数 ──

def resolve_camera(beat_type=None, shot_size_hint=None, angle_hint=None, movement_hint=None):
    """根据叙事节拍自动推理镜头参数。优先使用显式hint，其次用beat映射。"""
    result = {"shot_size": "medium", "angle": "eye", "movement": "static", "note": ""}
    if beat_type and beat_type in BEAT_CAMERA_MAP:
        result.update(BEAT_CAMERA_MAP[beat_type])
    if shot_size_hint and shot_size_hint in SHOT_SIZES:
        result["shot_size"] = shot_size_hint
    if angle_hint and angle_hint in CAMERA_ANGLES:
        result["angle"] = angle_hint
    if movement_hint and movement_hint in CAMERA_MOVEMENTS:
        result["movement"] = movement_hint
    size_info = SHOT_SIZES.get(result["shot_size"], {})
    angle_info = CAMERA_ANGLES.get(result["angle"], {})
    move_info = CAMERA_MOVEMENTS.get(result["movement"], {})
    result["shot_size_name"] = size_info.get("name", result["shot_size"])
    result["angle_name"] = angle_info.get("name", result["angle"])
    result["movement_name"] = move_info.get("name", result["movement"])
    result["movement_desc"] = move_info.get("desc", "")
    result["composition_hint"] = size_info.get("desc", "")
    return result


def resolve_emotion(emotion, lighting_hint=None, color_hint=None):
    """根据情绪标签解析灯光、色彩、强度。"""
    return {
        "emotion": emotion,
        "intensity": EMOTION_INTENSITY.get(emotion, 5),
        "lighting": lighting_hint or EMOTION_LIGHTING.get(emotion, "自然光"),
        "color_direction": color_hint or EMOTION_COLOR.get(emotion, "自然色调"),
    }


def resolve_timeline(beat_type):
    """获取某beat类型的时间轴参数。"""
    return TIMELINE_BEATS.get(beat_type, TIMELINE_BEATS["default"])


def build_camera_prompt(shot_size="medium", angle="eye", movement="static"):
    """生成相机描述字符串（向后兼容旧camera_mapper接口）"""
    size_info = SHOT_SIZES.get(shot_size, {})
    angle_info = CAMERA_ANGLES.get(angle, {})
    move_info = CAMERA_MOVEMENTS.get(movement, {})
    parts = [
        f"景别：{size_info.get('name', shot_size)}",
        f"角度：{angle_info.get('name', angle)}",
        f"运镜：{move_info.get('name', movement)}",
        move_info.get("desc", ""),
    ]
    return "，".join(p for p in parts if p)


def get_all_emotions():
    return list(EMOTION_LIGHTING.keys())

def get_all_beats():
    return list(BEAT_CAMERA_MAP.keys())
