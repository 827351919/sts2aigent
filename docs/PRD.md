# STS2 AI Agent 产品需求文档 (PRD)

## 1. 项目概述

### 1.1 项目名称
**STS2 AI Agent** - 基于 MCP 的《杀戮尖塔2》智能自动化代理

### 1.2 项目目标
构建一个能够通过 MCP 协议控制《杀戮尖塔2》游戏的 AI Agent，融合 AIBOT 的策略知识与 LLM 的推理能力，实现高效、可解释的游戏自动化。

### 1.3 核心价值
- **可解释性**：每一步决策都有明确的逻辑和推理过程
- **可扩展性**：易于切换 LLM 提供商、更新策略知识
- **可调试性**：完整的日志和决策追踪
- **人机协作**：支持全自动和辅助模式

---

## 2. 架构设计

### 2.1 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        STS2 AI Agent                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Config    │  │   Logger    │  │     State Manager       │ │
│  │   配置模块   │  │   日志模块   │  │      状态管理模块        │ │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘ │
│         └─────────────────┼─────────────────────┘               │
│                           ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Agent Core (核心决策层)                │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │   │
│  │  │   Prompt    │  │    LLM      │  │   Strategy      │  │   │
│  │  │   Builder   │  │   Client    │  │   Evaluator     │  │   │
│  │  │  提示构建器  │  │  LLM客户端   │  │   策略评估器     │  │   │
│  │  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘  │   │
│  │         └─────────────────┼──────────────────┘           │   │
│  │                           ↓                              │   │
│  │              ┌─────────────────────────┐                 │   │
│  │              │    Decision Engine      │                 │   │
│  │              │      决策引擎            │                 │   │
│  │              └───────────┬─────────────┘                 │   │
│  └──────────────────────────┼───────────────────────────────┘   │
│                             ↓                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  Action Executor (动作执行层)             │   │
│  │     ┌─────────────────────────────────────────────┐     │   │
│  │     │           MCP Client Wrapper                 │     │   │
│  │     │      (封装 stsmcp 的所有 tools)              │     │   │
│  │     └─────────────────────────────────────────────┘     │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓ HTTP (Port 15526)
┌─────────────────────────────────────────────────────────────────┐
│                     STS2 MCP Server                             │
│                    (来自 stsmcp 项目)                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  Slay The Spire 2 游戏                          │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 模块职责

| 模块 | 职责 | 关键文件 |
|------|------|----------|
| **MCP Client** | 与 stsmcp server 通信，封装所有游戏操作 | `mcp_client/client.py`, `tools.py` |
| **Knowledge Base** | 加载和管理 AIBOT 的策略知识 | `knowledge/loader.py`, `strategies/` |
| **Prompt Builder** | 根据游戏状态构建 LLM Prompt | `agent/prompt_builder.py` |
| **Decision Engine** | 解析 LLM 响应，生成可执行动作 | `agent/decision/engine.py` |
| **State Manager** | 维护游戏状态历史，支持上下文决策 | `agent/state/manager.py` |
| **Action Executor** | 执行决策，处理重试和错误 | `agent/executor/actions.py` |
| **LLM Client** | 支持多 LLM 提供商 (Claude/DeepSeek/OpenAI) | `utils/llm_client.py` |

---

## 3. 功能需求

### 3.1 核心功能

#### FR-001: 游戏状态获取与解析
- **描述**: 通过 MCP 获取游戏状态并解析为结构化数据
- **优先级**: P0
- **验收标准**:
  - 支持获取当前游戏状态（战斗、地图、事件、商店等）
  - 解析 JSON/Markdown 格式为内部 State 对象
  - 检测状态变化并触发决策

#### FR-002: 多场景决策支持
- **描述**: 支持游戏中所有需要决策的场景
- **优先级**: P0
- **支持场景**:
  | 场景 | 决策内容 |
  |------|----------|
  | Combat (战斗) | 出牌顺序、目标选择、药水使用、结束回合 |
  | Map (地图) | 路径选择、节点优先级 |
  | Card Reward (卡牌奖励) | 选牌、跳牌 |
  | Shop (商店) | 购买优先级、金币管理 |
  | Event (事件) | 选项选择 |
  | Rest Site (休息点) | 休息、锻造、其他选项 |
  | Treasure (宝箱) | 遗物选择 |

#### FR-003: 策略知识库集成
- **描述**: 整合 AIBOT 的策略知识到决策过程中
- **优先级**: P0
- **验收标准**:
  - 加载 AIBOT 的 JSON 知识文件
  - 根据当前游戏上下文检索相关知识
  - 将知识注入到 LLM Prompt 中

#### FR-004: 多 LLM 支持
- **描述**: 支持多种 LLM 提供商
- **优先级**: P1
- **支持列表**:
  - Claude (Anthropic API)
  - DeepSeek (AIBOT 原方案)
  - OpenAI GPT 系列
  - 本地模型 (Ollama/LM Studio)

#### FR-005: 决策可解释性
- **描述**: 每一步决策都有清晰的推理过程记录
- **优先级**: P1
- **验收标准**:
  - 记录完整的决策链（状态→Prompt→LLM响应→动作）
  - 生成决策报告（Markdown/HTML）
  - 支持决策回放

#### FR-006: 运行模式
- **描述**: 支持多种运行模式
- **优先级**: P1
- **模式列表**:
  | 模式 | 说明 |
  |------|------|
  | Full Auto (全自动) | AI 完全自主决策，无人干预 |
  | Semi Auto (半自动) | AI 给出建议，人工确认后执行 |
  | Assist (辅助) | 仅在特定场景提供建议 |
  | Simulation (模拟) | 不执行动作，仅输出决策供验证 |

### 3.2 高级功能

#### FR-007: 学习优化
- **描述**: 根据游戏结果优化策略
- **优先级**: P2
- **实现思路**:
  - 记录每局游戏的关键决策和结果
  - 分析胜利/失败的关键因素
  - 调整策略权重和 Prompt

#### FR-008: 多角色专精
- **描述**: 针对不同角色（Ironclad、Silent 等）使用专门策略
- **优先级**: P2
- **验收标准**:
  - 角色特定的卡牌评分
  - 角色特定的流派构建
  - 动态切换策略

#### FR-009: 实时可视化
- **描述**: 提供 Web UI 查看 AI 决策过程
- **优先级**: P3
- **功能**:
  - 实时游戏状态展示
  - 决策过程可视化
  - 历史记录查询

---

## 4. 非功能需求

### 4.1 性能需求

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 决策延迟 | < 3s | 从状态获取到动作执行 |
| MCP 调用 | < 500ms | 单次 MCP tool 调用 |
| LLM 响应 | < 2s | 首 token 返回时间 |
| 内存占用 | < 500MB | 运行时内存 |
| 知识库加载 | < 2s | 启动时加载所有 JSON |

### 4.2 可靠性需求

- **容错**: MCP 连接断开时自动重连（最多 5 次）
- **状态一致性**: 执行动作前验证状态未过期
- **错误恢复**: 动作执行失败时回滚或重试

### 4.3 可维护性需求

- **日志**: 完整记录 DEBUG/INFO/WARNING/ERROR 级别日志
- **配置**: 所有参数通过 YAML/JSON 配置，无需改代码
- **测试**: 核心模块单元测试覆盖率 > 80%

---

## 5. 数据设计

### 5.1 内部数据模型

```python
# 游戏状态
class GameState:
    state_type: StateType  # combat, map, event, shop, etc.
    player: PlayerState
    screen_data: Dict      # 场景特定数据
    timestamp: datetime

# 决策结果
class Decision:
    action: ActionType     # play_card, end_turn, choose_node, etc.
    params: Dict          # 动作参数
    reasoning: str        # 决策理由
    confidence: float     # 置信度 0-1

# 策略知识
class CardKnowledge:
    card_id: str
    base_score: float
    archetypes: List[str]  # 适用流派
    combos: List[str]      # 配合卡牌
    upgrades_priority: int
```

### 5.2 配置文件

```yaml
# config/main.yaml
llm:
  provider: "claude"  # claude | deepseek | openai
  model: "claude-sonnet-4-6"
  api_key: "${CLAUDE_API_KEY}"
  temperature: 0.3
  max_tokens: 4096

mcp:
  host: "localhost"
  port: 15526
  timeout: 10

agent:
  mode: "full_auto"  # full_auto | semi_auto | assist
  poll_interval_ms: 500
  decision_timeout: 30
  enable_knowledge: true
  log_decisions: true

knowledge:
  aibot_path: "./imported/aibot"
  custom_path: "./knowledge/custom"
```

---

## 6. 接口设计

### 6.1 MCP Client 接口

```python
class STS2MCPClient:
    async def connect() -> bool
    async def get_game_state(format: str = "json") -> GameState
    async def play_card(card_index: int, target: Optional[str]) -> Result
    async def end_turn() -> Result
    async def choose_map_node(node_index: int) -> Result
    async def select_card_reward(card_index: int) -> Result
    # ... 其他工具方法
```

### 6.2 Agent 接口

```python
class STS2Agent:
    async def start()  # 启动主循环
    async def stop()   # 停止
    async def decide(state: GameState) -> Decision
    async def execute(decision: Decision) -> Result
    def set_mode(mode: AgentMode)
    def get_stats() -> AgentStats
```

---

## 7. 开发计划

### Phase 1: 基础框架 (Week 1-2)
- [ ] 项目骨架搭建
- [ ] MCP Client 封装
- [ ] 配置和日志系统
- [ ] 基础状态解析

### Phase 2: 核心决策 (Week 3-4)
- [ ] Prompt Builder 实现
- [ ] LLM Client 多提供商支持
- [ ] 决策引擎基础版
- [ ] 战斗场景决策

### Phase 3: 知识集成 (Week 5-6)
- [ ] AIBOT 知识库导入
- [ ] 知识检索系统
- [ ] 全场景决策支持
- [ ] 策略评估器

### Phase 4: 完善优化 (Week 7-8)
- [ ] 多运行模式
- [ ] 决策可解释性
- [ ] 测试覆盖
- [ ] 文档完善

### Phase 5: 高级功能 (Week 9+)
- [ ] Web UI 可视化
- [ ] 学习优化
- [ ] 多角色专精

---

## 8. 风险评估

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| MCP 协议变更 | 中 | 高 | 封装抽象层，隔离变更 |
| LLM 响应不稳定 | 高 | 中 | 添加重试、降温和兜底策略 |
| 游戏版本更新 | 中 | 中 | 状态解析器可配置化 |
| 决策循环性能 | 中 | 中 | 缓存、并行、超时控制 |

---

## 9. 附录

### 9.1 参考资源
- [stsmcp](https://github.com/.../STS2MCP) - MCP Server
- [AIBOT](https://github.com/.../Slay_The_Spire_2_AIBot) - 策略知识来源
- [MCP Protocol](https://modelcontextprotocol.io/) - MCP 协议文档

### 9.2 术语表

| 术语 | 说明 |
|------|------|
| MCP | Model Context Protocol，模型上下文协议 |
| AIBOT | 原有的 AI 自动化项目 |
| STS2 | Slay The Spire 2，《杀戮尖塔2》 |
| Prompt | 发送给 LLM 的提示词 |
| Archetype | 卡组流派（如力量战、毒贼等） |

---

**版本**: 1.0
**日期**: 2026-03-24
**作者**: Claude Code
