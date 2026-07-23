"""Agent Runtime Engine managing step execution, token budgets, interrupts, and checkpoints."""

import time
import uuid
import logging
from typing import Optional, Callable, Awaitable
from datetime import datetime, UTC

from agent_runtime.interfaces import BaseCheckpointStore, BaseEventBus
from agent_runtime.state import AgentRuntimeState, ExecutionStep
from agent_runtime.budget import TokenBudgetManager, BudgetExceededError
from agent_runtime.checkpoint import InMemoryCheckpointStore
from agent_runtime.events import agent_event_bus

logger = logging.getLogger("agent_runtime.engine")


class AgentRuntimeEngine:
    """Operating system engine coordinating agent step execution, checkpoints, budget, and events."""

    def __init__(
        self,
        checkpoint_store: Optional[BaseCheckpointStore] = None,
        event_bus: Optional[BaseEventBus] = None,
    ):
        self.checkpoint_store = checkpoint_store or InMemoryCheckpointStore()
        self.event_bus = event_bus or agent_event_bus

    async def execute_step(
        self,
        state: AgentRuntimeState,
        node_name: str,
        step_func: Callable[[AgentRuntimeState], Awaitable[AgentRuntimeState]],
        agent_name: Optional[str] = None,
        estimated_prompt_tokens: int = 500,
        estimated_completion_tokens: int = 200,
    ) -> AgentRuntimeState:
        """Executes a single node step within budget limits, logging latency and broadcasting events."""

        if state.is_completed:
            logger.warning(f"State for run {state.run_id} is already completed")
            return state

        if state.is_interrupted:
            logger.warning(
                f"Run {state.run_id} is interrupted ({state.interrupt_reason})"
            )
            return state

        if state.current_step_count >= state.max_steps:
            state.is_completed = True
            state.error = f"Max step count ({state.max_steps}) reached"
            return state

        # Budget check
        budget_mgr = TokenBudgetManager(
            max_budget_usd=state.budget_limit_usd,
            model_name=state.metadata.get("model_name", "gemini-2.0-flash"),
        )
        # Restore current state cost
        budget_mgr.tokens_used = state.tokens_used
        budget_mgr.accumulated_cost_usd = state.estimated_cost_usd

        try:
            budget_mgr.record_usage(
                estimated_prompt_tokens, estimated_completion_tokens
            )
        except BudgetExceededError as err:
            logger.error(f"Budget error in run {state.run_id}: {err}")
            state.is_interrupted = True
            state.interrupt_reason = str(err)
            state.error = str(err)
            return state

        # Create step record
        step_id = str(uuid.uuid4())
        step_record = ExecutionStep(
            step_id=step_id,
            node_name=node_name,
            agent_name=agent_name,
            started_at=datetime.now(UTC),
            status="RUNNING",
            input_state={"current_node": state.current_node},
        )

        state.current_node = node_name
        state.current_step_count += 1
        state.tokens_used = budget_mgr.tokens_used
        state.estimated_cost_usd = budget_mgr.accumulated_cost_usd

        start_time = time.perf_counter()

        await self.event_bus.publish(
            f"run:{state.run_id}",
            {
                "event_type": "step_started",
                "step_id": step_id,
                "node_name": node_name,
                "agent_name": agent_name,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

        try:
            # Execute node function
            new_state = await step_func(state)
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

            step_record.finished_at = datetime.now(UTC)
            step_record.latency_ms = latency_ms
            step_record.status = "COMPLETED"
            step_record.output_state = {"current_node": new_state.current_node}

            new_state.steps.append(step_record)

            # Checkpoint save
            chk_id = await self.checkpoint_store.save_checkpoint(
                new_state.run_id, new_state
            )
            new_state.checkpoint_id = chk_id

            await self.event_bus.publish(
                f"run:{new_state.run_id}",
                {
                    "event_type": "step_completed",
                    "step_id": step_id,
                    "node_name": node_name,
                    "latency_ms": latency_ms,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
            return new_state

        except Exception as e:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            step_record.finished_at = datetime.now(UTC)
            step_record.latency_ms = latency_ms
            step_record.status = "FAILED"
            step_record.error_message = str(e)

            state.steps.append(step_record)
            state.error = str(e)
            state.is_completed = True

            logger.error(f"Step '{node_name}' failed in run {state.run_id}: {e}")
            await self.event_bus.publish(
                f"run:{state.run_id}",
                {
                    "event_type": "step_failed",
                    "step_id": step_id,
                    "node_name": node_name,
                    "error": str(e),
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
            return state
