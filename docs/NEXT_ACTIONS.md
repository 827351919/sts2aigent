# NEXT_ACTIONS.md

## 高优先级

- [x] 创建 `main.py` 入口文件，建立 Agent 启动与主循环骨架
- [x] 实现 `mcp_client/client.py`，直接对接 `http://localhost:15526`
- [x] 定义内部状态模型：
  - `GameState`
  - `Decision`
  - `ActionResult`
- [x] 实现状态机分发逻辑，按 `state_type` 路由到对应 handler
- [x] 先实现三个核心 handler：
  - combat
  - combat_rewards / card_reward
  - map
- [x] 建立基础日志系统，确保每一步可复盘

## Phase 2 准备

- [ ] 实际游戏测试，验证最小闭环
- [ ] 处理测试中发现的 bug
- [ ] 实现 `event` handler
- [ ] 实现 `rest_site` handler
- [ ] 实现 `shop` handler

## 中优先级

- [ ] 实现 `event` handler
- [ ] 实现 `rest_site` handler
- [ ] 实现 `shop` handler
- [ ] 实现 `treasure` handler
- [ ] 实现 `card_select` / `relic_select` / `hand_select` handler
- [ ] 加入动作执行后的状态刷新与重试策略
- [ ] 为未知状态增加 safe handler

## 低优先级

- [ ] 导入 AIBOT 的 cards / relics / enemies / events / builds 基础 JSON
- [ ] 实现知识检索器
- [ ] 设计启发式评分逻辑
- [ ] 增加可选的 LLM 决策增强
- [ ] 增加 `semi_auto` / `assist` / `simulation` 模式

## 已确认的实施顺序

1. 先打通 HTTP client
2. 再做状态机与主循环
3. 再补核心 handler
4. 再导知识
5. 最后再接 LLM

## 暂不处理

- 多人模式
- Web UI
- 自动学习 / 训练系统
- 多模型适配
- 高 Ascension 优化

## 完成标准

当前阶段以以下目标为准：

- 可以自动读取状态
- 可以做出合法动作
- 可以持续推进一整局流程
- 即使失败也能从日志中定位问题
