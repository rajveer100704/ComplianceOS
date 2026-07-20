class QueryPlanner:
    """Dynamically plans retrieval parameters and thresholds based on policy configurations."""

    def __init__(self, engine: str, strategy: str, policy: str):
        self.engine = engine
        self.strategy = strategy
        self.policy = policy

    def get_plan(self, query: str) -> dict:
        # Determine thresholds based on policy
        thresholds = {"support": 0.35, "partial": 0.15}
        if self.policy == "strict":
            thresholds = {"support": 0.50, "partial": 0.30}
        elif self.policy == "recall":
            thresholds = {"support": 0.20, "partial": 0.10}

        return {
            "engine": self.engine,
            "strategy": self.strategy,
            "policy": self.policy,
            "thresholds": thresholds
        }
