"""WorkflowExecutor running DAG topology action pipelines with step latency and retry tracking."""

import time
import logging
from typing import List, Dict, Any
from workflow.context import WorkflowContext
from workflow.registry import action_registry
from workflow.retry import calculate_delay_seconds

logger = logging.getLogger("workflow_executor")


class WorkflowExecutionResult:
    """Result summary emitted by WorkflowExecutor."""

    def __init__(self, workflow_id: str, success: bool, dry_run: bool):
        self.workflow_id = workflow_id
        self.success = success
        self.dry_run = dry_run
        self.step_results: List[Dict[str, Any]] = []


class WorkflowExecutor:
    """Executes DAG action topologies, managing retries, step latency, and dry-run modes."""

    async def execute_dag(
        self,
        workflow_id: str,
        steps: List[str],
        context: WorkflowContext,
    ) -> WorkflowExecutionResult:
        """Executes workflow steps in sequence or DAG topology, capturing results."""
        result = WorkflowExecutionResult(
            workflow_id=workflow_id, success=True, dry_run=context.dry_run
        )

        for step_key in steps:
            action = action_registry.get(step_key)
            if not action:
                logger.warning(f"Workflow action key '{step_key}' not found in ActionRegistry")
                result.step_results.append(
                    {
                        "action_key": step_key,
                        "status": "SKIPPED",
                        "reason": "Unregistered action key",
                    }
                )
                continue

            start = time.perf_counter()
            step_success = False
            step_output = {}

            # Execute with retry attempts
            for attempt in range(1, 4):
                try:
                    if context.dry_run:
                        step_output = await action.simulate(context)
                    else:
                        step_output = await action.execute(context)

                    step_success = True
                    break
                except Exception as e:
                    logger.error(
                        f"Action '{step_key}' failed attempt {attempt}: {e}"
                    )
                    delay = calculate_delay_seconds(action.retry_policy, attempt)
                    if delay > 0:
                        import asyncio

                        await asyncio.sleep(delay)

            latency_ms = (time.perf_counter() - start) * 1000.0

            result.step_results.append(
                {
                    "action_key": step_key,
                    "status": "COMPLETED" if step_success else "FAILED",
                    "latency_ms": round(latency_ms, 2),
                    "output": step_output,
                }
            )

            if not step_success:
                result.success = False
                logger.error(f"Workflow '{workflow_id}' halted on failed step '{step_key}'")
                break

        return result
