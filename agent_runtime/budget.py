"""Token budget manager and cost tracking for agent runtime executions."""

import logging

logger = logging.getLogger("agent_runtime.budget")

# Standard token rates per 1,000 tokens (USD)
MODEL_RATES = {
    "gemini-2.0-flash": {"input": 0.0001, "output": 0.0004},
    "gemini-1.5-pro": {"input": 0.00125, "output": 0.0050},
    "gpt-4o": {"input": 0.0025, "output": 0.0100},
    "claude-3-5-sonnet": {"input": 0.0030, "output": 0.0150},
    "default": {"input": 0.0010, "output": 0.0030},
}


class BudgetExceededError(Exception):
    """Raised when an agent execution exceeds token budget or cost limit."""

    pass


class TokenBudgetManager:
    """Tracks token consumption and estimated cost against allocated budgets."""

    def __init__(
        self,
        max_budget_usd: float = 5.0,
        max_tokens: int = 100_000,
        model_name: str = "gemini-2.0-flash",
    ):
        self.max_budget_usd = max_budget_usd
        self.max_tokens = max_tokens
        self.model_name = model_name
        self.tokens_used: int = 0
        self.accumulated_cost_usd: float = 0.0

    def calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculates cost in USD for a given token count based on model rates."""
        rates = MODEL_RATES.get(self.model_name, MODEL_RATES["default"])
        cost = (prompt_tokens / 1000.0) * rates["input"] + (
            completion_tokens / 1000.0
        ) * rates["output"]
        return round(cost, 6)

    def record_usage(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Records token usage, updates cost, and enforces budget limits."""
        total_new_tokens = prompt_tokens + completion_tokens
        cost = self.calculate_cost(prompt_tokens, completion_tokens)

        if self.tokens_used + total_new_tokens > self.max_tokens:
            raise BudgetExceededError(
                f"Token limit exceeded: {self.tokens_used + total_new_tokens} > {self.max_tokens}"
            )

        if self.accumulated_cost_usd + cost > self.max_budget_usd:
            raise BudgetExceededError(
                f"Cost limit exceeded: ${self.accumulated_cost_usd + cost:.4f} > ${self.max_budget_usd:.4f}"
            )

        self.tokens_used += total_new_tokens
        self.accumulated_cost_usd += cost
        logger.debug(
            f"Usage recorded: {total_new_tokens} tokens (${cost:.6f}). Total: {self.tokens_used} tokens (${self.accumulated_cost_usd:.4f})"
        )
        return self.accumulated_cost_usd
