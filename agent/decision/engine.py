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
        """战斗决策：能打就打，不能打就结束回合"""
        battle = context or state.battle or {}
        hand = battle.get("hand", [])
        energy = battle.get("energy", 0)
        enemies = battle.get("enemies", [])

        # 过滤可打的牌（费用 <= 当前能量）
        playable_cards = [
            (i, card) for i, card in enumerate(hand)
            if card.get("cost", 99) <= energy
        ]

        if playable_cards:
            # 选择第一张可打的牌
            card_idx, card = playable_cards[0]
            card_name = card.get("name", f"card_{card_idx}")

            # 确定目标（默认第一个活着的敌人）
            target_idx = 0
            for i, enemy in enumerate(enemies):
                if enemy.get("hp", 0) > 0:
                    target_idx = i
                    break

            return Decision(
                action_name="play_card",
                params={"card_index": card_idx, "target_index": target_idx},
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
        rewards = context or state.rewards or {}

        # 优先拿遗物
        relics = rewards.get("relics", [])
        if relics:
            return Decision(
                action_name="take_relic",
                params={"index": 0},
                reason="拿取第一个遗物",
                source="heuristic",
                confidence=0.7
            )

        # 其次拿药水
        potions = rewards.get("potions", [])
        if potions:
            return Decision(
                action_name="take_potion",
                params={"index": 0},
                reason="拿取第一个药水",
                source="heuristic",
                confidence=0.7
            )

        # 最后拿金币
        gold = rewards.get("gold", 0)
        if gold > 0:
            return Decision(
                action_name="take_gold",
                params={},
                reason=f"拿取{gold}金币",
                source="heuristic",
                confidence=0.9
            )

        # 没有奖励，跳过
        return Decision(
            action_name="skip",
            params={},
            reason="没有可拿的奖励",
            source="heuristic",
            confidence=1.0
        )

    def _card_reward_decision(self, state: GameState, context: dict[str, Any]) -> Decision:
        """卡牌奖励决策：选第一张或跳过"""
        cards = context.get("cards", []) if context else []
        if not cards and state.rewards:
            cards = state.rewards.get("cards", [])

        if cards:
            card_name = cards[0].get("name", f"card_0")
            return Decision(
                action_name="select_card",
                params={"index": 0},
                reason=f"选择第一张卡牌[{card_name}]",
                source="heuristic",
                confidence=0.5
            )
        else:
            return Decision(
                action_name="skip",
                params={},
                reason="没有卡牌可选",
                source="heuristic",
                confidence=1.0
            )

    def _map_decision(self, state: GameState, context: dict[str, Any]) -> Decision:
        """地图决策：选第一个可用节点"""
        available = context.get("available_nodes", [])
        if not available and state.map:
            available = state.map.get("available_nodes", [])

        if available:
            node = available[0]
            node_id = node.get("id", 0) if isinstance(node, dict) else node
            node_type = node.get("type", "unknown") if isinstance(node, dict) else "unknown"

            return Decision(
                action_name="select_node",
                params={"node_id": node_id},
                reason=f"选择第一个可用节点[{node_type}]",
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
