"""状态模型定义"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class GameState:
    """游戏状态模型"""

    state_type: str
    raw: dict[str, Any]
    player: dict[str, Any] | None = None
    battle: dict[str, Any] | None = None
    map: dict[str, Any] | None = None
    event: dict[str, Any] | None = None
    shop: dict[str, Any] | None = None
    rewards: dict[str, Any] | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    step_id: int = 0

    def __post_init__(self) -> None:
        """初始化后处理"""
        # 从 raw 中提取常用字段
        if not self.player and "player" in self.raw:
            self.player = self.raw["player"]
        if not self.battle and "battle" in self.raw:
            self.battle = self.raw["battle"]
        if not self.map and "map" in self.raw:
            self.map = self.raw["map"]
        if not self.event and "event" in self.raw:
            self.event = self.raw["event"]
        if not self.shop and "shop" in self.raw:
            self.shop = self.raw["shop"]
        if not self.rewards and "rewards" in self.raw:
            self.rewards = self.raw["rewards"]

    @property
    def is_combat(self) -> bool:
        """是否是战斗状态"""
        return self.state_type in ("monster", "elite", "boss")

    @property
    def is_reward(self) -> bool:
        """是否是奖励状态"""
        return self.state_type in ("combat_rewards", "card_reward")

    @property
    def is_map(self) -> bool:
        """是否是地图状态"""
        return self.state_type == "map"

    def get_summary(self) -> str:
        """获取状态摘要"""
        if self.is_combat and self.battle:
            enemies = self.battle.get("enemies", [])
            hp = self.player.get("hp", "?") if self.player else "?"
            return f"combat vs {len(enemies)} enemies, hp={hp}"
        elif self.is_reward:
            reward_type = self.state_type
            return f"reward: {reward_type}"
        elif self.is_map:
            return "map navigation"
        return f"state: {self.state_type}"


@dataclass
class Decision:
    """决策模型"""

    action_name: str
    params: dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    source: str = "heuristic"  # heuristic | knowledge | llm | fallback
    confidence: float = 1.0

    def __str__(self) -> str:
        return f"{self.action_name}({self.params}) source={self.source}"


@dataclass
class ActionResult:
    """动作执行结果模型"""

    ok: bool
    message: str = ""
    raw_response: dict[str, Any] | str | None = None
    retryable: bool = False

    @classmethod
    def success(cls, message: str = "", raw: dict[str, Any] | str | None = None) -> "ActionResult":
        """创建成功结果"""
        return cls(ok=True, message=message, raw_response=raw, retryable=False)

    @classmethod
    def failure(cls, message: str, retryable: bool = False) -> "ActionResult":
        """创建失败结果"""
        return cls(ok=False, message=message, raw_response=None, retryable=retryable)
