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

- `sts2-ai-agent-master` 目前仍以目录骨架为主
- 关键实现文件尚未落地：
  - `main.py`
  - `mcp_client/client.py`
  - `agent/state/manager.py`
  - `agent/decision/engine.py`
  - `agent/executor/actions.py`
  - `knowledge/loader.py`
- 项目尚未打通最小运行闭环

## 里程碑状态

| 里程碑 | 状态 | 说明 |
|------|------|------|
| 明确项目方向 | 已完成 | 已完成技术方案与边界梳理 |
| 完善 PRD | 已完成 | 已将目标调整为“先闭环” |
| 搭建基础协作文档 | 已完成 | 补齐项目协作文档 |
| 实现 HTTP client | 未开始 | 需要直连 `STS2MCP` HTTP API |
| 实现状态机主循环 | 未开始 | 需要形成最小可运行闭环 |
| 实现核心 handler | 未开始 | 优先 combat / rewards / map |
| 导入 AIBOT 知识 | 未开始 | 先导基础 JSON |
| 完整跑通单局 | 未开始 | MVP 目标 |

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
