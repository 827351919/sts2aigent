# STS2 AI Agent 产品需求文档 (PRD)

## 1. 项目概述

### 1.1 项目名称
**STS2 AI Agent** - 基于 STS2MCP 与 AIBOT 知识体系的《杀戮尖塔 2》自动化代理

### 1.2 项目背景
本项目希望借鉴两个已有项目的能力，构建一个可独立运行的 AI Agent：

- **STS2MCP**：提供《杀戮尖塔 2》的本地状态读取与动作执行能力
- **AIBOT**：提供面向 STS2 的策略知识、启发式思路与决策框架参考

本项目不直接复制二者实现，而是将它们拆分为两个能力来源：

- `STS2MCP` 作为**控制层**
- `AIBOT` 作为**知识与策略参考层**
- `STS2 AI Agent` 作为**编排与闭环执行层**

### 1.3 项目目标
构建一个能够自动游玩《杀戮尖塔 2》的 Python Agent，先打通“读取状态 -> 做出决策 -> 执行动作 -> 再次读取状态”的完整闭环，再逐步提升胜率与复杂度。

### 1.4 阶段性目标

#### 阶段目标 A：打通闭环
实现单人模式下的最小可用自动代理，能够：

- 识别主要游戏界面状态
- 对当前状态生成一个合法动作
- 执行动作并进入下一状态
- 持续循环直到本局失败或通关

#### 阶段目标 B：提升稳定性
在闭环跑通后，减少卡死、误操作、无效操作与状态失配，提高单局完成率。

#### 阶段目标 C：提升胜率
引入更完整的 AIBOT 知识和更强的决策逻辑，逐步向高难度通关靠近。

### 1.5 当前成功定义
当前阶段的“成功”不是立即达到进阶 10 通关率，而是达到以下标准：

1. Agent 可以在单人模式中自动完成一整局流程
2. Agent 不依赖人工介入即可处理核心场景
3. Agent 具备可复盘的日志和决策记录
4. 系统结构允许后续逐步替换策略与模型，而不需要推倒重来

### 1.6 非目标
以下内容不属于当前阶段目标：

- 直接追求 A20 或高 Ascension 稳定胜率
- 一开始就支持所有 LLM 供应商
- 一开始就支持多人模式
- 一开始就实现 Web UI、训练系统、自动学习
- 复刻 AIBOT 的游戏内 UI、聊天面板和多模式交互体验

---

## 2. 产品定位与核心价值

### 2.1 产品定位
这是一个**面向程序自动化执行**的游戏代理，而不是一个主要服务于游戏内对话交互的 Mod UI。

它的核心职责是：

- 从 `STS2MCP` 获取结构化游戏状态
- 基于规则、知识和 LLM 生成决策
- 执行动作并维护完整的状态机闭环

### 2.2 核心价值

- **闭环优先**：优先确保整局可跑通，而不是先追求高水平策略
- **可解释**：关键动作和原因可追踪、可复盘
- **可扩展**：可逐步引入更多知识、更多模型、更多场景
- **可替换**：状态获取、知识检索、决策引擎、动作执行器彼此解耦
- **可演进**：从规则驱动逐步演进到混合决策和更高胜率

---

## 3. 设计原则

### 3.1 总体原则

1. **先跑通，再变强**
2. **先规则兜底，再引入 LLM**
3. **先 HTTP 直连 STS2MCP，再考虑 MCP transport 抽象**
4. **先覆盖单人模式，再考虑多人模式**
5. **先支持核心状态，再逐步补齐边缘状态**

### 3.2 关键技术取舍

#### 控制层取舍
虽然项目名中保留 “MCP” 背景，但当前实现阶段优先直接调用 `STS2MCP` 暴露的 localhost HTTP API，而不是先实现一个完整 MCP transport client。

原因：

- `STS2MCP` 的 MCP server 本身就是对 HTTP API 的再封装
- Python Agent 作为本地程序，直接走 HTTP 更简单、可调试性更高
- 可以减少 stdio/MCP 工具发现等额外复杂度

结论：

- **P0/P1 阶段：HTTP 直连**
- **P2 以后：可选抽象为 MCP-compatible client**

#### 决策层取舍
P0 阶段不以“纯 LLM 决策”为目标，而采用：

- **规则 / 启发式优先**
- **知识检索增强**
- **必要时调用 LLM**

这样可以降低以下问题：

- LLM 响应慢导致卡回合
- LLM 产生非法动作
- 高成本 prompt 在高频轮询场景下不稳定

---

## 4. 系统架构

### 4.1 总体架构

```text
STS2 Game
  -> STS2MCP Mod
  -> HTTP API (localhost:15526)
  -> STS2 AI Agent
     - Config
     - Logger
     - HTTP Client
     - State Parser / State Machine
     - Knowledge Loader / Retriever
     - Decision Engine
     - Action Executor
     - Run Loop / Supervisor
```

### 4.2 模块职责

| 模块 | 职责 | 关键文件 |
|------|------|----------|
| `mcp_client` | 封装 `STS2MCP` HTTP API，提供状态获取和动作执行接口 | `mcp_client/client.py`, `mcp_client/tools.py` |
| `agent/state` | 将原始 JSON 状态转为内部状态对象，并驱动状态机 | `agent/state/models.py`, `agent/state/manager.py` |
| `knowledge` | 导入 AIBOT 知识，提供检索与摘要 | `knowledge/loader.py`, `knowledge/retriever.py` |
| `agent/decision` | 根据状态和知识生成动作 | `agent/decision/engine.py`, `agent/decision/heuristics.py` |
| `agent/executor` | 执行动作、校验结果、处理重试 | `agent/executor/actions.py` |
| `utils` | 日志、配置、LLM client、通用工具 | `utils/config.py`, `utils/logger.py`, `utils/llm_client.py` |
| `main.py` | Agent 入口、主循环、运行模式控制 | `main.py` |

### 4.3 与参考项目的关系

#### 从 STS2MCP 借鉴 / 依赖

- 游戏状态接口
- 动作执行接口
- 状态字段语义
- 主要 state type 划分

#### 从 AIBOT 借鉴 / 迁移

- 卡牌、遗物、敌人、事件等知识数据
- 构筑偏好与启发式思路
- 决策摘要构建方式
- 规则先行、LLM 增强的混合思路

#### 不直接迁移的部分

- Godot 游戏内 UI
- 游戏内聊天和模式切换面板
- 与 AIBOT 当前运行时强耦合的 Mod 内部逻辑

---

## 5. MVP 定义

### 5.1 MVP 目标
实现一个**可连续运行一整局单人模式**的 Agent。

### 5.2 MVP 范围

#### 必须支持的状态

- `monster` / `elite` / `boss`
- `combat_rewards`
- `card_reward`
- `map`
- `event`
- `rest_site`
- `shop`
- `treasure`
- `card_select`
- `relic_select`
- `hand_select`

#### 可以暂时弱化的能力

- 药水使用可以先只支持明显高价值场景
- 商店策略可以先做保守购买
- 事件策略可以先基于静态优先级和黑名单
- 复杂卡牌组合技可以先不做长链规划

### 5.3 MVP 不做的事

- 多人模式
- Web UI
- 自动学习 / 强化学习
- 高级 prompt 优化系统
- 完整的自然语言协作体验

### 5.4 MVP 验收标准

1. 可以成功连接到本地 `STS2MCP`
2. 能连续轮询状态并识别主要 `state_type`
3. 每个核心状态都能输出一个合法动作
4. 执行动作后能刷新状态并继续前进
5. 一局游戏中不因程序逻辑错误长期卡死
6. 决策和执行日志可回放

---

## 6. 功能需求

### 6.1 P0 核心需求

#### FR-001：状态获取与解析
- **描述**：从 `STS2MCP` 获取 JSON 状态，并解析为内部结构化对象
- **优先级**：P0
- **验收标准**：
  - 支持 `get_game_state(format="json")`
  - 能识别 `state_type`
  - 能提取 player、battle、map、event、shop 等关键字段
  - 能记录状态时间戳与最近一次状态摘要

#### FR-002：状态机驱动闭环
- **描述**：根据不同状态分发到对应决策 handler
- **优先级**：P0
- **验收标准**：
  - 每种核心 `state_type` 至少绑定一个 handler
  - 未知状态进入安全分支而不是崩溃
  - 支持循环执行直到 run 结束或手动停止

#### FR-003：动作执行封装
- **描述**：封装所有核心动作接口，并统一处理超时、错误和重试
- **优先级**：P0
- **验收标准**：
  - 支持战斗、地图、奖励、事件、商店、篝火、选卡、选遗物等主要动作
  - 动作执行失败后有明确错误分类
  - 可配置重试次数

#### FR-004：最小启发式决策引擎
- **描述**：在无 LLM 或 LLM 不可用时仍能完成基础决策
- **优先级**：P0
- **验收标准**：
  - 战斗可完成出牌与结束回合
  - 卡牌奖励可选牌或跳牌
  - 地图可基于简单权重选路
  - 篝火、商店、事件、宝箱可做保守决策

#### FR-005：AIBOT 知识导入
- **描述**：支持加载 AIBOT 导出的知识文件，并按场景检索
- **优先级**：P0
- **验收标准**：
  - 至少支持 cards / relics / enemies / events / builds 等基础数据
  - 可根据当前角色、卡组、遗物做相关知识过滤
  - 可输出知识摘要供启发式或 LLM 使用

#### FR-006：结构化日志与回放
- **描述**：记录状态、决策、动作、结果，支持复盘
- **优先级**：P0
- **验收标准**：
  - 每一步记录 `state -> decision -> action -> result`
  - 失败时可从日志定位到具体状态和动作
  - 支持以 JSONL 或 Markdown 形式导出

### 6.2 P1 增强需求

#### FR-007：LLM 增强决策
- **描述**：在规则引擎基础上，引入可选 LLM 决策辅助
- **优先级**：P1
- **验收标准**：
  - 当规则不确定时可调用 LLM
  - LLM 输出必须经过动作合法性校验
  - LLM 超时或失败时自动回退到规则策略

#### FR-008：多运行模式
- **描述**：支持全自动、半自动、辅助和模拟模式
- **优先级**：P1
- **模式定义**：
  - `full_auto`：自动执行
  - `semi_auto`：给出建议，人工确认后执行
  - `assist`：仅输出建议，不主动执行
  - `simulation`：不连接游戏，只对录制状态做决策演练

#### FR-009：决策解释
- **描述**：输出简洁清晰的“为什么这么做”
- **优先级**：P1
- **验收标准**：
  - 每条决策带原因摘要
  - 区分规则命中、知识命中、LLM 补充三类来源

### 6.3 P2 / P3 长期需求

#### FR-010：多模型支持
- **优先级**：P2
- **范围**：
  - Claude
  - OpenAI
  - DeepSeek
  - Ollama / LM Studio

#### FR-011：角色专精与构筑策略
- **优先级**：P2
- **范围**：
  - 角色特定选牌
  - 角色特定选路
  - 角色特定商店与篝火策略

#### FR-012：学习与评估
- **优先级**：P3
- **范围**：
  - 对局结果聚合
  - 策略效果统计
  - Prompt 与规则的迭代评估

#### FR-013：可视化界面
- **优先级**：P3
- **范围**：
  - 实时状态面板
  - 决策链展示
  - 历史回放界面

---

## 7. 非功能需求

### 7.1 性能需求

| 指标 | 目标值 | 备注 |
|------|--------|------|
| 状态获取耗时 | < 500ms | 单次 HTTP 请求 |
| 单步决策耗时 | < 3s | 含知识检索，不含极端网络抖动 |
| 规则决策耗时 | < 500ms | 无 LLM 场景 |
| LLM 决策超时 | 5-15s 可配置 | 超时后必须回退 |
| 启动知识加载 | < 3s | 基础 JSON 知识 |
| 单进程内存占用 | < 500MB | 不含外部模型服务 |

### 7.2 可靠性需求

- Agent 启动时可检测游戏 / Mod 是否在线
- 网络连接失败时可自动重试
- 动作执行前必须验证当前状态仍匹配预期
- 连续错误达到阈值后应自动暂停，而不是无限乱点
- 遇到未知状态时应进入安全等待或记录错误退出

### 7.3 可维护性需求

- 所有核心行为通过配置文件控制
- 模块间接口清晰，便于替换具体实现
- 关键数据结构有类型定义
- 核心状态与动作映射有测试

### 7.4 可观测性需求

- 日志分级：`DEBUG / INFO / WARNING / ERROR`
- 输出 run id、step id、state_type、action、latency
- 错误日志可关联到原始状态片段
- 支持保存最近 N 次状态快照

---

## 8. 数据与状态设计

### 8.1 内部核心模型

```python
class GameState:
    state_type: str
    raw: dict
    player: dict | None
    battle: dict | None
    map: dict | None
    event: dict | None
    shop: dict | None
    rewards: dict | None
    timestamp: datetime
    step_id: int


class Decision:
    action_name: str
    params: dict
    reason: str
    source: str         # heuristic | knowledge | llm | fallback
    confidence: float
    expected_state: str | None


class ActionResult:
    ok: bool
    message: str
    raw_response: dict | str | None
    retryable: bool
```

### 8.2 状态机设计

| `state_type` | Handler | 处理目标 |
|--------------|---------|----------|
| `monster` / `elite` / `boss` | combat handler | 出牌、目标、药水、结束回合 |
| `hand_select` | combat select handler | 处理战斗内选牌 |
| `combat_rewards` | rewards handler | 领奖励、进入选牌或继续 |
| `card_reward` | card reward handler | 选牌或跳牌 |
| `map` | map handler | 选下一个节点 |
| `event` | event handler | 选事件选项或推进对话 |
| `rest_site` | rest handler | 休息、锻造或其他功能 |
| `shop` | shop handler | 购买或离开 |
| `card_select` | deck select handler | 处理移除、升级、变形等 |
| `relic_select` | relic handler | 选择或跳过遗物 |
| `treasure` | treasure handler | 领取宝箱遗物并继续 |
| `unknown` / `overlay` / `menu` | safe handler | 记录、等待、退出或人工接管 |

### 8.3 配置设计

```yaml
llm:
  provider: "claude"
  model: "claude-sonnet-4-6"
  api_key: "${CLAUDE_API_KEY}"
  base_url: null
  temperature: 0.2
  max_tokens: 2048
  timeout_seconds: 10

stsmcp:
  host: "localhost"
  port: 15526
  timeout_seconds: 10
  reconnect_attempts: 5

agent:
  mode: "full_auto"
  poll_interval_ms: 500
  max_consecutive_errors: 5
  dry_run: false
  enable_llm: false
  enable_knowledge: true
  decision_timeout_seconds: 10
  save_state_snapshots: true

knowledge:
  aibot_path: "./imported/aibot"
  custom_path: "./knowledge/custom"
  enable_cards: true
  enable_relics: true
  enable_events: true
  enable_enemies: true
  top_k: 5

logging:
  level: "INFO"
  file: "logs/agent.log"
```

---

## 9. 决策策略设计

### 9.1 决策分层

#### 第一层：硬规则
用于处理明确且不应交给 LLM 猜测的情况，例如：

- 当前只有一个合法动作
- 卡牌索引、奖励索引、地图索引的合法性约束
- 明确需要推进对话或确认选择

#### 第二层：启发式
用于大部分 P0 场景：

- 战斗出牌顺序
- 卡牌奖励选择
- 地图选路
- 商店购买优先级
- 篝火选择

#### 第三层：知识增强
从 AIBOT 知识中抽取：

- 卡牌基础价值
- 构筑关联
- 敌人威胁点
- 事件风险
- 遗物协同

#### 第四层：LLM 补充
仅在以下场景启用：

- 多个候选动作分数接近
- 出现复杂组合判断
- 规则未覆盖的新状态细节

### 9.2 动作合法性约束
所有决策必须经过执行前校验：

- 动作是否适用于当前 `state_type`
- 索引是否仍在合法范围内
- 目标是否存在
- 当前状态是否已经变化

### 9.3 失败回退策略

1. 动作执行失败 -> 重新拉取状态
2. 若状态已推进 -> 视为成功
3. 若状态未推进且动作非法 -> 重新决策
4. 连续失败超过阈值 -> 暂停 Agent

---

## 10. 开发计划

### Phase 0：项目落地准备
- [ ] 明确目录结构和入口文件
- [ ] 定义配置模型和日志模型
- [ ] 补齐 README 与运行说明

### Phase 1：最小闭环
- [ ] 实现 HTTP client
- [ ] 实现 `GameState` 解析
- [ ] 实现状态机主循环
- [ ] 实现 combat / rewards / map 三个核心 handler
- [ ] 实现基础日志与错误处理

### Phase 2：核心场景补齐
- [ ] 实现 event / rest_site / shop / treasure handler
- [ ] 实现 card_select / relic_select / hand_select handler
- [ ] 实现最小启发式决策器
- [ ] 打通“能自动跑完整局”

### Phase 3：知识接入
- [ ] 导入 AIBOT 基础知识文件
- [ ] 实现知识检索器
- [ ] 将知识摘要注入决策引擎
- [ ] 优化卡牌奖励、地图、商店等场景质量

### Phase 4：LLM 增强
- [ ] 接入单一 LLM provider
- [ ] 设计 Prompt Builder
- [ ] 实现规则优先、LLM 兜底的混合引擎
- [ ] 完善决策解释与回放

### Phase 5：稳定性与评估
- [ ] 录制对局日志
- [ ] 添加回放 / 离线仿真
- [ ] 统计卡死率、完整跑局率、平均层数、胜率
- [ ] 为后续高 Ascension 优化做基线

---

## 11. 验收与评估指标

### 11.1 P0 / MVP 指标

- 能连接游戏：成功率 > 95%
- 单步决策合法率 > 90%
- 单局闭环完成率 > 70%
- 未知状态导致崩溃次数接近 0
- 日志可定位 95% 以上失败原因

### 11.2 P1 指标

- 核心状态覆盖率 > 95%
- 连续运行稳定性明显提升
- 有基本可解释性输出
- 能对多局结果做统计

### 11.3 长期指标

- 平均到达层数
- 精英击败率
- Boss 到达率
- 通关率
- 特定 Ascension 下的胜率

---

## 12. 风险评估

### 12.1 总体判断
项目整体可行，但风险并不在“能不能控制游戏”，而在“能否稳定完成闭环并逐步提升策略质量”。

### 12.2 风险矩阵

| 风险 | 可能性 | 影响 | 说明 | 缓解措施 |
|------|--------|------|------|----------|
| 状态字段变动 | 中 | 高 | 游戏更新或 Mod 更新后 JSON 结构变化 | 对状态字段做适配层，不直接把原始 JSON 散落到全项目 |
| 状态机漏分支 | 高 | 高 | 某个 `state_type` 或边缘界面未覆盖会卡死 | 未知状态统一走 safe handler，并记录原始快照 |
| 动作索引失效 | 高 | 高 | 出牌、奖励、选项执行后索引会变化 | 每次动作后重新拉取状态，不连续假定旧索引仍有效 |
| LLM 非法输出 | 高 | 中 | 给出不存在的动作或参数 | 所有 LLM 输出必须经 schema 和合法性校验 |
| LLM 超时 | 高 | 中 | 回合内决策过慢，影响流畅性 | LLM 只作补充，规则兜底，设置硬超时 |
| 知识迁移成本高 | 中 | 中 | AIBOT 知识结构和当前 Python 侧不一致 | 先只导静态 JSON，不迁移运行时强耦合逻辑 |
| 闭环卡死难复现 | 中 | 高 | 某些状态切换时机和日志不一致 | 保存状态快照与 step id，支持离线复盘 |
| 接口与实现命名误导 | 中 | 中 | 实际走 HTTP，但模块命名叫 MCP，易混淆 | 在文档和代码中明确“当前实现基于 HTTP API” |
| 游戏版本兼容性 | 中 | 中 | STS2 或 Mod 升级后行为变化 | 在 README 和配置中标注适配版本 |
| 胜率预期过高 | 高 | 中 | 团队容易过早追求 A20，导致方案失焦 | PRD 明确阶段目标：先闭环、再稳定、后优化 |
| 商店/事件复杂决策误伤长期胜率 | 中 | 中 | 早期规则太粗糙会埋下策略债务 | 保留策略来源字段，后续可替换局部 handler |
| 过度依赖单一 LLM | 中 | 中 | API 波动影响整体可用性 | P0 不依赖 LLM，P1 也必须可关闭 |

### 12.3 重点风险详解

#### 风险 1：闭环打不断，但会“假推进”
有些动作执行后接口返回成功，但状态未真正推进，或者需要再次拉状态才能进入下一阶段。

应对：

- 每次执行后强制 re-fetch
- 对关键状态变迁建立预期校验
- 把“动作成功”和“状态成功推进”视为两个不同概念

#### 风险 2：战斗是最大复杂度来源
战斗是最高频、最复杂的状态，涉及卡牌索引变化、目标选择、能量约束、回合切换和特殊选牌。

应对：

- P0 战斗策略保持保守
- 不追求复杂连招
- 出牌后立即重拉状态
- 先保证不出非法动作，再追求更优动作

#### 风险 3：AIBOT 的可迁移部分有限
AIBOT 很多价值在知识结构和启发式思路，但其 Godot 运行时、UI、Agent 模式逻辑并不适合直接搬到 Python agent。

应对：

- 把 AIBOT 当“知识来源”和“设计参考”
- 不把“复刻 AIBOT 功能”当目标
- 先做数据导入和规则抽取，再决定哪些 heuristics 需要复写

#### 风险 4：PRD 过大导致实现迟迟不能开始
如果一开始同时追求 MCP 标准化、多 LLM、Web UI、学习优化，项目会长期停留在设计阶段。

应对：

- 严格按 Phase 拆解
- 先做最小闭环版本
- 每个阶段都有明确可运行产物

---

## 13. 里程碑产物

### Milestone 1：能连上
- 可读取当前状态
- 可执行单个动作
- 有基础 CLI

### Milestone 2：能打完战斗并继续前进
- 支持战斗、奖励、地图
- 可连续运行若干层

### Milestone 3：能自动跑完整局
- 核心状态全部覆盖
- 基本不会因未处理状态卡死

### Milestone 4：能复盘与优化
- 日志清晰
- 有对局统计
- 知识开始显著提升决策质量

---

## 14. 附录

### 14.1 参考项目
- `STS2MCP`：提供游戏状态和动作接口
- `Slay_The_Spire_2_AIBot`：提供知识结构与决策思路参考

### 14.2 术语表

| 术语 | 说明 |
|------|------|
| STS2 | Slay The Spire 2，《杀戮尖塔 2》 |
| STS2MCP | 负责游戏状态读取与动作执行的 Mod / API 项目 |
| AIBOT | 现有 STS2 AI Mod 项目，提供知识与启发式参考 |
| 闭环 | 读取状态 -> 决策 -> 执行动作 -> 再次读取状态 |
| Handler | 某种 `state_type` 的专用处理器 |
| Heuristic | 不依赖 LLM 的规则 / 启发式决策逻辑 |

---

**版本**: 1.1  
**日期**: 2026-03-24  
**作者**: Codex
