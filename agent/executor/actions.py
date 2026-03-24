"""动作执行器"""

from typing import Any

from agent.state.models import ActionResult, Decision
from mcp_client.client import MCPClient, MCPClientError
from utils.logger import get_logger


class ActionExecutor:
    """动作执行器"""

    def __init__(self, client: MCPClient | None = None):
        self.client = client or MCPClient()
        self.logger = get_logger()

    def execute(self, decision: Decision) -> ActionResult:
        """执行决策"""
        self.logger.log_decision(
            decision.action_name,
            decision.reason,
            decision.source,
            decision.confidence
        )

        # 低置信度警告
        if decision.confidence < 0.5:
            self.logger.warning(
                f"决策置信度较低: {decision.confidence:.2f}",
                action=decision.action_name
            )

        try:
            # 执行动作
            result = self.client.execute_action(
                decision.action_name,
                decision.params
            )

            # 解析结果
            success = result.get("success", False)
            message = result.get("message", "")

            if success:
                self.logger.log_action(decision.action_name, True, message)
                return ActionResult.success(message, result)
            else:
                self.logger.log_action(decision.action_name, False, message)
                # 判断是否可重试
                retryable = self._is_retryable_error(message)
                return ActionResult.failure(message, retryable)

        except MCPClientError as e:
            self.logger.error(f"执行动作失败: {decision.action_name}", error=str(e))
            return ActionResult.failure(str(e), retryable=True)

        except Exception as e:
            self.logger.error(f"执行动作时发生异常: {decision.action_name}", error=str(e))
            return ActionResult.failure(f"异常: {e}", retryable=False)

    def execute_with_retry(
        self,
        decision: Decision,
        max_retries: int = 2
    ) -> ActionResult:
        """带重试的执行"""
        for attempt in range(max_retries + 1):
            result = self.execute(decision)

            if result.ok:
                return result

            if not result.retryable or attempt >= max_retries:
                return result

            self.logger.warning(
                f"动作失败，准备重试 ({attempt + 1}/{max_retries + 1})",
                action=decision.action_name
            )

        return result

    def validate_and_execute(
        self,
        decision: Decision,
        current_state: dict[str, Any]
    ) -> ActionResult:
        """验证并执行动作"""
        # 基础验证
        validation_error = self._validate_decision(decision, current_state)
        if validation_error:
            self.logger.error(f"决策验证失败: {validation_error}")
            return ActionResult.failure(f"验证失败: {validation_error}", retryable=False)

        # 执行
        return self.execute(decision)

    def _validate_decision(
        self,
        decision: Decision,
        state: dict[str, Any]
    ) -> str | None:
        """验证决策合法性，返回错误信息或 None"""
        action = decision.action_name
        params = decision.params

        # 战斗动作验证
        if action == "play_card":
            card_idx = params.get("card_index")
            hand = state.get("battle", {}).get("hand", [])

            if card_idx is None:
                return "缺少 card_index 参数"
            if not isinstance(card_idx, int):
                return "card_index 必须是整数"
            if card_idx < 0 or card_idx >= len(hand):
                return f"card_index {card_idx} 超出手牌范围 [0, {len(hand)})"

        elif action == "select_card":
            card_idx = params.get("index")
            cards = state.get("rewards", {}).get("cards", [])

            if card_idx is None:
                return "缺少 index 参数"
            if not isinstance(card_idx, int):
                return "index 必须是整数"
            if card_idx < 0 or card_idx >= len(cards):
                return f"index {card_idx} 超出卡牌范围 [0, {len(cards)})"

        elif action == "select_node":
            node_id = params.get("node_id")
            if node_id is None:
                return "缺少 node_id 参数"

        # 其他动作暂时不验证
        return None

    def _is_retryable_error(self, message: str) -> bool:
        """判断错误是否可重试"""
        retryable_keywords = [
            "timeout",
            "connection",
            "network",
            "temporarily",
            "busy",
            "retry",
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in retryable_keywords)

    def refresh_state(self) -> dict[str, Any] | None:
        """刷新并返回最新状态"""
        try:
            return self.client.get_game_state()
        except MCPClientError as e:
            self.logger.error(f"刷新状态失败: {e}")
            return None
