"""日志系统"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any

from utils.config import get_config


class AgentLogger:
    """Agent 日志管理器"""

    _instance: "AgentLogger | None" = None

    def __new__(cls) -> "AgentLogger":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._logger = logging.getLogger("sts2_agent")
        self._logger.setLevel(logging.DEBUG)
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """设置日志处理器"""
        config = get_config()
        log_level = getattr(logging, config.log_level.upper(), logging.INFO)

        # 清除现有处理器
        self._logger.handlers.clear()

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_format = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S"
        )
        console_handler.setFormatter(console_format)
        self._logger.addHandler(console_handler)

        # 文件处理器
        log_file = config.log_file
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=config.get("logging.max_size_mb", 100) * 1024 * 1024,
                backupCount=config.get("logging.backup_count", 5),
                encoding="utf-8"
            )
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter(
                config.get(
                    "logging.format",
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
            file_handler.setFormatter(file_format)
            self._logger.addHandler(file_handler)

    def debug(self, msg: str, **kwargs: Any) -> None:
        """记录 DEBUG 级别日志"""
        self._log(logging.DEBUG, msg, **kwargs)

    def info(self, msg: str, **kwargs: Any) -> None:
        """记录 INFO 级别日志"""
        self._log(logging.INFO, msg, **kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:
        """记录 WARNING 级别日志"""
        self._log(logging.WARNING, msg, **kwargs)

    def error(self, msg: str, **kwargs: Any) -> None:
        """记录 ERROR 级别日志"""
        self._log(logging.ERROR, msg, **kwargs)

    def _log(self, level: int, msg: str, **kwargs: Any) -> None:
        """内部日志记录方法"""
        if kwargs:
            # 构建结构化日志消息
            extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())
            msg = f"{msg} | {extra_info}"
        self._logger.log(level, msg)

    def log_step(self, step_id: int, state_type: str, decision: str, result: str) -> None:
        """记录决策步骤"""
        self.info(
            f"Step {step_id}",
            state_type=state_type,
            decision=decision,
            result=result
        )

    def log_state(self, state_type: str, raw_summary: str) -> None:
        """记录状态信息"""
        self.debug(f"State: {state_type}", raw=raw_summary)

    def log_decision(self, action: str, reason: str, source: str, confidence: float) -> None:
        """记录决策信息"""
        self.info(
            f"Decision: {action}",
            reason=reason,
            source=source,
            confidence=f"{confidence:.2f}"
        )

    def log_action(self, action: str, success: bool, message: str = "") -> None:
        """记录动作执行结果"""
        if success:
            self.info(f"Action success: {action}", message=message)
        else:
            self.error(f"Action failed: {action}", message=message)


# 便捷函数
def get_logger() -> AgentLogger:
    """获取日志实例"""
    return AgentLogger()
