"""STS2 AI Agent 主入口"""

import argparse
import signal
import sys
import time
import traceback
from pathlib import Path

from agent.decision.engine import DecisionEngine
from agent.executor.actions import ActionExecutor
from agent.state.manager import StateManager
from agent.state.models import GameState
from mcp_client.client import MCPClient, MCPConnectionError
from utils.config import get_config
from utils.logger import get_logger


class AgentShutdown(Exception):
    """Agent 关闭信号"""
    pass


class STS2Agent:
    """STS2 AI Agent 主类"""

    def __init__(self, config_path: str | None = None):
        """初始化 Agent"""
        self.logger = get_logger()
        self.logger.info("=" * 50)
        self.logger.info("STS2 AI Agent 启动中...")
        self.logger.info("=" * 50)

        # 加载配置
        if config_path:
            get_config(config_path)
            self.logger.info(f"加载配置: {config_path}")

        self.config = get_config()

        # 初始化组件
        self.client = MCPClient()
        self.state_manager = StateManager()
        self.decision_engine = DecisionEngine()
        self.executor = ActionExecutor(self.client)

        # 运行状态
        self.running = False
        self.step_count = 0
        self.consecutive_errors = 0
        self.max_consecutive_errors = 5

        # 注册信号处理
        self._setup_signal_handlers()

        self.logger.info("Agent 初始化完成")

    def _setup_signal_handlers(self) -> None:
        """设置信号处理器"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame) -> None:
        """信号处理器"""
        self.logger.info(f"收到信号 {signum}，准备关闭...")
        self.running = False

    def run(self) -> None:
        """主循环"""
        self.logger.info("启动主循环...")
        self.running = True

        # 等待连接
        if not self.client.wait_for_connection(timeout=30):
            self.logger.error("无法连接到游戏，退出")
            return

        try:
            while self.running:
                self._step()
                time.sleep(self.config.poll_interval_ms / 1000)

        except AgentShutdown:
            self.logger.info("Agent 正常关闭")
        except Exception as e:
            self.logger.error(f"主循环异常: {e}")
            self.logger.error(traceback.format_exc())
        finally:
            self._cleanup()

    def _step(self) -> None:
        """执行一步"""
        self.step_count += 1

        try:
            # 1. 获取状态
            raw_state = self.client.get_game_state()
            if not raw_state:
                self.logger.warning("获取到空状态")
                return

            # 2. 解析状态
            game_state = self.state_manager.parse_state(raw_state)

            # 3. 状态分发（获取上下文）
            context = self.state_manager.handle_state(game_state)

            # 4. 生成决策
            decision = self.decision_engine.decide(game_state, context)

            # 如果返回 None，说明当前不需要执行动作（如敌人回合）
            if decision is None:
                self.logger.debug("当前无需执行动作，等待中...")
                return

            # 5. 执行动作
            result = self.executor.validate_and_execute(decision, raw_state)

            # 6. 记录步骤
            self.logger.log_step(
                self.step_count,
                game_state.state_type,
                str(decision),
                "success" if result.ok else f"failed: {result.message}"
            )

            # 7. 重置错误计数
            if result.ok:
                self.consecutive_errors = 0
            else:
                self.consecutive_errors += 1

            # 8. 检查连续错误
            if self.consecutive_errors >= self.max_consecutive_errors:
                self.logger.error(f"连续错误次数过多 ({self.consecutive_errors})，暂停运行")
                self.running = False

        except MCPConnectionError as e:
            self.logger.error(f"连接错误: {e}")
            self.consecutive_errors += 1
            if self.consecutive_errors >= self.max_consecutive_errors:
                self.logger.error("连接错误过多，退出")
                self.running = False

        except Exception as e:
            self.logger.error(f"步骤执行异常: {e}")
            self.logger.error(traceback.format_exc())
            self.consecutive_errors += 1

    def _cleanup(self) -> None:
        """清理资源"""
        self.logger.info("=" * 50)
        self.logger.info(f"Agent 停止，共执行 {self.step_count} 步")
        self.logger.info("=" * 50)

    def stop(self) -> None:
        """停止 Agent"""
        self.running = False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="STS2 AI Agent")
    parser.add_argument(
        "-c", "--config",
        default="config/example.yaml",
        help="配置文件路径"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="启用详细日志"
    )

    args = parser.parse_args()

    # 检查配置文件
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"错误: 配置文件不存在: {args.config}")
        print("使用默认配置启动...")
        config_path = None

    # 创建并运行 Agent
    agent = STS2Agent(str(config_path) if config_path else None)

    try:
        agent.run()
    except KeyboardInterrupt:
        print("\n用户中断")
        agent.stop()
    finally:
        sys.exit(0)


if __name__ == "__main__":
    main()
