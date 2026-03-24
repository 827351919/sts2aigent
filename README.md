# STS2 AI Agent

基于 MCP 协议的《杀戮尖塔2》智能自动化代理

## 项目简介

本项目结合了 **stsmcp** 的 MCP 游戏控制能力 和 **AIBOT** 的策略知识库，构建一个可通过 LLM 自动玩《杀戮尖塔2》的 AI Agent。

## 特性

- 🎮 **MCP 控制**: 通过 MCP 协议直接控制游戏
- 🧠 **LLM 决策**: 支持 Claude、DeepSeek、OpenAI 等多种 LLM
- 📚 **策略知识**: 集成 AIBOT 的卡牌、遗物、敌人策略数据
- 🔍 **可解释**: 每一步决策都有清晰的推理过程
- ⚙️ **多模式**: 全自动、半自动、辅助模式可选

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repo-url>
cd sts2-ai-agent

# 安装依赖
pip install -r requirements.txt

# 复制配置文件
cp config/example.yaml config/main.yaml
# 编辑 config/main.yaml，填入 API Key
```

### 2. 启动游戏和 MCP Server

确保《杀戮尖塔2》已安装 stsmcp mod，并启动游戏。

### 3. 运行 AI Agent

```bash
# 全自动模式
python main.py --mode full_auto

# 半自动模式
python main.py --mode semi_auto
```

## 项目结构

```
sts2-ai-agent/
├── docs/              # 文档
│   └── PRD.md         # 产品需求文档
├── mcp_client/        # MCP 客户端封装
│   ├── client.py
│   └── tools.py
├── knowledge/         # 策略知识库
│   ├── cards/         # 卡牌策略
│   ├── relics/        # 遗物策略
│   ├── enemies/       # 敌人策略
│   ├── builds/        # 流派构建
│   └── events/        # 事件策略
├── agent/             # AI Agent 核心
│   ├── decision/      # 决策逻辑
│   ├── executor/      # 动作执行
│   └── state/         # 状态管理
├── utils/             # 工具模块
├── config/            # 配置文件
├── tests/             # 测试
└── main.py            # 入口
```

## 配置说明

```yaml
# config/main.yaml
llm:
  provider: "claude"  # claude | deepseek | openai
  model: "claude-sonnet-4-6"
  api_key: "your-api-key"

agent:
  mode: "full_auto"  # full_auto | semi_auto | assist
  poll_interval_ms: 500

knowledge:
  aibot_path: "./imported/aibot"
```

## 致谢

- [STS2MCP](https://github.com/...) - MCP Server 实现
- [Slay_The_Spire_2_AIBot](https://github.com/...) - 策略知识来源

## License

MIT
