"""Agent and Tool registry for dynamic capability lookup and execution."""

import logging
from typing import Dict, List, Optional
from agent_runtime.interfaces import BaseAgent, BaseTool

logger = logging.getLogger("agent_runtime.registry")


class AgentRegistry:
    """Registry maintaining active agents and capability mapping."""

    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        """Registers an agent instance."""
        if agent.name in self._agents:
            logger.warning(f"Overwriting existing registered agent '{agent.name}'")
        self._agents[agent.name] = agent
        logger.info(f"Agent '{agent.name}' successfully registered")

    def get(self, name: str) -> Optional[BaseAgent]:
        """Retrieves a registered agent by name."""
        return self._agents.get(name)

    def list_agents(self) -> List[str]:
        """Lists names of all registered agents."""
        return list(self._agents.keys())


class ToolRegistry:
    """Registry maintaining active tools available to reasoning agents."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Registers a tool instance."""
        if tool.name in self._tools:
            logger.warning(f"Overwriting existing registered tool '{tool.name}'")
        self._tools[tool.name] = tool
        logger.info(f"Tool '{tool.name}' successfully registered")

    def get(self, name: str) -> Optional[BaseTool]:
        """Retrieves a registered tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """Lists names of all registered tools."""
        return list(self._tools.keys())


# Global singleton instances
agent_registry = AgentRegistry()
tool_registry = ToolRegistry()
