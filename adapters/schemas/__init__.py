"""
drama-workflow 结构化数据契约

从 视频生成模型 2.0 Skill OS 吸收的 5 个 JSON Schema：
  - prompt-spec    : prompt的元数据封装
  - clip-contract  : 单镜头合同（起始/结束状态+连续性锁）
  - project-state  : 多clip项目状态模型
  - gen-run        : 单次生成任务记录
  - take-review    : 生成结果审查

每个 schema 提供 validate() 和 default() 两个函数
"""

import json, os

_SCHEMAS = {}
_DIR = os.path.dirname(os.path.abspath(__file__))

def _load(name):
    if name not in _SCHEMAS:
        p = os.path.join(_DIR, name)
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                _SCHEMAS[name] = json.load(f)
        else:
            raise FileNotFoundError(f"Schema not found: {p}")
    return _SCHEMAS[name]

try:
    import jsonschema
    HAS_VALIDATOR = True
except ImportError:
    HAS_VALIDATOR = False

def validate(name, data):
    """Validate data against a named schema. Returns (ok, errors)"""
    schema = _load(name)
    if not HAS_VALIDATOR:
        # 无jsonschema库时做基本类型检查
        return _basic_validate(schema, data)
    try:
        jsonschema.validate(data, schema)
        return (True, [])
    except Exception as e:
        return (False, [str(e)])

def _basic_validate(schema, data, path=""):
    """Fallback: required fields check only"""
    errors = []
    required = schema.get("required", [])
    for f in required:
        if f not in data:
            errors.append(f"{path}.{f}: required field missing")
    return (len(errors) == 0, errors)

def make_prompt_spec(**kw):
    """Create a prompt-spec with sensible defaults"""
    return {
        "project_id": kw.get("project_id", ""),
        "clip_id": kw.get("clip_id", ""),
        "prompt_version": kw.get("prompt_version", "1.0"),
        "sequence_relation": kw.get("sequence_relation", "standalone"),
        "generation_mode": kw.get("generation_mode", "t2v"),
        "reference_roles": kw.get("reference_roles", []),
        "opening_state_source": kw.get("opening_state_source", "planned_start_state"),
        "current_clip_action": kw.get("current_clip_action", ""),
        "endpoint": kw.get("endpoint", ""),
        "completed_beat_exclusions": kw.get("completed_beat_exclusions", []),
        "reserved_future_exclusions": kw.get("reserved_future_exclusions", []),
        "natural_language_prompt": kw.get("natural_language_prompt", ""),
    }

def make_clip_contract(**kw):
    """Create a clip-contract with defaults"""
    return {
        "project_id": kw.get("project_id", ""),
        "clip_id": kw.get("clip_id", ""),
        "parent_clip_id": kw.get("parent_clip_id", None),
        "sequence_index": kw.get("sequence_index", 1),
        "narrative_job": kw.get("narrative_job", ""),
        "target_duration_sec": kw.get("target_duration_sec", None),
        "generation_mode": kw.get("generation_mode", "t2v"),
        "shot_structure": kw.get("shot_structure", "compact_single_take"),
        "already_happened": kw.get("already_happened", []),
        "this_clip_only": kw.get("this_clip_only", []),
        "reserved_for_later": kw.get("reserved_for_later", []),
        "planned_start_state": kw.get("planned_start_state", {}),
        "planned_end_state": kw.get("planned_end_state", {}),
        "continuity_locks": kw.get("continuity_locks", []),
        "allowed_changes": kw.get("allowed_changes", []),
        "status": kw.get("status", "planned"),
    }

def make_project_state(**kw):
    """Create a project-state with defaults"""
    return {
        "schema_version": kw.get("schema_version", "1.0"),
        "state_revision": kw.get("state_revision", 1),
        "project_id": kw.get("project_id", ""),
        "project_mode": kw.get("project_mode", "standalone_clip"),
        "surface": kw.get("surface", {}),
        "clip_budget_sec": kw.get("clip_budget_sec", None),
        "prompt_budget": kw.get("prompt_budget", None),
        "story": kw.get("story", {}),
        "world_bible": kw.get("world_bible", {}),
        "reference_registry": kw.get("reference_registry", []),
        "beats": kw.get("beats", []),
        "clips": kw.get("clips", []),
        "take_history": kw.get("take_history", []),
        "current_clip_id": kw.get("current_clip_id", ""),
        "canon_revision": kw.get("canon_revision", 1),
        "updated_at": kw.get("updated_at", ""),
    }

# 快捷函数
def is_valid_prompt_spec(data):
    return validate("prompt-spec.json", data)[0]

def is_valid_clip_contract(data):
    return validate("clip-contract.json", data)[0]

SCHEMA_MAP = {
    "prompt-spec": "prompt-spec.json",
    "clip-contract": "clip-contract.json",
    "project-state": "project-state.json",
    "gen-run": "gen-run.json",
    "take-review": "take-review.json",
}
