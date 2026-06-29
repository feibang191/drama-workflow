"""Phase 1-2: 质量评估引擎 — 生成前9项Prompt检查 + 生成后7维Shot评分"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class PromptCheck:
    name: str; passed: bool; detail: str = ""
    score: float = 1.0 if True else 0.0

PROMPT_CHECKS = [
    ("去静态化检查", lambda p: "@图片" in p.get("prompt",""), "L1层必须通过@图片绑定角色"),
    ("@标签绑定检查", lambda p: any(f"@图片{i}" in p.get("prompt","") for i in range(1,6)), "至少1个@图片引用"),
    ("单动词原则", lambda p: p.get("prompt","").count("，") <= 2, "单镜头不要超过2个逗号分隔的动作"),
    ("空间锚定检查", lambda p: any(kw in p.get("scene_desc","") for kw in ["前景","中景","背景","[空间锚定]"]), "场景描述需含空间锚定"),
    ("禁止项检查", lambda p: not any(w in p.get("prompt","") for w in ["字幕","水印","logo","text"]), "不允许字幕/水印/logo"),
    ("长度检查", lambda p: 50 <= len(p.get("prompt","")) <= 2000, "prompt长度50-2000字符"),
    ("抽象情绪检查", lambda p: True, "留待check_visual_description()检测"),  # 委派给P0-3
    ("外貌重述检查", lambda p: True, "留待check_appearance_lock()检测"),  # 委派给P0-1
    ("复杂度匹配检查", lambda p: True, "留待GR001检测"),  # 委派给护栏
]

SHOT_SCORE_DIMS = [
    "identity", "prop_consistency", "spatial_anchor",
    "motion_execution", "camera_execution", "style_consistency", "continuity"
]

@dataclass
class ShotQualityReport:
    shot_id: str
    prompt_checks: List[PromptCheck] = field(default_factory=list)
    shot_scores: Dict[str, float] = field(default_factory=dict)
    qa_status: str = "PENDING"  # PASS / FAIL / WARN / PENDING
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

def run_prompt_qa(prompt_data: dict) -> ShotQualityReport:
    """生成前自动Prompt质量检查"""
    checks = []
    for name, check_fn, desc in PROMPT_CHECKS:
        if name in ("抽象情绪检查","外貌重述检查","复杂度匹配检查"):
            # 委派检查，默认通过
            checks.append(PromptCheck(name, True, "委派给专用规则引擎"))
        else:
            try:
                passed = check_fn(prompt_data) if callable(check_fn) else True
                msg = desc
                checks.append(PromptCheck(name, passed, msg))
            except Exception as e:
                checks.append(PromptCheck(name, False, f"检查异常: {e}"))
    
    # 综合评分
    fail_count = sum(1 for c in checks if not c.passed)
    status = "PASS" if fail_count == 0 else ("WARN" if fail_count <= 2 else "FAIL")
    
    return ShotQualityReport(
        shot_id=prompt_data.get("shot_id", "unknown"),
        prompt_checks=checks,
        qa_status=status,
    )

def evaluate_shot(scores: Dict[str, float]) -> Dict:
    """生成后7维Shot评估"""
    avg = sum(scores.values()) / len(scores) if scores else 0
    return {
        "dimensions": scores,
        "average": round(avg, 2),
        "rating": "优秀" if avg >= 4.5 else "良好" if avg >= 3.5 else "合格" if avg >= 2.5 else "不合格",
    }


# ── 多候选图像一致性评分 (开源视频生成框架 BestImageSelector 吸收) ──

@dataclass
class CandidateScore:
    """候选图像评分"""
    image_path: str
    scores: Dict[str, float] = field(default_factory=dict)
    average_score: float = 0.0
    rank: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "image_path": self.image_path,
            "scores": self.scores,
            "average_score": self.average_score,
            "rank": self.rank,
        }


async def evaluate_candidates_parallel(
    candidates: List[str],
    prompt_data: Dict,
    evaluator_fn: Optional[callable] = None,
) -> List[CandidateScore]:
    """
    并行评估多个候选图像
    
    Args:
        candidates: 候选图像路径列表
        prompt_data: 原始 prompt 数据
        evaluator_fn: 评估函数（可选），默认使用规则评估
    
    Returns:
        按平均分排序的 CandidateScore 列表
    """
    if not candidates:
        return []
    
    # 并行评分
    async def score_one(img_path: str) -> CandidateScore:
        if evaluator_fn:
            scores = await evaluator_fn(img_path, prompt_data)
        else:
            scores = _default_score_candidate(img_path, prompt_data)
        
        avg = sum(scores.values()) / len(scores) if scores else 0
        return CandidateScore(image_path=img_path, scores=scores, average_score=avg)
    
    tasks = [score_one(img) for img in candidates]
    results = await asyncio.gather(*tasks)
    
    # 按平均分排序
    results.sort(key=lambda x: x.average_score, reverse=True)
    
    # 设置排名
    for i, result in enumerate(results):
        result.rank = i + 1
    
    return results


def _default_score_candidate(img_path: str, prompt_data: Dict) -> Dict[str, float]:
    """
    默认评分函数（基于规则）
    
    实际使用时应该调用 VLM 模型评估
    """
    scores = {}
    
    # 这里可以集成 VLM 评估
    # 目前返回默认分数
    dimensions = ["identity", "prop_consistency", "spatial_anchor",
                  "motion_execution", "camera_execution", "style_consistency", "continuity"]
    
    for dim in dimensions:
        scores[dim] = 3.5  # 默认中等分数
    
    return scores


def select_best_candidate(
    candidates: List[str],
    prompt_data: Dict,
    evaluator_fn: Optional[callable] = None,
    top_n: int = 1,
) -> List[str]:
    """
    选择最佳候选图像
    
    Args:
        candidates: 候选图像路径列表
        prompt_data: 原始 prompt 数据
        evaluator_fn: 评估函数
        top_n: 返回前 N 个
    
    Returns:
        最佳候选图像路径列表（按评分排序）
    """
    scored = asyncio.run(evaluate_candidates_parallel(candidates, prompt_data, evaluator_fn))
    return [s.image_path for s in scored[:top_n]]


def batch_score_candidates(
    candidates_by_shot: Dict[str, List[str]],
    prompt_data_by_shot: Dict[str, Dict],
    evaluator_fn: Optional[callable] = None,
) -> Dict[str, List[CandidateScore]]:
    """
    批量评估多个镜头的候选图像
    
    Args:
        candidates_by_shot: 每个镜头的候选图像 {shot_id: [img_paths]}
        prompt_data_by_shot: 每个镜头的 prompt 数据
        evaluator_fn: 评估函数
    
    Returns:
        {shot_id: [CandidateScore]}
    """
    results = {}
    
    for shot_id, candidates in candidates_by_shot.items():
        prompt_data = prompt_data_by_shot.get(shot_id, {})
        scores = asyncio.run(evaluate_candidates_parallel(candidates, prompt_data, evaluator_fn))
        results[shot_id] = scores
    
    return results
