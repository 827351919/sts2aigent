"""决策引擎"""

from typing import Any

from agent.state.models import Decision, GameState
from utils.logger import get_logger


class DecisionEngine:
    """启发式决策引擎"""

    def __init__(self):
        self.logger = get_logger()

    def decide(self, state: GameState, context: dict[str, Any] | None = None) -> Decision:
        """根据状态生成决策"""
        context = context or {}

        if state.is_combat:
            return self._combat_decision(state, context)
        elif state.state_type == "combat_rewards":
            return self._reward_decision(state, context)
        elif state.state_type == "card_reward":
            return self._card_reward_decision(state, context)
        elif state.is_map:
            return self._map_decision(state, context)
        else:
            return self._fallback_decision(state, context)

    def _combat_decision(self, state: GameState, context: dict[str, Any]) -> Decision:
        """战斗决策：能打就打，不能打就结束回合

        STS2MCP 动作格式:
        - play_card: {"action": "play_card", "card_index": int, "target": str}
          target 是 entity_id (如 "jaw_worm_0")
        - end_turn: {"action": "end_turn"}
        """
        # 从扁平结构读取（StateManager._combat_handler 返回扁平结构）
        ctx = context or state.battle or {}
        hand = ctx.get("hand", [])
        energy = ctx.get("energy", 0)
        enemies = ctx.get("enemies", [])

        # 过滤可打的牌（费用 <= 当前能量 且 can_play 为 True）
        playable_cards = [
            (i, card) for i, card in enumerate(hand)
            if card.get("can_play", False) and int(card.get("cost", 99)) <= energy
        ]

        if playable_cards:
            # 选择第一张可打的牌
            card_idx, card = playable_cards[0]
            card_name = card.get("name", f"card_{card_idx}")

            # 确定目标（默认第一个活着的敌人的 entity_id）
            target = None
            for enemy in enemies:
                if enemy.get("hp", 0) > 0:
                    target = enemy.get("entity_id")
                    break

            params = {"card_index": card_idx}
            if target and card.get("target_type") == "AnyEnemy":
                params["target"] = target

            return Decision(
                action_name="play_card",
                params=params,
                reason=f"打出手牌[{card_name}]，费用{card.get('cost')} <= 能量{energy}",
                source="heuristic",
                confidence=0.8
            )
        else:
            # 没有可打的牌，结束回合
            return Decision(
                action_name="end_turn",
                params={},
                reason="没有可打的手牌或能量不足，结束回合",
                source="heuristic",
                confidence=1.0
            )

    def _reward_decision(self, state: GameState, context: dict[str, Any]) -> Decision:
        """战斗奖励决策：拿第一个奖励"""
        # 根据 STS2MCP 协议，使用 claim_reward(index) 拿取奖励
        items = context.get("items", []) if context else []
        if not items:
            # 尝试从 state.rewards 获取
            rewards = state.rewards or {}
            items = rewards.get("items", [])

        if items:
            # 拿取第一个奖励
            first_item = items[0]
            item_type = first_item.get("type", "unknown")
            return Decision(
                action_name="claim_reward",
                params={"index": 0},
                reason=f"拿取第一个奖励[{item_type}]: {first_item.get('description', '')}",
                source="heuristic",
                confidence=0.7
            )

        # 检查是否可以 proceed
        can_proceed = context.get("can_proceed", False)
        if can_proceed:
            return Decision(
                action_name="proceed",
                params={},
                reason="奖励已领取完毕，继续前进",
                source="heuristic",
                confidence=1.0
            )

        # 没有奖励，等待
        return Decision(
            action_name="wait",
            params={},
            reason="没有可拿的奖励",
            source="fallback",
            confidence=0.3
        )

    def _card_reward_decision(self, state: GameState, context: dict[str, Any]) -> Decision:
        """卡牌奖励决策：选第一张或跳过"""
        cards = context.get("cards", []) if context else []

        if cards:
            card_name = cards[0].get("name", f"card_0")
            return Decision(
                action_name="select_card_reward",
                params={"index": 0},
                reason=f"选择第一张卡牌[{card_name}]",
                source="heuristic",
                confidence=0.5
            )
        else:
            return Decision(
                action_name="skip_card_reward",
                params={},
                reason="没有卡牌可选，跳过",
                source="heuristic",
                confidence=1.0
            )

    def _map_decision(self, state: GameState, context: dict[str, Any]) -> Decision:
        """地图决策：选第一个可用节点

        STS2MCP 动作: choose_map_node(index)
        index 是 next_options 数组中的索引
        """
        next_options = context.get("next_options", [])

        if next_options:
            node = next_options[0]
            node_type = node.get("type", "unknown")
            node_coord = (node.get("col", 0), node.get("row", 0))

            return Decision(
                action_name="choose_map_node",
                params={"index": 0},  # index 对应 next_options 中的位置
                reason=f"选择第一个可用节点[{node_type}] at {node_coord}",
                source="heuristic",
                confidence=0.6
            )
        else:
            return Decision(
                action_name="wait",
                params={},
                reason="没有可用节点",
                source="fallback",
                confidence=0.3
            )

    def _fallback_decision(self, state: GameState, context: dict[str, Any]) -> Decision:
        """兜底决策"""
        self.logger.warning(
            f"状态 {state.state_type} 没有专用决策逻辑，使用兜底策略"
        )

        return Decision(
            action_name="wait",
            params={},
            reason=f"未知状态[{state.state_type}]，等待人工介入",
            source="fallback",
            confidence=0.1
        )
