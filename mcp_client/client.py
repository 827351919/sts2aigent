"""MCP HTTP 客户端"""

import json
import time
from typing import Any

import requests

from utils.config import get_config
from utils.logger import get_logger


class MCPClientError(Exception):
    """MCP 客户端错误"""
    pass


class MCPConnectionError(MCPClientError):
    """连接错误"""
    pass


class MCPTimeoutError(MCPClientError):
    """超时错误"""
    pass


class MCPClient:
    """MCP HTTP 客户端"""

    def __init__(self, host: str | None = None, port: int | None = None):
        config = get_config()
        self.host = host or config.mcp_host
        self.port = port or config.mcp_port
        self.timeout = config.mcp_timeout
        self.max_retries = config.mcp_reconnect_attempts
        self.base_url = f"http://{self.host}:{self.port}"
        self.logger = get_logger()

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        retry_count: int = 0
    ) -> dict[str, Any]:
        """发送 HTTP 请求"""
        url = f"{self.base_url}{endpoint}"

        try:
            if method == "GET":
                response = requests.get(url, timeout=self.timeout)
            elif method == "POST":
                response = requests.post(
                    url,
                    json=data,
                    headers={"Content-Type": "application/json"},
                    timeout=self.timeout
                )
            else:
                raise MCPClientError(f"不支持的 HTTP 方法: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.ConnectionError as e:
            if retry_count < self.max_retries:
                self.logger.warning(
                    f"连接失败，{retry_count + 1}/{self.max_retries} 重试...",
                    error=str(e)
                )
                time.sleep(1)
                return self._make_request(method, endpoint, data, retry_count + 1)
            raise MCPConnectionError(f"无法连接到 MCP Server: {e}")

        except requests.exceptions.Timeout as e:
            if retry_count < self.max_retries:
                self.logger.warning(
                    f"请求超时，{retry_count + 1}/{self.max_retries} 重试...",
                    error=str(e)
                )
                time.sleep(1)
                return self._make_request(method, endpoint, data, retry_count + 1)
            raise MCPTimeoutError(f"请求超时: {e}")

        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP 错误: {e}", status=response.status_code)
            raise MCPClientError(f"HTTP 错误 {response.status_code}: {e}")

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON 解析错误: {e}")
            raise MCPClientError(f"响应解析失败: {e}")

    def get_game_state(self) -> dict[str, Any]:
        """获取游戏状态"""
        self.logger.debug("获取游戏状态...")
        try:
            # 尝试获取单人游戏状态
            result = self._make_request("GET", "/api/v1/singleplayer/state")
            self.logger.debug("成功获取游戏状态")
            return result
        except MCPConnectionError:
            self.logger.error("无法连接到游戏，请确保 STS2MCP 已启动")
            raise

    def execute_action(self, action_name: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """执行动作"""
        params = params or {}
        self.logger.debug(f"执行动作: {action_name}", params=params)

        payload = {
            "action": action_name,
            "params": params
        }

        try:
            result = self._make_request("POST", "/api/v1/singleplayer/action", payload)
            self.logger.debug(f"动作执行成功: {action_name}")
            return result
        except MCPClientError as e:
            self.logger.error(f"动作执行失败: {action_name}", error=str(e))
            raise

    def ping(self) -> bool:
        """测试连接"""
        try:
            self._make_request("GET", "/api/v1/health", retry_count=0)
            return True
        except Exception:
            return False

    def wait_for_connection(self, timeout: int = 30) -> bool:
        """等待连接建立"""
        self.logger.info(f"等待连接到 {self.base_url}...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            if self.ping():
                self.logger.info("成功连接到 MCP Server")
                return True
            time.sleep(1)

        self.logger.error(f"连接超时 ({timeout}s)")
        return False
