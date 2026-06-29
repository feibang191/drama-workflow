"""prompt_compiler — 7层Prompt编译引擎
Phase 2: 吸收B2 焚诀1-9注入规则 + camera_language完整映射表
焚诀4: 镜头运动量化注入 | 焚诀5: 引用权限声明 | 焚诀6: 多镜头一致性锚点 | 焚诀9: 运镜叙事校验
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from adapters.prompt_optimizer import (
    check_appearance_lock, strip_appearance, convert_abstract_to_physical,
    check_dialogue_in_first_frame, check_visual_description, optimize_shot_prompt,
)
from adapters.shot_connector import CharacterPose, extract_ending_state, build_inertia_chain
from adapters.template_engine import substitute_vars, clean_prompt, build_char_prompt
from adapters.camera_mapper import (
    resolve_camera, resolve_emotion, build_camera_prompt,
    SHOT_SIZES, CAMERA_ANGLES, CAMERA_MOVEMENTS, EMOTION_LIGHTING,
    TIMELINE_BEATS,
)
from adapters.schemas import make_prompt_spec, make_clip_contract
from adapters.reference_role import ReferenceRegistry, ReferenceAsset
from adapters.sequence_protocol import ClipContract, check_continuity_locks

# ── 焚诀4: 镜头运动量化 ──
CAMERA_QUANTIZATION = {
    "dolly_in":  "人物面部在4秒内从占画面约15%%扩大至约40%%。节奏：前2秒缓慢加速，中段稳定，最后2秒减速到位。",
    "dolly_out": "镜头在4秒内从近景稳定拉远至全景。节奏：匀速运动，无加速。",
    "arc":       "以人物为中心，从正前方0度环至右后方约120度，耗时7秒。节奏：前90度缓慢观察，后30度仅2秒突然加快。",
    "tracking":  "镜头与人物同步横向移动，速度匹配人物步速。画面中人物保持居中，背景匀速滑动。",
    "static":    "镜头固定，角色在画面中运动产生变化。节奏：仅依赖角色动作节奏。",
    "zoom_push": "在1.5秒内从近景急推至特写。节奏：先静止3秒建立预期，最后1.5秒急速推进。",
    "truck":     "在5秒内从左向右横移3米。节奏：匀速移动，起止无加速。",
    "tilt":      "在4秒内从地面扫至天空。节奏：前3秒慢速向上，最后1秒加速到位。",
}

# ── 焚诀5: 引用权限模式 ──
REFERENCE_PERMISSIONS = {
    "full_lock": "锁定面部+发型+服装。参考强度70。背景、光线由文字描述决定。",
    "face_only": "仅锁定面部特征。参考强度30。服装、场景由文字描述决定。",
    "scene_only": "仅锁定场景/背景。参考强度50。角色、光线由文字描述决定。",
    "pose_only": "仅锁定姿态/构图。参考强度40。角色、场景由文字描述决定。",
}

# ── 焚诀6: 多镜头一致性 ──
TRANSITION_TYPES = ["硬切", "前景擦镜", "甩镜", "动作接续"]


class PromptCompiler:
    def __init__(self, style="东方仙侠", quality="8K高清，HDR",
                 ref_mode="full_lock", transition_type="硬切", lock_anchors=True):
        self.style = style
        self.quality = quality
        self.ref_mode = ref_mode
        self.transition_type = transition_type
        self.lock_anchors = lock_anchors
        self._layers = {i: "" for i in range(1, 8)}
        self._injections = {}

    def set_layer(self, num, content):
        if 1 <= num <= 7:
            self._layers[num] = content.strip()

    def _get_val(self, obj, attr, default=""):
        if hasattr(obj, attr):
            return getattr(obj, attr, default)
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return default

    def compile(self, shot_id="", use_schema=True):
        result = {}
        for i in range(1, 8):
            val = self._layers[i]
            if val:
                result[f"L{i}"] = val

        # 焚诀5: 引用权限声明注入（L1层追加）
        if self.ref_mode in REFERENCE_PERMISSIONS:
            ref_note = REFERENCE_PERMISSIONS[self.ref_mode]
            if "L1" in result:
                result["L1"] += f" [{ref_note}]"

        # 焚诀4: 镜头运动量化注入（L5层追加）
        movement = self._guess_movement_from_layers()
        if movement in CAMERA_QUANTIZATION:
            quant = CAMERA_QUANTIZATION[movement]
            if "L5" in result:
                result["L5"] += f" [量化：{quant}]"

        # 焚诀6: 一致性锚点（L7层追加）
        if self.lock_anchors:
            if "L7" in result:
                result["L7"] += f" [转场:{self.transition_type}][一致性：头发分线+衣领+眼距比例所有镜头保持锁定]"

        full_parts = [v for v in result.values() if v]
        full_prompt = "\n".join(full_parts)
        result["full_prompt_zh"] = full_prompt
        negatives = ["low quality", "blurry", "distorted", "extra limbs",
                     "bad anatomy", "watermark", "text", "signature"]
        result["negative_prompt"] = ", ".join(negatives)
        if shot_id and use_schema:
            result["_schema"] = make_prompt_spec(
                project_id="drama", clip_id=shot_id,
                natural_language_prompt=full_prompt)
        return result

    def _guess_movement_from_layers(self):
        """从L5层中猜测运镜类型"""
        l5 = self._layers.get(5, "")
        for m in ["dolly_in", "dolly_out", "arc", "tracking", "zoom_push", "truck", "tilt", "static"]:
            if m in l5 or CAMERA_MOVEMENTS.get(m, {}).get("name","") in l5:
                return m
        return ""

    def compile_shot(self, shot, char_db=None, scene_db=None, prev_pose=None):
        desc = self._get_val(shot, "description")
        sid = self._get_val(shot, "shot_id")
        posture = self._get_val(shot, "posture", "站立")
        emotion = self._get_val(shot, "emotion", "平静")
        beat = self._get_val(shot, "beat", "")
        shot_size = self._get_val(shot, "shot_size", "")
        angle = self._get_val(shot, "angle", "")
        movement = self._get_val(shot, "movement", "")

        char_name = ""
        char_desc = ""
        scene_name = ""
        scene_desc = ""
        lighting = ""
        color_tone = ""

        if char_db and char_db.characters:
            first_char = list(char_db.characters.values())[0]
            char_name = first_char.name
            char_desc = first_char.appearance
        if scene_db and scene_db.scenes:
            first_scene = list(scene_db.scenes.values())[0]
            scene_name = first_scene.name
            scene_desc = first_scene.description
            lighting = first_scene.lighting

        clean_desc = convert_abstract_to_physical(desc)
        action_desc = clean_desc
        if prev_pose:
            inertia = build_inertia_chain(prev_pose, clean_desc)
            if inertia:
                action_desc = inertia + " " + clean_desc

        # 使用camera_mapper的智能推理
        cam_result = resolve_camera(
            beat_type=beat or None,
            shot_size_hint=shot_size or None,
            angle_hint=angle or None,
            movement_hint=movement or None,
        )
        camera = build_camera_prompt(
            cam_result["shot_size"], cam_result["angle"], cam_result["movement"])
        
        # 焚诀4: 量化描述直接注入
        quant_desc = CAMERA_QUANTIZATION.get(cam_result["movement"], "")

        # 焚诀7: 声音设计（简化版）— 情绪→音调映射
        emotion_data = resolve_emotion(emotion)
        
        # 焚诀9: 运镜叙事校验（作为comment输出）
        narrative_check = ""
        movement_narrative = {
            "dolly_in": "确认：我应该注意什么？",
            "dolly_out": "重新理解：这个处境意味着什么？",
            "arc": "检验：每个角度看都一样吗？",
            "static": "观察：由角色动作驱动叙事",
        }
        if cam_result["movement"] in movement_narrative:
            narrative_check = f"[叙事校验：{movement_narrative[cam_result['movement']]}]"

        # 构建7层
        l1 = f"【主体定义】{char_name}，{char_desc}，{posture}，{emotion}，{emotion_data['lighting']}" if char_name else ""
        l2 = f"【场景环境】{scene_name}，{scene_desc}，{emotion_data['lighting']}，{emotion_data['color_direction']}" if scene_name else ""
        l3 = f"【分镜描述】{clean_desc}"
        l4 = f"【动作姿态】{action_desc}"
        l5 = f"【技术参数】{camera}"
        if quant_desc:
            l5 += f" [量化：{quant_desc}]"
        l6 = f"【风格质感】{self.style}，{self.quality}，情绪强度{emotion_data['intensity']}/10"
        l7 = "【全局约束】画面纯净、光影真实、质感细腻、色彩和谐、角色一致"
        if self.lock_anchors:
            l7 += f" [转场:{self.transition_type}][一致性：头发分线+衣领+眼距比例所有镜头保持锁定]"
        if narrative_check:
            l7 += f" {narrative_check}"

        self.set_layer(1, l1)
        self.set_layer(2, l2)
        self.set_layer(3, l3)
        self.set_layer(4, l4)
        self.set_layer(5, l5)
        self.set_layer(6, l6)
        self.set_layer(7, l7)

        return self.compile(sid)


def batch_compile(shots, char_db=None, scene_db=None):
    compiler = PromptCompiler()
    results = []
    prev_pose = None
    for s in shots:
        r = compiler.compile_shot(s, char_db, scene_db, prev_pose)
        results.append(r)
        desc = r.get("L3", "").replace("【分镜描述】", "")
        if desc:
            prev_pose = extract_ending_state(desc)
    return results


# ── 转换层 ──
def compile_to_guitu_format(compiler_result, char_name="角色", ref_images=None):
    full = compiler_result.get("full_prompt_zh", "")
    l1 = compiler_result.get("L1", "")
    guitu = {
        "L1_主体定义": l1.replace("【主体定义】", "").strip(),
        "image_list": ref_images or ["@图片1"],
        "reference_cluster": {
            "role": "identity",
            "path": f"assets/{char_name}/identity.png" if char_name else "assets/identity.png",
        },
        "start_frame_image": ref_images[0] if ref_images and len(ref_images) > 0 else "@图片1",
        "target_model": "doubao-视频生成模型-2-0-260128",
        "_original": compiler_result,
        "full_prompt_zh": full,
        "negative_prompt": compiler_result.get("negative_prompt", ""),
    }
    return guitu


def batch_to_guitu(results, char_names=None, ref_images_map=None):
    if ref_images_map is None:
        ref_images_map = {}
    guitu_results = []
    for i, r in enumerate(results):
        char_name = "角色"
        if char_names and i < len(char_names):
            char_name = char_names[i]
        refs = ref_images_map.get(str(i), None)
        guitu_results.append(compile_to_guitu_format(r, char_name, refs))
    return guitu_results
