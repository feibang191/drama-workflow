---
name: drama-workflow
description: "漫剧工业化工作流 v4.4 — Python包基座，含三系统评估与B2吸收路线。吸收 视频生成模型 2.0 Skill OS 后重构。从剧本文本到 Block/六宫格/Keyframes 的全链路离线流水线，含结构化 Schema 契约 + 连续性协议 + 参考角色分离。"
version: 4.4.1
author: "南山 (作者)"
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [漫剧, 短剧, 工业化, 工作流, adapters, 视频生成模型, 连续性, Schema]
    related_skills: [ai-drama-project-assessment, ai-drama-script-design, ai-drama-script-writer, ai-drama-storyboard-design, ai-drama-video-prompt-engineering, drama-industrial-workflow-v2, workflow/continuity-guard]
---

# drama-workflow v4.4

漫剧工业化工作流。从剧本文本到Block分镜/六宫格/Keyframes的全链路离线流水线。
核心引擎（adapters/）无需外部API Key即可跑通17关回归测试；出图/出视频阶段需要API Key

---

## 架构

```
L6 交付层       Block分镜(中间数据) | 六宫格(3x2竖屏/2x3横屏) | Keyframes(首帧+视频+尾帧)
L5 质量门       P0/P1/P2 规则引擎 (10条规则)
L4 策略层       BlockStoryboard + 运镜推理 + 节奏规划
L3 编译层       prompt_compiler (7层体系: L1主体~L7全局约束)
L2 适配层       6个API适配器 + 元数据 + 角色库 + 批量
L1 基础层       角色圣经 | 场景圣经 | 道具圣经 | 相机语言
```

## 视频生成模型 (2026-06-20)更新


### 1. adapters/schemas/ — 结构化数据契约

5个JSON Schema，所有中间数据经过契约校验：

| Schema | 用途 | 关键字段 |
|--------|------|---------|
| prompt-spec.json | prompt元数据封装 | sequence_relation, generation_mode, reference_roles |
| clip-contract.json | 单镜头合同（状态机） | planned_start/end_state, continuity_locks, status |
| project-state.json | 多clip项目状态 | beats, clips, take_history, canon_revision |
| gen-run.json | 单次生成记录 | generation_mode, seed, status |
| take-review.json | 审查结果 | verdict, repair_variable, continuity_deviations |

使用方式：
```python
from adapters.schemas import make_prompt_spec, make_clip_contract, validate
ps = make_prompt_spec(project_id="示例项目", clip_id="SD01")
ok, errors = validate("prompt-spec.json", ps)
```

### 2. adapters/sequence_protocol.py — 连续性协议

多clip序列管理，基于实际生成结果驱动下一clip：

- `ClipContract` — 单镜头合同类，携带状态机（planned→ready→generated→reviewed→accepted）
- `SequenceProject` — 多clip序列项目，advance()推进下一clip
- `check_continuity_locks()` — 检测连续性锁违规（如"灰蓝布衣→白衣剑尊"跨clip突变）
- 三级范围控制：already_happened / this_clip_only / reserved_for_later
- 7种连续性关系：standalone / seamless_continuation / bridge_between_known_states / repair_tail 等

### 3. adapters/reference_role.py — 参考角色分离

每个参考素材按角色标注，非混用：

| 角色 | 媒体类型 | 持久度 | 嵌入位置 |
|------|---------|--------|---------|
| identity | image | 项目不变 | L1-L2 |
| environment | image/video | 场景级 | L2 |
| motion | video | clip级 | L4 |
| camera_rhythm | video | 序列级 | L5 |
| audio_tempo | audio | clip级 | L6 |
| style | image/video | 项目级 | L5-L6 |
| endpoint | image | clip级 | L3 |

使用方式：
```python
from adapters.reference_role import ReferenceAsset, ReferenceRegistry
reg = ReferenceRegistry()
reg.register(ReferenceAsset(asset_id="char_01", role="identity",
    media_type="image", path="assets/linxia.png", character_id="C01"))
```

## Pipeline Stages (15门 — pipeline_runner.py 编排)

| Stage | 名称 | 工具/模块 | 产出 | 门控 |
|-------|------|-----------|------|------|
| 0a | 剧本创作 | ai_drama_script_writer | source.md | 5幕20SD |
| 0b | 角色设定 | character_database.py | 角色/场景/道具圣经 | 视觉锚点锁定 |
| 0c | 复杂度评级 | guardrail_rules.GR001 | L1-L5等级 | L5强制拆镜 |
| 1a | 角色衣橱 | experience_db + char_db | 角色变体 | active_variation非null |
| 1b | 场景衣橱 | scene_wardrobe | 场景变体+道具 | 空间锚定 |
| 2 | 母图锚定 | executor→adapter fallback | 首帧图/身份板 | 适配器健康 |
| 3 | 镜头推理 | camera_mapper + shot_connector | 关键帧+运镜计划 | 动作连续性检查 |
| 4 | Prompt编译 | prompt_compiler (焚诀注入) | prompts.json | P0/P1/P2规则 |
| 4b | 护栏检测 | guardrail_rules.check_all_rules | 9条GR报告 | ALL PASS |
| 4c | Prompt QA | quality_evaluator.run_prompt_qa | QA报告 | FAIL阻断 |
| 5 | 视频生成 | executor→adapter fallback | 视频片段 | API Key (阻塞) |
| 6 | 批量生成 | batch_video_runner | 多段视频 | --confirm |
| 7 | 版本注册 | trace_logger + quality_evaluator | 版本注册表 | 7维评分 |
| 8 | 合成交付 | delivery_assembler.DeliveryAssembler | SRT+拼接视频 | ffmpeg成功 |
| 9 | 经验入库 | experience_db.ExperienceDB | 成功/失败样本 | 自动回写 |

### 视频管线 (异步，2026-06-25 建立)

通过 `scripts/run_video_pipeline.py` 运行：

```bash
# 后台启动（因为execute_code有5分钟硬超时）
terminal(background=true, workdir="/tmp")
python3 scripts/run_video_pipeline.py  # 自动从config.yaml读Key
```

**关键参数**:
- 模型: `图像生成 API-video-v2.0` (T2V)
- 分辨率: 1280×704
- 时长: 5秒
- 轮询间隔: 15秒，最多60次(15分钟)
- 状态机: queued → IN_PROGRESS → SUCCEEDED / FAILED / CANCELLED

**详细参考**: `references/图像生成 API-api-session-20260625.md`

## 完整模块清单（34个模块，Phase 0-4四次升级）

```
adapters/
├── schemas/                数据契约（6个JSON Schema）
│   ├── __init__.py         Schema验证器 + 工厂函数
│   ├── prompt-spec.json    prompt元数据封装
│   ├── clip-contract.json  单镜头合同（状态机）
│   ├── project-state.json  多clip项目状态模型
│   ├── gen-run.json        单次生成记录
│   ├── take-review.json    审查结果契约
│   └── module-count.json   模块计数（34个）
│                                      ← 核心创作模块 (7个)
├── character_database.py   角色圣经/场景圣经数据结构     ← 无依赖
├── camera_mapper.py        ★ 全镜头语言: 8景别+7角度+12运镜+23情绪+13节拍   ← 无依赖 (v2)
├── template_engine.py      变量替换+clean               ← 无依赖
├── prompt_optimizer.py     P0规则(首帧88词禁止/49组抽象→物理) ← 无依赖 (v2)
├── shot_connector.py       P1动作惯性引擎               ← 无依赖
├── block_storyboard.py     P2-1 Block分镜系统           ← 依赖 shot_connector + schemas
├── grid_template.py        P2-2 宫格模板系统(6种)       ← 无依赖（纯模板渲染）
│                                      ← 视频生成模型吸收 (3个)
├── sequence_protocol.py    连续性契约(视频生成模型吸收)     ← 依赖 schemas
├── reference_role.py       参考角色分离(7种角色)        ← 无依赖
│                                      ← 适配器层 (6个)
├── base.py                 API适配器基类+异常            ← 无依赖
├── registry.py             适配器注册表                  ← 依赖 base
├── executor.py             fallback链执行器             ← 依赖 registry + base
├── 视频生成模型.py             视频生成模型 2.0 API适配器       ← 依赖 base
├── 图像生成 API.py                ★ 图像生成 API API适配器 (图片+视频) ← 依赖 base (v4, 2026-06-25)
├── metadata.py             元数据嵌入(PNG/MP4)          ← 无依赖
│                                      ← ★ Phase 1新模块 (8个)
├── guardrail_rules.py      ★ 护栏规则: 9条GR(BLOCK/WARN)  ← 无依赖
├── quality_evaluator.py    ★ 质量评估: 9项Prompt+7维Shot  ← 无依赖
├── experience_db.py        ★ 经验库: 成功/失败/模型三类    ← 无依赖
├── budget_controller.py    ★ 预算: 费用/API/重试/时间四维  ← 无依赖
├── trace_logger.py         ★ Trace: Stage级运行记录      ← 无依赖
├── fallback_manager.py     ★ 回退: 4级降级+指数退避       ← 无依赖
├── delivery_assembler.py   ★ 交付: 视频拼接+SRT+ffmpeg   ← 无依赖
├── pipeline_dashboard.py   ★ 仪表盘: 项目状态+终端输出    ← 无依赖
│                                      ← ★ Phase 2新模块 (4个)
├── camera_tree.py          ★ 相机树(基于开源视频生成框架)           ← 无依赖
├── reference_image_selector.py ★ 参考图选择(基于开源视频生成框架)   ← 无依赖
│                                      ← ★ Phase 3新模块 (3个)
├── video_calibration.py    ★ 视频校准(基于开源视频生成框架)         ← 无依赖
├── shot_connector.py       ★ 镜头连接器(增强)            ← 无依赖
├── block_storyboard.py     ★ Block分镜(增强)             ← 无依赖
│                                      ← ★ Phase 4 开源视频生成框架全量吸收 (7个)
├── best_image_selector.py  ★ MLLM自动选最佳图(P0)        ← 无依赖
├── novel_compressor.py     ★ 小说→分集压缩(P1)           ← 无依赖
├── event_extractor.py      ★ 事件链提取(P1)              ← 无依赖
├── character_portraits_generator.py ★ 角色肖像生成(P2)   ← 无依赖
├── scene_extractor.py      ★ 场景自动提取(P2)            ← 无依赖
├── global_information_planner.py ★ 全局规划(P2)          ← 无依赖
├── agent_loop.py           ★ Agent状态机(P3)             ← 无依赖
│
├── __init__.py             统一导出(from adapters import *)
│
scripts/
    ├── prompt_compiler.py  7层Prompt编译引擎 + 焚诀4/5/6/7/9注入 + compile_to_guitu_format ← 依赖全部adapters模块
    ├── pipeline_runner.py  15 Stage Pipeline编排器（Stage 0a-9）
    ├── run_video_pipeline.py 视频管线(异步, 2026-06-25)
    └── verify_full_chain.py 回归测试（17项核心验证）
```

模块依赖链: 全部单向，无循环引用。下层不引用上层。
总文件数: 34个 .py + 6个 .json schema + 4个 scripts = 44个文件
总代码量: 155KB (adapters/) + 25KB (scripts/) = 180KB

## 全链路回归测试（13项核心验证）

每次修改任一模块后执行。使用示例项目EP01 source.md（20SD/60s）：

```bash
python3 scripts/verify_full_chain.py
```

验证项目：
```
 1. 剧本输入      → 20 SD镜头分割
 2. 角色数据库    → CharacterDB（1角色+3场景）
 3. P0外貌锁     → 检出2项（首帧88词/49组抽象→物理）
 4. Block分镜    → 7Block/20Shot
 5. 7层编译      → L1~L7全部输出
 6. full_prompt  → 全部含完整7层
 7. Schema验证   → prompt-spec valid=True
 8. ClipContract → 20个全部生成且Schema通过
 9. 六宫格       → 1466字符（3×2竖屏）
10. Keyframes    → 475字符（首帧+视频+尾帧）
11. Sequence     → clip契约状态机推进到index=1
12. Adapter链    → fallback执行器(simulated)
13. 双格式兼容   → dataclass=7层 / dict=7层
```

失败排查：
| 关卡 | 常见失败 | 修复 |
|------|---------|------|
| 1 | 剧本路径不对/编码 | 检查 source.md |
| 2 | 导入路径错误 | sys.path 指向 drama-workflow/ |
| 3 | FIRST_FRAME_FORBIDDEN未导出 | __init__.py 需导出该变量 |
| 4 | Shot.dataclass vs dict不兼容 | 统一用 _get_val() 适配双格式 |
| 5 | 同4 | — |
| 6 | prompt_compiler import循环 | 检查 sys.path insert 位置 |
| 7-8 | 编译输出字段缺失 | 检查 compile() 方法返回值 |
| 9-10 | Schema必填字段缺失 | natural_language_prompt 不能为空 |
| 11-12 | shot dict 缺key | 确保含 shot_id/description |
| 13 | add_clip后没advance | 状态机需按序走 |
| 14 | media_type不在allowed_media | 检查 image/video/audio |
| 15 | 适配器未注册 | registry.register() 需先调用 |
| 16 | 姿态变化警告 | 剧本本身的蹲→站/坐→站变化是正常检测 |
| 17 | ClipContract必填字段缺失 | 检查合同构造参数 |


## 三系统关系 (2026-06-23 评估)

本skill（系统A, adapters/ v4.4）不是独立存在的。Hermes Studio中另有两套漫剧工作流系统：

| 系统 | 位置 | 行数 | 状态 | 关系 |
|------|------|------|------|------|
| A (本skill) | skills/writing/drama-workflow/ | 1,382行 | ✅ active | Python包基座 |
| B2 | skills/drama-industrial-workflow-v2/ | 6,879行 | ✅ installed | 生产演化版，从WSL迁移 |
| B1 | 00_索引/v2.2_可复用文件包/ | 8,319行 | ❌ archived | 初代原型，被B2覆盖 |


## 前置依赖：AI漫剧SKILL模块（5个，独立于本skill）

Pipeline Stages (-1到6) 引用的工具对应5个独立skill（非本skill代码）：

| Stage | 对应skill | 位置 |
|-------|----------|------|
| -1 立项评估 | ai-drama-project-assessment | `skills/AI漫剧/AI漫剧立项与评估/SKILL.md` |
| -0.5 故事设计 | ai-drama-script-design | `skills/AI漫剧/AI漫剧剧本设计/SKILL.md` |
| 0a 剧本创作 | ai-drama-script-writer | `skills/AI漫剧/AI漫剧剧本创作/SKILL.md` |
| 3 故事板 | ai-drama-storyboard-design | `skills/AI漫剧/AI漫剧分镜设计/SKILL.md` |
| 4 生成执行 | ai-drama-video-prompt-engineering | `skills/AI漫剧/AI漫剧视频提示词工程/SKILL.md` |

本skill(adapters/)只负责Stage 2(Prompt编译)+3后半(Block/宫格)之后的部分。

.register()`。

可通过 `register_default_adapters()` 自动从 config.yaml 读
