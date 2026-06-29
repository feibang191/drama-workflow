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
核心引擎（adapters/）无需外部API Key即可跑通17关回归测试；出图/出视频阶段需要API Key（示例项目EP01卡在Phase 2因Key缺失）。

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

## 视频生成模型 2.0 吸收 (2026-06-20)

从 [Emily2040/视频生成模型-2.0](https://github.com/Emily2040/视频生成模型-2.0) 吸收3个模块：

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

### 系谱
- B1(5月) → B2(5月底) → A(6月，不同设计理念)
- B2已吸收焚诀1-9、经验库、质量评估、预算控制等production级能力
- A是干净的Python包架构(可import)，有适配器层+Block分镜+宫格模板+视频生成模型 Schema

### 升级方向
以A的Python包架构为基座，吸收B2的运营组件（护栏检测/质量评估/预算控制/Trace/仪表盘/经验库/本地回退/交付组装），不做合并巨无霸。

Phase 0 — 修A的3个P0 Bug + B1归档
Phase 1 — 8个B2模块吸收到A (无依赖)
Phase 2 — 焚诀注入 + pipeline编排器
Phase 3 — 输出格式对齐 → 示例项目Phase 2解冻
Phase 4 — 40项统一回归测试

详见: 示例项目项目 `00_立项评估/三系统评估与升级方向_20260623.md`

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

## 东方仙侠 Prompt 审美语言 (2026-06-25 新增)

**核心原则**: Prompt 语言决定了生成结果的审美取向。用西方CG术语（PBR、ACES、4-light布光）写东方仙侠，出来的图就算技术正确，审美也是错的。

### 词库对照: 西方CG → 东方仙侠

| 场景 | ❌ 西方CG语言（过去失败） | ✅ 东方仙侠语言（正确） |
|------|--------------------------|------------------------|
| 风格声明 | PBR materials, ACES Filmic, film grain, 4-light cinematic setup | 水墨渲染, 东方古韵, 缥缈仙气, 诗意留白, ink-wash aesthetic |
| 角色描述 | skin hex, hair hex, cloth hex | 白发素髻的布衣老妪, 双丫髻乡村童女, 古装朴素 |
| 场景氛围 | cold red low-key lighting, hex color value | 冷红冥府, 彼岸花海, 血雾缭绕, 水墨缥缈 |
| 灯光 | warm key + cold blue fill + double golden rim | 晨光熹微, 仙气氤氲, 烛火暖光, 月光清冷 |
| 画质 | hyper-detailed, PBR | 4K, cinematic CG with traditional Chinese aesthetics |
| 拒绝词 | no ugly, no deformed | no cartoon, no anime, no Disney, no Pixar, no western fantasy aesthetic |

### 东方仙侠 Prompt 模板结构

```
[Chinese xianxia ink-wash aesthetic], ethereal misty atmosphere.
[角色身份描述: 用东方叙事，不用色码]。
[具体动作: 用短句/意象式描述]。
[场景: 用水墨/古风词汇，不写技术参数]。
[灯光色调: 用国画色彩名: 月白、青灰、赭石、黛绿]。
[画幅, 画质]。
no cartoon, no anime, no Disney, no Pixar, no western fantasy aesthetic.
```

### 参考图驱动工作流 (2026-06-25 新增)

每个示例项目项目在 `assets/characters/` 下有**多版参考图**（v1~v6+），生图前必须参照：

```python
# 正确顺序:
1. 扫描 assets/characters/ 找参考图 (char_林夏_图像生成 API_v3_master.png 等)
2. 从参考图提取: 肤色/发型/服装款式/材质/色调
3. 用东方仙侠语言写prompt (见词库对照表)
4. 角色年龄硬约束写入prompt (林夏=70+老妪, 阿梨=8岁女童)
5. 生成并立即下载

# 错误: 直接凭印象写prompt → 角色风格不匹配
```

### 示例项目角色参考图特征 (2026-06-25 vision_analyze确认)

**林夏参考图** (`char_林夏_图像生成 API_v3_master.png`):
- 写实CG+东方古韵混合画风 (非纯水墨，非纯CG)
- 冷灰蓝调主色，沉稳庄重气场
- 肤色暖黄偏暗 (东方人种真实肤色)，额头眼角有明显皱纹
- 银白高髻+木簪，不是精致发饰
- 灰蓝宽大长袍，棉麻质感，边缘有磨损痕迹
- 手持竹杖，金色符文在腕间发光
- 眼神坚定沉稳，不是温暖慈祥——**不是"慈祥老奶奶"表情**
- 简约金色手环配饰

**阿梨参考图** (`char_阿梨_图像生成 API_v3.png`):
- 水墨插画风格 (不是写实CG)
- 暖棕/土黄主色调，翠绿铃铛点缀
- 健康小麦色肤色，带红晕，不是白皙皮肤
- 双髻 + 交领右衽传统上衣，粗布棉麻
- 缺牙灿烂笑，调皮眼神，人间烟火气
- 腰部系翠绿玉铃

**两张参考图风格不统一**: 林夏偏写实CG，阿梨偏水墨插画。生图时不可用同一套prompt语言混写。

### 示例项目审美锁 (与 project_style_config.json 同步)

| 元素 | 色调 | 描述 |
|------|------|------|
| 仙界/忘川 | 冷红 #2A1015 | 血雾、彼岸花、冥府幽光 |
| 凡间 | 暖灰/暖黄 | 晨雾、青石巷、古村 |
| 魔气 | 黑红 | 锁妖塔、魔纹 |
| 林夏(凡间态) | 灰蓝衣+白发+暖黄肤 | 70+老妪，朴素布衣，苍老温柔 |
| 林夏(剑尊态) | 仙白剑袍 | 剑尊觉醒态 |
| 阿梨 | 粗布棕+玉铃青 | 8岁女童，双丫髻，缺牙笑 |

### 检查清单 (生成前)

- [ ] 角色年龄是否正确？（林夏=70+阿婆，不是仙子；阿梨=8岁童女，不是少女）
- [ ] 风格词是否用了东方语言？（禁止: PBR/ACES/4-light/dramatic lighting/rim light）
- [ ] 拒绝词是否含西方审美屏蔽？（至少需 no cartoon/anime/Disney/Pixar/western fantasy）
- [ ] 色调是否符合示例项目三色调？（冷红仙界↔暖灰凡间↔黑红魔气）
- [ ] 是否参考了 assets/characters/ 下的实际参考图？
- [ ] 林夏和阿梨是否用了不同的风格语言？（林夏偏CG写实，阿梨偏水墨）

## 开源视频生成框架 吸收 (2026-06-28)

从 [香港大学研究团队/开源视频生成框架](https://github.com/香港大学研究团队/开源视频生成框架) 吸收视频前置校准体系：

### 新增 adapters/video_calibration.py

- `VideoCalibration` 数据类（9字段 + 嵌套结构）
- `PresenceMap` — 人物可见性约束（`humans_allowed` / `forbidden_entities`）
- `ModeRecommendation` — I2V vs FLF2V 选择
- `PromptLayers` — 四层 prompt 结构（asset_instruction / motion / camera / negative_guard）
- `视频生成模型LimitsCheck` — 9图/3视频/3音频/12文件/5000字符硬约束
- `Gate` — 付费提交前 Gate 状态机（BLOCKED / ALLOW_DRY_RUN / ALLOW_PAID_PILOT / ALLOW_BATCH）
- 工厂函数：`make_empty_calibration()` / `make_landscape_calibration()` / `make_human_asset_calibration()`

### 新增 GR010-GR014 (guardrail_rules.py)

| 规则 | 检查项 | 限制 |
|------|--------|------|
| GR010 | Prompt 超长 | ≤5000字符 |
| GR011 | 图片数量 | ≤9张 |
| GR012 | 视频数量 | ≤3个 |
| GR013 | 音频数量 | ≤3个 |
| GR014 | 总文件数 | ≤12个 |

### 参考文档

- `references/相机树机制.md` — Camera Tree 机位继承
- `references/参考图选择器.md` — 参考图职责标注 (5种 Asset Roles)
- `references/镜头分解.md` — StoryboardArtist 镜头拆解
- `references/视频生成框架分析笔记.md` — 本次吸收完整总结
- `references/视频生成框架吸收摘要.md` — 开源视频生成框架 全量吸收总结（7模块+脱敏上传）

### 关键机制

**空镜防补人**：
```python
cal = make_landscape_calibration("SD01A")
# 自动设置 humans_allowed=False + forbidden_entities + FLF2V禁止
```

**空镜 prompt 必须追加**：
```
Landscape-only. No humans, no cultivators, no monks,
no sitting figure, no meditating person, no cross-legged pose,
no new characters, no new props.
```

**付费前 Gate (P0)**：
- prompt ≤ 5000 + 文件数 ≤ 12 + reference_mode=human-asset
- 空镜 `humans_allowed=false` + 不是 FLF2V + `size=720x1280`

## 开源视频生成框架 吸收 (2026-06-29 更新)

### 新增模块

| 模块 | 文件 | 说明 |
|------|------|------|
| Camera Tree | `adapters/camera_tree.py` | 机位继承 + 父子关系 + 优先级镜头提取 |
| Reference Image Selector | `adapters/reference_image_selector.py` | 参考图自动选择 + 职责标注 |
| 多候选评分 | `quality_evaluator.py` 更新 | 并行生成多图 → VLM 选最佳 |

### Camera Tree 机制

```python
from adapters.camera_tree import build_camera_tree, CameraTree

shot_descriptions = [
    {"idx": 0, "cam_idx": 0, "ff_desc": "...", "lf_desc": "..."},
    {"idx": 1, "cam_idx": 0, "ff_desc": "...", "lf_desc": "..."},
    {"idx": 2, "cam_idx": 1, "ff_desc": "...", "lf_desc": "..."},
]
tree = build_camera_tree(shot_descriptions)
priority_shots = tree.get_priority_shot_idxs()
```

**关键规则**：
- 父镜头应包含子镜头内容（如 Wide Shot → Medium Shot）
- 优先选择更大景别作为父镜头
- 必须无环（第一镜头为根）
- `_validate_camera_tree()` 防止自引用和循环

### Reference Image Selector 机制

```python
from adapters.reference_image_selector import (
    ReferenceAsset, ReferenceSet,
    select_reference_images_for_shot,
    format_reference_instruction,
)

# 创建参考素材
portrait = ReferenceAsset(
    asset_id="char_linxia",
    role="identity",  # 5种角色之一
    media_type="image",
    path="assets/characters/linxia.png",
    character_id="C01",
)

# 为镜头选择参考图
selected = select_reference_images_for_shot([portrait], shot_desc)

# 生成 prompt 说明
ref_set = ReferenceSet(assets=selected)
instruction = format_reference_instruction(ref_set)
```

**Asset Roles 优先级**：
1. `identity` (角色身份) — 必须有
2. `environment` (场景锁定) — 强烈建议
3. `composition` (构图锚点) — 建议
4. `motion` (运动参考) — 可选

**硬约束**：
- 图片 ≤ 9，视频 ≤ 3，音频 ≤ 3，总文件 ≤ 12
- 实操建议：控制在 5-8 个文件

### 多候选评分

```python
from adapters.quality_evaluator import evaluate_candidates_parallel

# 并行评估多个候选
candidates = ["img1.png", "img2.png", "img3.png"]
scored = await evaluate_candidates_parallel(candidates, prompt_data)
best = scored[0]  # 最高分
```

### 参考文档

| 文件 | 说明 |
|------|------|
| `references/最佳图像选择器.md` | Best Image Selector 使用指南 |
| `references/小说压缩器.md` | Novel Compressor 使用指南 |
| `references/事件提取器.md` | Event Extractor 使用指南 |
| `references/角色肖像生成.md` | Character Portraits 使用指南 |
| `references/场景提取器.md` | Scene Extractor 使用指南 |
| `references/全局信息规划器.md` | Global Planner 使用指南 |
| `references/智能体循环机制.md` | Agent Loop 使用指南 |
| `references/相机树机制.md` | Camera Tree 详解 |
| `references/参考图选择器.md` | Reference Selector 详解 |
| `references/镜头分解.md` | Shot Decomposition 详解 |

### 下一步行动

| 优先级 | 任务 | 预估 |
|-------|------|------|
| P0 | 多候选评分集成到 pipeline_runner | 2小时 |
| P0 | 参考图自动选择集成到 pipeline_runner | 3小时 |
| P1 | Camera Tree 集成到 block_storyboard | 4小时 |
| P1 | 角色肖像生成器 (character_portrait_generator.py) | 1天 |

## 快捷键
|------|------|
| /guitu_prompts | 生成EP01 prompts.json |
| /guitu_blocks | 生成Block分镜 |
| /guitu_grid | 生成六宫格+Keyframes |
| /guitu_all | 全链路跑通（10关回归） |

## 规则引擎 (19条 — 10条P0/P1/P2 + 9条GR护栏)

### P0/P1/P2规则引擎 (10条)
| 级别 | 规则 | 触发→处理 | 来源 |
|------|------|----------|------|
| P0阻断 | 角色外貌锁 | 首帧含外貌词→强制清洗 | prompt_optimizer |
| P0阻断 | 对白铁律 | video缺对白→阻断 | prompt_optimizer |
| P0阻断 | 首帧禁台词 | firstFrame含引号→清除 | prompt_optimizer |
| P0阻断 | 纯视觉描述 | 抽象情绪词→物理替换 (49组) | prompt_optimizer |
| P0阻断 | 首尾衔接 | 跨镜断裂→自动注入 | shot_connector |
| P1警告 | 动作惯性断裂 | 坐下→奔跑→告警 | shot_connector |
| P1警告 | 严格映射 | 未知角色→标记 | reference_role |
| P1警告 | 空间锚定丢失 | 有道具无边界→审计 | guardrail_rules.GR006 |
| P2建议 | Block不完整 | <3Shot→报告 | block_storyboard |
| P2建议 | Block超时 | >12s→审计 | block_storyboard |

### GR护栏规则 (9条 — guardrail_rules.py)
| 规则 | 严重度 | 检查条件 |
|------|--------|----------|
| GR001 L4+禁止视频生成模型 | BLOCK | L4/L5用了视频生成模型模型 |
| GR002 Reference超槽位 | BLOCK | L1=1张, L2=2张, L3=4张 |
| GR003 未编译阻断 | BLOCK | FLF2V模式缺@图片标签 |
| GR004 角色描述非DNA原文 | BLOCK | prompt与dna_block不匹配 |
| GR005 衣橱未锁定 | BLOCK | active_variation为null |
| GR006 背景未锚定 | WARN | 场景缺空间锚定 |
| GR007 多角色道具穿模 | BLOCK | ≥2角色+≥3道具 |
| GR008 FLF2V注入外观描述 | BLOCK | L1层含颜色/材质词 |
| GR009 三视图Reference | BLOCK | 含三视图标签 |

调用方式：
```python
from adapters import check_all_rules, check_rule
results = check_all_rules(level="L4", model="doubao-视频生成模型-2-0-260128")
blocked = [(rid,sev) for rid,sev,passed,_ in results if not passed]
```

### 🔧 execute_code 最佳实践 (2026-06-25 经验)

本 skill 的大量测试/集成工作通过 `execute_code` (Python sandbox) 执行。以下是高频失败陷阱：

**常见失败模式：**

| 错误 | 原因 | 修复 |
|------|------|------|
| NameError: name 'sys' is not defined | 遗漏 import | 每段都显式 import sys, os, json |
| f-string: unmatched/repeated | 嵌套表达式与括号冲突 | 提取为变量再插值，不要在 f-string 里写三元表达式 |
| SyntaxError: f-string with ) in condition | f-string 中含 ) 在条件表达式内 | 条件赋值到变量再插值 |
| unterminated string literal | API Key 含特殊字符 | 从 yaml 文件读 key，不要硬编码 |
| \U unicodeescape | Windows 路径在 Python 字符串中 | 用 os.path.join() 或 raw string r |
| TypeError: unexpected keyword | 函数签名已变 | 先 inspect.signature() |
| ValueError: too many values to unpack | 函数返回格式变了 | 先 print(type(result)) |
| subprocess.TimeoutExpired | 超时太短 | 视频 API 设 timeout=120，图片设 60 |
| JSONDecodeError: Expecting value | curl 返回空串 | 增大 timeout，检查 API 状态 |
| HTTP 502 on video content URL | 内容端点502 | 改查 data.data.video_info.video_url |

**API Key 安全读取（不从代码硬编码）：**

```python
import yaml
with open(r"C:\Users\Administrator\AppData\Local\hermes\config.yaml") as f:
    cfg = yaml.safe_load(f)
key = next(p['api_key'] for p in cfg.get('custom_providers', [])
           if 'apihub.图像生成 API' in p.get('base_url', ''))
```

**terminal() 工作目录：**

默认 workdir `D:\...\webui` 不存在，每次显式设 `workdir="/tmp"`。或直接用 execute_code 内 subprocess.run。

### 各Adapter状态 (2026-06-25)

| 适配器 | 状态 | 类型 | 用途 | 说明 |
|--------|------|------|------|------|
| 图像生成 API_image | ✅ live | 图片 (同步) | 生图 | 图像生成 API-image-2.1-flash, 1920×1080, ~10s/张, URL立即过期 |
| 图像生成 API_video | ✅ live | 视频 (异步轮询) | 生视频 | 图像生成 API-video-v2.0, 1280×704, 轮询~3-8分钟, 60次轮询 |
| 视频生成模型 | 🟡 骨架 | 预留 | 视频生成模型 2.0 API | 当前未启用 |
| 视频生成 API | 🟡 骨架 | 预留 | Tokln API | 当前未启用 |
| minimax | 🟡 骨架 | 预留 | MiniMax API | 当前未启用 |

适配器通过 `executor.py` 统一 fallback 链调度。新增适配器：继承 `BaseAdapter` + `generate()` + `registry.register()`。

可通过 `register_default_adapters()` 自动从 config.yaml 读