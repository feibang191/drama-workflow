"""drama-workflow adapters — v0.2"""

from .schemas import (
    make_prompt_spec, make_clip_contract, make_project_state,
    is_valid_prompt_spec, validate, SCHEMA_MAP,
)
from .character_database import Character, Scene, CharacterDB
from .camera_mapper import build_camera_prompt
from .template_engine import substitute_vars, clean_prompt, build_char_prompt
from .prompt_optimizer import (
    check_appearance_lock, strip_appearance, check_visual_description,
    convert_abstract_to_physical, optimize_shot_prompt,
    FIRST_FRAME_FORBIDDEN, GENERALLY_FORBIDDEN, ABSTRACT_TO_PHYSICAL,
)
from .shot_connector import (
    CharacterPose, extract_ending_state, build_inertia_chain,
    detect_pose_break, ShotState,
)
from .block_storyboard import Shot, Block, BlockStoryboard
from .grid_template import SixGridTemplate, KeyframesTemplate, IRON_LAWS
from .sequence_protocol import (
    ClipContract, SequenceProject,
    check_continuity_locks, check_shot_structure_compliance,
)
from .reference_role import (
    ReferenceAsset, ReferenceRegistry,
    REFERENCE_ROLES,
    embed_reference_roles, check_identity_persistence,
)
from .base import (
    BaseAdapter, AdapterConfig, AdapterError,
    AuthError, RateLimitError, TimeoutError, ContentBlockedError,
)
from .registry import AdapterRegistry
from .executor import AdapterExecutor
from .视频生成模型 import 视频生成模型Adapter
from .图像生成 API import 图像生成 APIImageAdapter, 图像生成 APIVideoAdapter
from .metadata import build_metadata, embed_to_png, embed_to_mp4

# Phase 1-1: 护栏规则引擎
from .guardrail_rules import (
    check_all_rules, check_rule, GR_RULES,
    GuardRule, COMPLEXITY_LEVELS, SLOT_LIMITS,
)
# Phase 1-2: 质量评估
from .quality_evaluator import (
    run_prompt_qa, evaluate_shot, ShotQualityReport, PromptCheck,
    PROMPT_CHECKS, SHOT_SCORE_DIMS,
)
# Phase 1-3: 经验库
from .experience_db import ExperienceDB, ExperienceSample
# Phase 1-4: 预算控制
from .budget_controller import BudgetController, BudgetState, DEFAULT_BUDGET
# Phase 1-5: Trace
from .trace_logger import PipelineTracer, TraceRecord
# Phase 1-6: 回退
from .fallback_manager import FallbackManager, FallbackJob, DEGRADE_LEVELS
# Phase 1-7: 交付组装
from .delivery_assembler import DeliveryAssembler, VideoSegment, SubtitleEntry
# Phase 1-8: 仪表盘
from .pipeline_dashboard import PipelineDashboard, ProjectStatus


# === 预注册适配器 ===
def register_default_adapters(registry=None):
    """注册默认适配器到注册表"""
    if registry is None:
        from .registry import AdapterRegistry
        registry = AdapterRegistry()
    import yaml, os
    config_path = os.path.join("C:", os.sep, "Users", "Administrator", "AppData", "Local", "hermes", "config.yaml")
    config_path = os.path.abspath(config_path)
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f) or {}
        for p in cfg.get("custom_providers", []):
            base = p.get("base_url", "")
            key = p.get("api_key", "")
            if "apihub.图像生成 API" in base:
                from .base import AdapterConfig
                acfg = AdapterConfig(api_key=key, base_url=base)
                registry.register(图像生成 APIImageAdapter(acfg), "图像生成 API_image")
                registry.register(图像生成 APIVideoAdapter(acfg), "图像生成 API_video")
                registry.set_fallback_chain(["图像生成 API_image", "图像生成 API_video"])
                break
    return registry

# Camera Tree (开源视频生成框架吸收)
from .camera_tree import (
    Camera, CameraParentItem, CameraTree,
    build_camera_tree, camera_tree_to_json,
    load_camera_tree, save_camera_tree,
    make_simple_camera_tree, validate_and_fix_camera_tree,
)

# Reference Image Selector (开源视频生成框架吸收)
from .reference_image_selector import (
    ReferenceAsset, ReferenceSet,
    select_reference_images_for_shot,
    create_reference_set_for_scene,
    format_reference_instruction,
    validate_reference_count,
    MAX_IMAGES, MAX_VIDEOS, MAX_AUDIO, MAX_TOTAL_FILES,
)

# 开源视频生成框架 Phase 4 新增模块
from .best_image_selector import (
    EvaluationScore,
    CandidateImage,
    evaluate_candidate_mlmm,
    select_best_candidate,
    batch_evaluate_candidates,
    create_candidate,
    create_multiple_candidates,
)
from .novel_compressor import (
    CompressedScene,
    CompressionResult,
    compress_novel_to_episodes,
    compress_paragraphs,
)
from .event_extractor import (
    Event,
    EventChain,
    extract_events_from_script,
    classify_event,
    calculate_importance,
)
from .character_portraits_generator import (
    PortraitView,
    CharacterPortrait,
    generate_eight_view_portrait,
    generate_three_in_one_portrait,
    build_prompt,
)
from .scene_extractor import (
    SceneElement,
    Scene,
    extract_scenes_from_script,
    identify_scene_transitions,
)
from .global_information_planner import (
    GlobalConstraint,
    GlobalPlan,
    create_global_plan,
)
from .agent_loop import (
    AgentState,
    AgentStep,
    AgentLoop,
)
