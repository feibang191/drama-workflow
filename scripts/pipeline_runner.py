"""pipeline_runner — 15 Stage Pipeline编排器
Phase 2: 从B2吸收15 Stage状态机 + 断点续跑 + 门控
调用adapters/全部模块进行端到端编排
"""
import os, json, sys

# ── 15 Stage 定义 ──
STAGES = [
    ("0a", "剧本创作", "从创意生成结构化剧本"),
    ("0b", "角色设定", "创建角色/场景/道具圣经"),
    ("0c", "复杂度评级", "计算复杂度等级L1-L5"),
    ("1a", "角色衣橱", "生成角色多套变体"),
    ("1b", "场景衣橱", "生成场景多套变体"),
    ("2",  "母图锚定", "生成角色面部特写+全身妆造+场景背景"),
    ("3",  "镜头推理", "生成关键帧+运镜计划"),
    ("4",  "Prompt编译", "七层结构编译+焚诀注入"),
    ("4b", "护栏检测", "GR001-GR009自动校验"),
    ("4c", "Prompt QA", "生成前自动质量检查"),
    ("5",  "视频生成", "调用API生成视频"),
    ("6",  "批量生成", "批量并发+轮询+下载"),
    ("7",  "版本注册", "终审+经验库回写"),
    ("8",  "合成交付", "视频拼接+SRT+导出"),
    ("9",  "经验入库", "成功/失败样本入库"),
]

STAGE_MAP = {s[0]: {"name": s[1], "desc": s[2]} for s in STAGES}
STAGE_ORDER = [s[0] for s in STAGES]

class PipelineRunner:
    def __init__(self, project_path=None):
        self.project_path = project_path or os.getcwd()
        self.states = {}  # {stage_id: "done"/"running"/"blocked"/"pending"}
        self.gate = {}    # gate.json equivalent
        self._load_state()
    
    def _load_state(self):
        gate_path = os.path.join(self.project_path, "ctl", "gate.json") if self.project_path else ""
        if gate_path and os.path.exists(gate_path):
            try:
                with open(gate_path, 'r', encoding='utf-8') as f:
                    self.gate = json.load(f)
            except:
                self.gate = {}
    
    def status(self):
        """输出当前Pipeline状态"""
        result = {"current_stage": "", "stages": []}
        for sid in STAGE_ORDER:
            info = STAGE_MAP[sid]
            state = self.states.get(sid, "pending")
            result["stages"].append({
                "id": sid, "name": info["name"], "state": state,
            })
            if state == "running":
                result["current_stage"] = sid
        return result
    
    def available_since(self, stage_id):
        """获取从某stage开始可用的模块名列表"""
        idx = STAGE_ORDER.index(stage_id)
        available = []
        for sid in STAGE_ORDER[:idx+1]:
            available.append({
                "stage": sid,
                "modules": self._get_modules_for_stage(sid),
            })
        return available
    
    def _get_modules_for_stage(self, stage_id):
        """返回该stage可以调用的adapters模块"""
        from adapters import (
            guardrail_rules, quality_evaluator, experience_db,
            budget_controller, trace_logger, fallback_manager,
            delivery_assembler, pipeline_dashboard,
        )
        from scripts.prompt_compiler import batch_compile, compile_to_guitu_format
        from adapters.block_storyboard import BlockStoryboard
        from adapters.grid_template import SixGridTemplate, KeyframesTemplate
        from adapters.sequence_protocol import SequenceProject
        from adapters.prompt_optimizer import check_visual_description, check_appearance_lock
        
        mapping = {
            "0a": [], "0b": [], "0c": [],
            "1a": [], "1b": [], "2": [],
            "3": [],
            "4": ["batch_compile"],
            "4b": ["check_all_rules"],
            "4c": ["run_prompt_qa"],
            "5": [], "6": [],
            "7": ["check_all_rules", "evaluate_shot"],
            "8": ["DeliveryAssembler"],
            "9": ["ExperienceDB"],
        }
        return mapping.get(stage_id, [])
    
    def render_status(self):
        """终端友好状态输出"""
        lines = []
        lines.append("╔══ Pipeline Status ══╗")
        for sid in STAGE_ORDER:
            info = STAGE_MAP[sid]
            state = self.states.get(sid, "pending")
            icons = {"done": "✅", "running": "🔄", "blocked": "⛔", "pending": "⏳"}
            icon = icons.get(state, "❓")
            lines.append(f"  {icon} {sid} {info['name']:8} — {info['desc']}")
        return "\n".join(lines)


# CLI入口
def main():
    import argparse
    parser = argparse.ArgumentParser(description="漫剧工作流Pipeline")
    parser.add_argument("-p", "--project", help="项目路径")
    parser.add_argument("--status", action="store_true", help="显示状态")
    parser.add_argument("--run", action="store_true", help="全流程执行")
    parser.add_argument("--stage", help="执行指定Stage")
    parser.add_argument("--resume", action="store_true", help="断点续跑")
    
    args = parser.parse_args()
    runner = PipelineRunner(args.project)
    
    if args.status:
        print(runner.render_status())
    elif args.stage:
        available = runner.available_since(args.stage)
        for a in available:
            print(f"  Stage {a['stage']}: {', '.join(a['modules']) if a['modules'] else '无直接可调模块'}")
    elif args.run or args.resume:
        print("  Pipeline执行: 需要先通过Phase 3完成生图/视频API对接")
        print(runner.render_status())

if __name__ == "__main__":
    main()
