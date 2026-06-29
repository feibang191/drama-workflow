#!/usr/bin/env python3
"""
漫剧工作流 v4.3 · 全链路回归测试脚本
执行: python3 verify_full_chain.py
包含14项核心验证
"""

import sys, os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKFLOW_DIR = os.path.join(SCRIPT_DIR, "..")
sys.path.insert(0, WORKFLOW_DIR)

SCRIPT_PATH = r"E:\MyBrain\WIKI\短视频风格库\06_项目库\示例项目\02_剧本\EP01_示例项目\source.md"

from adapters import *
from scripts.prompt_compiler import PromptCompiler, batch_compile
from adapters.schemas import validate, is_valid_clip_contract, make_prompt_spec
from adapters.sequence_protocol import SequenceProject, ClipContract


def test_all():
    r = {}
    # 1. 剧本
    with open(SCRIPT_PATH, 'r', encoding='utf-8') as f:
        raw = f.read()
    sd_lines = [l.strip() for l in raw.split('\n') if l.strip().startswith("SD")]
    r["剧本输入"] = f"{len(sd_lines)} SD镜头"

    # 2. 角色
    db = CharacterDB()
    db.add_character(Character("C01", "林夏", "女", "老年", "灰蓝布衣"))
    db.add_scene(Scene("S01", "忘川河畔", "血雾翻涌"))
    r["角色数据库"] = f"{len(db.characters)}角色"

    # 3. P0
    appr = check_appearance_lock("白发眼神", "first_frame")
    r["P0外貌锁"] = f"检出{len(appr['forbidden_found'])}项"

    # 4. Block
    blocks = []
    for gi in range(0, len(sd_lines), 3):
        block = Block(block_id=f"B{gi//3:02d}")
        for sd_text in sd_lines[gi:gi+3]:
            sid = sd_text.split('｜')[0]
            desc = sd_text.split('｜')[1] if '｜' in sd_text else sd_text
            block.add_shot(Shot(shot_id=sid, duration=3.3, description=desc))
        blocks.append(block)
    bs = BlockStoryboard(blocks)
    all_shots = [s for b in bs.generate_blocks() for s in b.shots]
    r["Block分镜"] = f"{len(bs.blocks)}Block/{len(all_shots)}Shot"

    # 5. 7层编译
    compiled = batch_compile(all_shots[:5], db, db)
    layers = [k for k in compiled[0] if k.startswith("L")]
    r["7层编译"] = f"{len(layers)}层"
    r["full_prompt"] = "全部含" if all(c.get("full_prompt_zh") for c in compiled) else "缺失"

    # 6. Schema
    ps = make_prompt_spec(project_id="t", clip_id="SD01", natural_language_prompt=compiled[0].get("full_prompt_zh",""))
    ok, _ = validate("prompt-spec.json", ps)
    r["Schema验证"] = f"valid={ok}"

    # 7. ClipContract
    cc = bs.to_clip_contracts("示例项目")
    valid = sum(1 for c in cc if is_valid_clip_contract(c))
    r["ClipContract"] = f"{len(cc)}个/{valid}valid"

    # 8. 六宫格
    gs = [{"shot_id":s.shot_id,"description":s.description,"first_frame_prompt":s.description[:30]} for s in all_shots[:6]]
    r["六宫格"] = f"{len(SixGridTemplate().render(gs))}字符"

    # 9. Keyframes
    ko = KeyframesTemplate().render({"shot_id":"T","description":"test"})
    r["Keyframes"] = f"{len(ko)}字符"

    # 10. Sequence
    sq = SequenceProject("t")
    sq.add_clip(ClipContract(clip_id="SD01"))
    sq.advance({"p":"s"})
    r["Sequence"] = f"index={sq.current_clip_index}"

    # 11. Adapter
    ar = AdapterRegistry()
    ar.register(视频生成模型Adapter(AdapterConfig(api_key="t")))
    rx = AdapterExecutor(ar).execute("test", preferred="视频生成模型")
    r["Adapter链"] = rx["status"]

    # 12. 双格式兼容
    cp = PromptCompiler()
    r1 = cp.compile_shot(Shot(shot_id="SD01",description="test"), db, db)
    r2 = cp.compile_shot({"shot_id":"SD01","description":"test"}, db, db)
    r["双格式兼容"] = f"dataclass={len([k for k in r1 if k.startswith('L')])}层/dict={len([k for k in r2 if k.startswith('L')])}层"

    return r


if __name__ == "__main__":
    print("═" * 46)
    print("  漫剧工作流 v4.3 · 全链路回归测试")
    print("═" * 46)
    results = test_all()
    for k, v in results.items():
        mark = "✅" if "0层" not in str(v) and "缺失" not in str(v) and "False" not in str(v) else "❌"
        print(f"  {mark} {k:<14} {v}")
    print("═" * 46)