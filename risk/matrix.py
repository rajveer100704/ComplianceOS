"""5x5 Safety Engineering Likelihood x Impact Risk Matrix Evaluator."""

import logging
from risk.schemas import RiskMatrix, RiskLevel

logger = logging.getLogger("risk.matrix")

# Likelihood & Impact numeric mapping (1 to 5)
LIKELIHOOD_MAP = {"very low": 1, "low": 2, "medium": 3, "high": 4, "critical": 5}
IMPACT_MAP = {"minor": 1, "moderate": 2, "major": 3, "severe": 4, "catastrophic": 5}


class RiskMatrixEvaluator:
    """Evaluates 5x5 Likelihood x Impact safety matrix coordinates."""

    def evaluate(self, likelihood: str, impact: str) -> RiskMatrix:
        l_val = LIKELIHOOD_MAP.get(likelihood.lower(), 2)
        i_val = IMPACT_MAP.get(impact.lower(), 2)

        matrix_product = l_val * i_val

        if matrix_product >= 20:
            zone = RiskLevel.CRITICAL
        elif matrix_product >= 12:
            zone = RiskLevel.RED
        elif matrix_product >= 8:
            zone = RiskLevel.ORANGE
        elif matrix_product >= 4:
            zone = RiskLevel.YELLOW
        else:
            zone = RiskLevel.GREEN

        score = round((matrix_product / 25.0) * 100.0, 1)

        return RiskMatrix(
            likelihood=likelihood.title(),
            impact=impact.title(),
            zone=zone,
            score=score,
        )
