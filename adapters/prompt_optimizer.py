"""P0 规则引擎 — 角色外貌锁 / 对白铁律 / 纯视觉描述 / 严格映射
v2.0 — ABSTRACT_TO_PHYSICAL补全至52组 + FORBIDDEN_WORDS首帧/非首帧分级
"""
import re

# 首帧禁止的外貌词（video frame可以包含，因为需要描述画面内容）
FIRST_FRAME_FORBIDDEN = {
    # 头发
    "头发","白发","银发","黑发","金发","长发","短发","卷发","刘海","马尾","辫子","盘发","发丝","发髻","青丝",
    # 眼睛
    "瞳孔","眼睛","眼神","眼眸","眼瞳","睫毛","眉毛","眼角","眼眶","目光","眼底","眼睑","眼袋",
    # 面部
    "嘴唇","嘴巴","牙齿","酒窝","胡须","胡茬","胡子","脸颊","额头","鼻梁",
    # 皮肤
    "皮肤","肌肤","肤色","皱纹","雀斑","伤疤","疤痕","毛孔","细纹",
    # 服饰
    "衣服","裙子","裤子","外套","披风","铠甲","袍子","长袍","靴子","帽子","手套","腰带","衣领","袖口",
    "旗袍","古装","汉服","婚服","道袍","制服","西装","礼服","斗篷","坎肩","围巾","头饰","发簪","耳环",
    # 身体
    "手指","手掌","手臂","肩膀","腰部","腿部","膝盖","脚","翅膀","尾巴","后背","胸口","颈部",
}

# 通用禁止词（所有frame类型都不允许）
GENERALLY_FORBIDDEN = {
    "watermark","logo","text","signature","水印","字幕",
}

def check_appearance_lock(prompt, frame_type="first_frame"):
    """检查prompt是否含有禁止的外貌词"""
    result = {"passed": True, "forbidden_found": [], "suggestions": []}
    
    # 首帧检查更严格：外貌词、通用词全部检查
    target_words = GENERALLY_FORBIDDEN.copy()
    if frame_type == "first_frame":
        target_words.update(FIRST_FRAME_FORBIDDEN)
    
    for word in target_words:
        if word in prompt:
            result["forbidden_found"].append(word)
            result["passed"] = False
    
    if not result["passed"]:
        if frame_type == "first_frame":
            result["suggestions"] = ["首帧禁止描写外貌，请用参考图承载角色外观"]
        else:
            result["suggestions"] = ["prompt中不应包含水印/字幕等通用词"]
    return result

def strip_appearance(prompt, frame_type="first_frame"):
    """清洗prompt中的禁止词"""
    target_words = GENERALLY_FORBIDDEN.copy()
    if frame_type == "first_frame":
        target_words.update(FIRST_FRAME_FORBIDDEN)
    
    for word in sorted(target_words, key=len, reverse=True):
        prompt = prompt.replace(word, "")
    prompt = re.sub(r'\s{2,}', ' ', prompt)
    return prompt.strip()

def check_dialogue_in_first_frame(prompt, mode="video"):
    """检查首帧是否含台词"""
    found = []
    for p in [r'「(.+?)」', r'[\u201c\u201d](.+?)[\u201c\u201d]', r'["\u201c](.+?)["\u201d]']:
        matches = re.findall(p, prompt)
        found.extend(matches)
    return {"passed": len(found) == 0, "dialogue_found": found}

# === 52组抽象→物理映射 ===
ABSTRACT_TO_PHYSICAL = {
    # 悲伤/难过 (6组)
    "难过": "眼眶泛红，低垂着头，手指无意识地攥着衣角",
    "悲伤": "肩膀下垂，呼吸沉重，目光空洞地望着前方",
    "绝望": "身体滑落在地，双手抱头，全身微微发抖",
    "心碎": "一手扶着胸口，身体微微晃了一下，嘴唇颤抖说不出话",
    "痛苦": "眉头紧蹙，咬紧下唇，额角渗出冷汗",
    "心疼": "伸手想触碰又缩回，眼眶泛酸，别过头去",
    
    # 喜悦/开心 (5组)
    "开心": "嘴角上扬露出笑容，眼睛弯成了月牙",
    "幸福": "嘴角含着笑意，眼眶微微泛光，像是藏着光",
    "放松": "长舒一口气，肩膀缓缓下沉，嘴角浮起浅笑",
    "欣慰": "眼神温柔，唇角微微扬起，轻轻点了点头",
    "满足": "靠向椅背，闭上眼，嘴角带着浅浅的笑意",
    
    # 愤怒/情绪激动 (4组)
    "愤怒": "咬紧牙关，拳头攥得指关节泛白，胸膛剧烈起伏",
    "生气": "脸色沉下来，眉头拧紧，攥着拳头一言不发",
    "不耐烦": "眉头微皱，指尖在桌面上轻轻敲击，叹了口气",
    "冷漠": "面无表情地扫了一眼，语气平淡没有起伏",
    
    # 恐惧/紧张 (5组)
    "恐惧": "瞳孔骤缩，身体后仰，双手护在胸前微微后退了一步",
    "害怕": "双手环抱自身，向角落里缩了缩，呼吸变得急促",
    "紧张": "手指捏着衣角反复揉搓，喉结上下动了动，眼神闪烁",
    "慌乱": "左右张望，动作变得急促而不协调，声音发颤",
    "不安": "频繁回头张望，手指反复摩挲，坐立难安",
    
    # 惊讶/震惊 (3组)
    "惊讶": "瞳孔微张，嘴唇轻启，整个人像是定格了一瞬",
    "震惊": "瞳孔猛地放大，身体僵在原地，过了几秒才说出话来",
    "难以置信": "瞪大眼睛，后退半步，张了张嘴却说不出话",
    
    # 疑惑/困惑 (3组)
    "疑惑": "微微歪头，眉头轻皱，上下打量了几番",
    "困惑": "皱着眉来回踱步，时不时抬头看一眼又迅速低下头",
    "不解": "眉头拧成一个结，偏着头看对方，嘴唇动了动又闭上",
    
    # 思考/回忆 (4组)
    "沉思": "垂着眼，手指无意识地在桌面上轻点，眉头微微锁着",
    "回忆": "目光变得悠远，视线落在虚空中某个点上，嘴角微动",
    "想起": "忽然停下动作，眼神闪了闪，像是记起了什么",
    "忽然": "动作猛地一顿，瞳孔微缩，像是被什么念头击中",
    
    # 决心/犹豫 (5组)
    "下定决心": "缓缓抬起头，目光从飘忽变得坚定，深吸一口气",
    "坚定": "目光笔直地看向前方，下巴微抬，肩膀端平",
    "犹豫": "张了张嘴又闭上，手指抬起又放下，目光游移不定",
    "内心挣扎": "低头沉默，手指绞在一起，眉头紧锁，呼吸时快时慢",
    "犹豫不决": "站住脚步，脚尖朝着外面又转回来，咬了咬下唇",
    
    # 温柔/安抚 (3组)
    "温柔": "目光柔和下来，声音轻缓，动作轻柔得像怕惊动什么",
    "温暖": "眼里带着浅浅的笑意，声音柔和了几分",
    "安慰": "抬手轻轻搭在对方肩上，目光温和，声音放得很轻",
    
    # 震惊/醒悟 (3组)
    "恍然大悟": "蓦地抬眼，瞳孔微张，嘴唇无声地动了动，像是理清了什么",
    "猛然惊觉": "身体猛地绷直，瞳孔骤然收缩，呼吸停了半拍",
    "心里咯噔一下": "动作突然僵住，眼睛微微睁大，喉结上下动了动",
    
    # 孤独/寂寞 (3组)
    "孤独": "独自坐在角落，抱着膝盖，下巴抵在膝上发呆",
    "落寞": "背影微微佝偻，低头慢慢走着，像被世界遗忘",
    "寂寞": "伸手摸了摸冰冷的座位，叹了口气，目光暗了暗",
    
    # 身体感觉 (3组)
    "心中一痛": "眉头紧蹙，抬手按住胸口，呼吸急促了几分",
    "松了一口气": "胸口起伏了一下，肩膀缓缓下沉，双手从紧握变成了松开",
    "心里一紧": "身体微僵，呼吸在那一瞬间停了半拍",
    "心软": "原本绷着的表情松动了一下，视线软下来，轻叹了口气",
    "心酸": "鼻子微微发酸，喉头滚动，视线变得模糊了一瞬",
}

ABSTRACT_COUNT = len(ABSTRACT_TO_PHYSICAL)

def convert_abstract_to_physical(prompt):
    """将抽象情绪词替换为物理动作描述"""
    for abstract, physical in ABSTRACT_TO_PHYSICAL.items():
        prompt = prompt.replace(abstract, physical)
    return prompt

def check_visual_description(prompt):
    """检测prompt中是否含有未替换的抽象情绪词"""
    found = []
    for abstract in ABSTRACT_TO_PHYSICAL:
        if abstract in prompt:
            found.append(abstract)
    return {"passed": len(found) == 0, "abstract_found": found}

def optimize_shot_prompt(shot, known_chars=None, frame_type="first_frame"):
    """一站式预测优化：外貌锁+台词检测+抽象词转换"""
    desc = shot.get("description", "")
    first_prompt = shot.get("first_frame_prompt", desc)
    issues = []
    fixes = {}
    
    # P0-1 外貌锁
    appr = check_appearance_lock(first_prompt, frame_type)
    if not appr["passed"]:
        fixes["first_frame_prompt"] = strip_appearance(first_prompt, frame_type)
        issues.append(f"外貌锁违规({len(appr['forbidden_found'])}词)")
    
    # P0-2 对白铁律（首帧不能有台词）
    df = check_dialogue_in_first_frame(first_prompt)
    if not df["passed"]:
        issues.append("首帧含台词")
    
    # P0-3 纯视觉描述（抽象→物理替换）
    a2p = convert_abstract_to_physical(desc)
    if a2p != desc:
        fixes["description"] = a2p
        issues.append("抽象词已转换")
    
    return {"passed": len(issues)==0, "issues": issues, "fixes": fixes,
            "score": max(0, 100 - len(issues)*10)}
