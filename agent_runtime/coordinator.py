"""Execution Coordinator decoupling runtime orchestration from node execution."""

import logging
from typing import Dict, Any, List, Optional
from agent_runtime.state import AgentRuntimeState
from agent_runtime.engine import AgentRuntimeEngine

logger = logging.getLogger("agent_runtime.coordinator")


class ExecutionCoordinator:
    """Orchestrates node step dispatching, recovery loops, and step pipeline flow."""

    def __init__(self, engine: Optional[AgentRuntimeEngine] = None):
        self.engine = engine or AgentRuntimeEngine()

    async def run_pipeline(
        self,
        initial_state: AgentRuntimeState,
        nodes: List[Dict[str, Any]],
    ) -> AgentRuntimeState:
        """Runs a sequence of node step handlers through the runtime engine.

        nodes parameter format:
        [
            {
                "node_name": "planner",
                "agent_name": "supervisor",
                "func": async_node_func,
                "prompt_tokens": 300,
                "completion_tokens": 150
            },
            ...
        ]
        """
        current_state = initial_state

        for node in nodes:
            if current_state.is_completed or current_state.is_interrupted:
                logger.info(f"Pipeline stopped early for run {current_state.run_id}")
                break

            node_name = node["node_name"]
            agent_name = node.get("agent_name")
            func = node["func"]
            p_tokens = node.get("prompt_tokens", 400)
            c_tokens = node.get("completion_tokens", 200)

            current_state = await self.engine.execute_step(
                state=current_state,
                node_name=node_name,
                step_func=func,
                agent_name=agent_name,
                estimated_prompt_tokens=p_tokens,
                estimated_completion_tokens=c_tokens,
            )

        return current_state
