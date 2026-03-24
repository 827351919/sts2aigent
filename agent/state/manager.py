"""状态机管理器"""

from typing import Any, Callable

from agent.state.models import GameState
from utils.logger import get_logger

# 处理器类型别名
StateHandler = Callable[[GameState], Any]


class StateManager:
    """游戏状态管理器"""

    def __init__(self):
        self.logger = get_logger()
        self._handlers: dict[str, StateHandler] = {}
        self._safe_handler: StateHandler | None = None
        self._step_counter = 0

        # 注册默认处理器
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """注册默认处理器"""
        # 战斗状态
        self.register_handler("monster", self._combat_handler)
        self.register_handler("elite", self._combat_handler)
        self.register_handler("boss", self._combat_handler)

        # 奖励状态
        self.register_handler("combat_rewards", self._reward_handler)
        self.register_handler("card_reward", self._card_reward_handler)

        # 地图状态
        self.register_handler("map", self._map_handler)

        # 其他状态（安全处理）
        self.register_handler("event", self._safe_state_handler)
        self.register_handler("rest_site", self._safe_state_handler)
        self.register_handler("shop", self._safe_state_handler)
        self.register_handler("treasure", self._safe_state_handler)
        self.register_handler("card_select", self._safe_state_handler)
        self.register_handler("relic_select", self._safe_state_handler)
        self.register_handler("hand_select", self._safe_state_handler)
        self.register_handler("grid_select", self._safe_state_handler)

        # 设置安全处理器
        self.set_safe_handler(self._unknown_state_handler)

    def register_handler(self, state_type: str, handler: StateHandler) -> None:
        """注册状态处理器"""
        self._handlers[state_type] = handler
        self.logger.debug(f"注册处理器: {state_type}")

    def set_safe_handler(self, handler: StateHandler) -> None:
        """设置安全处理器（用于未知状态）"""
        self._safe_handler = handler

    def parse_state(self, raw_state: dict[str, Any]) -> GameState:
        """解析原始状态为 GameState"""
        self._step_counter += 1

        # 提取状态类型
        state_type = raw_state.get("state_type", "unknown")
        if not state_type or state_type == "unknown":
            # 尝试从其他字段推断
            if "battle" in raw_state:
                state_type = "monster"
            elif "rewards" in raw_state:
                state_type = "combat_rewards"
            elif "map" in raw_state:
                state_type = "map"
            elif "event" in raw_state:
                state_type = "event"

        game_state = GameState(
            state_type=state_type,
            raw=raw_state,
            step_id=self._step_counter
        )

        self.logger.log_state(state_type, game_state.get_summary())
        return game_state

    def handle_state(self, state: GameState) -> Any:
        """分发状态到对应处理器"""
        handler = self._handlers.get(state.state_type)

        if handler:
            self.logger.debug(f"使用处理器: {state.state_type}")
            return handler(state)
        elif self._safe_handler:
            self.logger.warning(f"未知状态类型: {state.state_type}，使用安全处理器")
            return self._safe_handler(state)
        else:
            self.logger.error(f"未知状态类型且无安全处理器: {state.state_type}")
            raise ValueError(f"无法处理状态类型: {state.state_type}")

    def get_handler_for(self, state_type: str) -> StateHandler | None:
        """获取指定状态的处理器"""
        return self._handlers.get(state_type)

    # ============ 默认处理器实现 ============

    def _combat_handler(self, state: GameState) -> dict[str, Any]:
        """战斗状态处理器 - 返回决策所需信息"""
        battle = state.battle or {}
        player = state.player or {}

        return {
            "state_type": state.state_type,
            "player_hp": player.get("hp", 0),
            "player_max_hp": player.get("max_hp", 0),
            "energy": battle.get("energy", 0),
            "max_energy": battle.get("max_energy", 3),
            "hand": battle.get("hand", []),
            "enemies": battle.get("enemies", []),
            "turn": battle.get("turn", 1),
            "can_end_turn": True,
        }

    def _reward_handler(self, state: GameState) -> dict[str, Any]:
        """战斗奖励处理器"""
        rewards = state.rewards or {}

        return {
            "state_type": state.state_type,
            "gold": rewards.get("gold", 0),
            "relics": rewards.get("relics", []),
            "potions": rewards.get("potions", []),
            "cards": rewards.get("cards", []),
            "can_skip": True,
        }

    def _card_reward_handler(self, state: GameState) -> dict[str, Any]:
        """卡牌奖励处理器"""
        rewards = state.rewards or {}

        return {
            "state_type": state.state_type,
            "cards": rewards.get("cards", []),
            "can_skip": True,
        }

    def _map_handler(self, state: GameState) -> dict[str, Any]:
        """地图状态处理器"""
        map_data = state.map or {}

        return {
            "state_type": state.state_type,
            "current_node": map_data.get("current_node"),
            "available_nodes": map_data.get("available_nodes", []),
            "boss_known": map_data.get("boss_known", False),
        }

    def _safe_state_handler(self, state: GameState) -> dict[str, Any]:
        """安全状态处理器 - 用于已知但暂不处理的状态"""
        self.logger.warning(
            f"状态 {state.state_type} 使用安全处理",
            suggestion="需要实现专用处理器"
        )
        return {
            "state_type": state.state_type,
            "safe_mode": True,
            "raw_keys": list(state.raw.keys()),
        }

    def _unknown_state_handler(self, state: GameState) -> dict[str, Any]:
        """未知状态处理器"""
        self.logger.error(
            f"遇到未知状态: {state.state_type}",
            raw_keys=list(state.raw.keys())
        )
        return {
            "state_type": state.state_type,
            "unknown": True,
            "raw_keys": list(state.raw.keys()),
        }
