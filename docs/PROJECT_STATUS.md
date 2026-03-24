# PROJECT_STATUS.md

## 项目状态摘要

- **项目名称**：STS2 AI Agent
- **当前阶段**：方案明确 / 实现前准备
- **总体目标**：借鉴 `STS2MCP` 和 `AIBOT`，构建一个可自动游玩《杀戮尖塔 2》的 Agent
- **当前优先级**：先打通单人模式的完整闭环，再逐步提升稳定性和胜率

## 当前进展

### 已完成

- 明确了项目定位：
  - `STS2MCP` 作为控制层
  - `AIBOT` 作为知识与策略参考层
  - `STS2 AI Agent` 作为编排与闭环执行层
- 阅读并评估了以下项目：
  - `STS2MCP-main`
  - `Slay_The_Spire_2_AIBot-master`
  - `sts2-ai-agent-master`
- 确认 `STS2MCP` 已具备关键状态读取与动作执行能力
- 确认 `AIBOT` 可作为知识结构和启发式策略来源
- 重写并完善了 `PRD.md`
- 建立了项目入口文档 `CODEX.md`

### 当前现实情况

- `sts2-ai-agent-master` Phase 1 已实现
- 核心文件已落地：
  - `main.py` - Agent 入口和主循环
  - `mcp_client/client.py` - HTTP 客户端
  - `agent/state/models.py` - 状态模型
  - `agent/state/manager.py` - 状态机管理器
  - `agent/decision/engine.py` - 启发式决策引擎
  - `agent/executor/actions.py` - 动作执行器
  - `utils/logger.py` - 日志系统
  - `utils/config.py` - 配置加载
- 已实现最小闭环：状态读取 -> 决策 -> 执行 -> 刷新
- 待实现：`knowledge/loader.py` 等知识库相关功能

### 2026-03-24 修复记录

**Codex Review 发现并修复的问题：**

1. **结构不一致问题**（已修复）
   - `StateManager._combat_handler` 返回扁平结构（`hand`/`energy`/`enemies` 在顶层）
   - `DecisionEngine._combat_decision` 错误地当成嵌套结构读取
   - **修复**：统一按扁平结构读取 context

2. **Action 校验层未同步**（已修复）
   - `ActionExecutor._validate_decision` 还在校验旧 action 名 `select_card`/`select_node`
   - **修复**：更新为新的 action 名 `select_card_reward`/`choose_map_node`
   - 同时修复了 `play_card` 的 hand 读取路径

3. **select_card_reward 参数名错误**（已修复）
   - Agent 发送 `{"index": 0}`，但 STS2MCP 期望 `{"card_index": 0}`
   - **修复**：统一将 `index` 改为 `card_index`（涉及 engine.py 和 actions.py）

4. **战斗回合时序问题**（已修复）
   - Agent 在敌人回合尝试出牌，导致 `Not in play phase` 错误
   - **修复**：添加 `is_play_phase` 检查，非玩家回合时返回 wait

5. **choose_map_node 参数名错误**（已修复）
   - Agent 发送 `{"index": 0}`，但 STS2MCP 期望 `{"map_index": 0}`
   - **修复**：统一将 `index` 改为 `map_index`（涉及 engine.py 和 actions.py）

6. **非玩家回合 wait 动作无效**（已修复）
   - 当 `is_play_phase` 为 False 时返回 wait Decision，但 `wait` 不是有效的 MCP 动作
   - 导致报错 "Unknown action: wait"
   - **修复**：非玩家回合时返回 `None`，主循环检测到 None 则跳过动作执行
   - Agent 发送 `{"index": 0}`，但 STS2MCP 期望 `{"map_index": 0}`
   - **修复**：统一将 `index` 改为 `map_index`（涉及 engine.py 和 actions.py）

**当前状态**：以上参数名和时序问题已修复，可重新测试验证。

## 里程碑状态

| 里程碑 | 状态 | 说明 |
|------|------|------|
| 明确项目方向 | 已完成 | 已完成技术方案与边界梳理 |
| 完善 PRD | 已完成 | 已将目标调整为”先闭环” |
| 搭建基础协作文档 | 已完成 | 补齐项目协作文档 |
| 实现 HTTP client | 已完成 | MCPClient 已实现连接、重试、错误处理 |
| 实现状态机主循环 | 已完成 | main.py 主循环 + graceful shutdown |
| 实现核心 handler | 已完成 | combat / rewards / map 三个 handler |
| 导入 AIBOT 知识 | 未开始 | 先导基础 JSON |
| 完整跑通单局 | 进行中 | 需要实际游戏测试验证 |

## 当前判断

- **可行性**：可行
- **主要技术路线**：HTTP 直连 `STS2MCP`，规则/启发式优先，AIBOT 知识增强，LLM 作为后续补充
- **当前重点**：不要过早追求高难度胜率，先把“状态读取 -> 决策 -> 执行 -> 状态刷新”的循环跑起来

## 主要风险

- 状态机漏分支导致卡死
- 动作执行后索引变化导致非法操作
- 项目目标过大，迟迟无法进入实现
- 过早依赖 LLM 导致系统不稳定

## 下一阶段目标

1. 创建 `main.py` 和基础配置加载逻辑
2. 实现 `STS2MCP` HTTP client
3. 定义内部 `GameState` / `Decision` / `ActionResult` 模型
4. 打通 combat / rewards / map 三个核心状态
5. 形成最小自动运行闭环

## 最近更新时间

- 2026-03-24
