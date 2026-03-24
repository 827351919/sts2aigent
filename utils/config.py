"""配置加载模块"""

import os
from pathlib import Path
from typing import Any

import yaml


class Config:
    """配置管理器"""

    def __init__(self, config_path: str | None = None):
        self._config: dict[str, Any] = {}
        self._load_defaults()
        if config_path:
            self.load_from_file(config_path)

    def _load_defaults(self) -> None:
        """加载默认配置"""
        self._config = {
            "mcp": {
                "host": "localhost",
                "port": 15526,
                "timeout": 10,
                "reconnect_attempts": 3,
            },
            "agent": {
                "mode": "full_auto",
                "poll_interval_ms": 500,
                "decision_timeout": 30,
                "enable_knowledge": False,
                "log_decisions": True,
                "max_decision_history": 100,
            },
            "logging": {
                "level": "INFO",
                "file": "logs/agent.log",
                "max_size_mb": 100,
                "backup_count": 5,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        }

    def load_from_file(self, path: str) -> None:
        """从 YAML 文件加载配置"""
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {path}")

        with open(config_path, "r", encoding="utf-8") as f:
            user_config = yaml.safe_load(f) or {}

        # 递归合并配置
        self._merge_config(self._config, user_config)

        # 处理环境变量替换
        self._resolve_env_vars(self._config)

    def _merge_config(self, base: dict, override: dict) -> None:
        """递归合并配置字典"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def _resolve_env_vars(self, config: dict) -> None:
        """解析配置中的环境变量"""
        for key, value in config.items():
            if isinstance(value, dict):
                self._resolve_env_vars(value)
            elif isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                default_value = None
                if ":" in env_var:
                    env_var, default_value = env_var.split(":", 1)
                config[key] = os.getenv(env_var, default_value)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项，支持点号分隔的路径"""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """设置配置项"""
        keys = key.split(".")
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    @property
    def mcp_host(self) -> str:
        return self.get("mcp.host", "localhost")

    @property
    def mcp_port(self) -> int:
        return self.get("mcp.port", 15526)

    @property
    def mcp_timeout(self) -> int:
        return self.get("mcp.timeout", 10)

    @property
    def mcp_reconnect_attempts(self) -> int:
        return self.get("mcp.reconnect_attempts", 3)

    @property
    def poll_interval_ms(self) -> int:
        return self.get("agent.poll_interval_ms", 500)

    @property
    def log_level(self) -> str:
        return self.get("logging.level", "INFO")

    @property
    def log_file(self) -> str:
        return self.get("logging.file", "logs/agent.log")


# 全局配置实例
_config_instance: Config | None = None


def get_config(config_path: str | None = None) -> Config:
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None or config_path:
        _config_instance = Config(config_path)
    return _config_instance
