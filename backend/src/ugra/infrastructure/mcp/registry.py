"""MCP server registry — plug-and-play MCP integration."""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ugra.core.logging.setup import get_logger

logger = get_logger(__name__)


@dataclass
class MCPServerConfig:
    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)


class MCPClient(ABC):
    @abstractmethod
    async def connect(self) -> None: ...

    @abstractmethod
    async def disconnect(self) -> None: ...

    @abstractmethod
    async def list_tools(self) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any: ...


class MCPRegistry:
    """Register and manage MCP servers without modifying core architecture."""

    def __init__(self) -> None:
        self._configs: dict[str, MCPServerConfig] = {}
        self._clients: dict[str, MCPClient] = {}

    def register_config(self, config: MCPServerConfig) -> None:
        self._configs[config.name] = config
        logger.info("mcp_server_registered", name=config.name)

    def register_client(self, name: str, client: MCPClient) -> None:
        self._clients[name] = client

    def load_from_json(self, json_config: str) -> None:
        configs = json.loads(json_config)
        for item in configs:
            self.register_config(MCPServerConfig(**item))

    @property
    def available_servers(self) -> list[str]:
        return list(self._configs.keys())

    async def get_tools(self, server_name: str) -> list[dict[str, Any]]:
        client = self._clients.get(server_name)
        if not client:
            return []
        return await client.list_tools()

    async def call_tool(
        self, server_name: str, tool_name: str, arguments: dict[str, Any]
    ) -> Any:
        client = self._clients.get(server_name)
        if not client:
            msg = f"MCP server '{server_name}' not connected"
            raise ValueError(msg)
        return await client.call_tool(tool_name, arguments)
