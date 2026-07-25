"""Compliance sign-off gate evaluator enforcing quantitative threshold guardrails."""

import logging
from typing import List, Dict, Any
from governance.schemas import (
    ComplianceRule,
    GateEvaluationResult,
    GateStatus,
    RuleOperator,
)

logger = logging.getLogger("governance.compliance_gates.evaluator")


class ComplianceGateEvaluator:
    """Evaluates context metrics against active organization compliance rules."""

    def __init__(self):
        self._rules: Dict[str, List[ComplianceRule]] = (
            {}
        )  # organization_id -> List[ComplianceRule]

    async def add_rule(self, rule: ComplianceRule) -> ComplianceRule:
        org_id = rule.organization_id
        if org_id not in self._rules:
            self._rules[org_id] = []
        self._rules[org_id].append(rule)
        logger.info(
            f"Added ComplianceRule '{rule.name}' for org '{org_id}' threshold={rule.threshold_value}"
        )
        return rule

    async def evaluate_gate(
        self,
        session_id: str,
        context_metrics: Dict[str, float],
        organization_id: str = "default",
    ) -> GateEvaluationResult:
        rules = self._rules.get(organization_id, [])
        violations: List[Dict[str, Any]] = []

        passed_count = 0
        failed_count = 0
        is_rejected = False

        for rule in rules:
            metric_val = context_metrics.get(rule.metric_name)
            if metric_val is None:
                continue

            rule_passed = True
            if (
                rule.operator == RuleOperator.GREATER_THAN_EQUAL
                and metric_val < rule.threshold_value
            ):
                rule_passed = False
            elif (
                rule.operator == RuleOperator.LESS_THAN_EQUAL
                and metric_val > rule.threshold_value
            ):
                rule_passed = False
            elif (
                rule.operator == RuleOperator.EQUALS
                and metric_val != rule.threshold_value
            ):
                rule_passed = False

            if rule_passed:
                passed_count += 1
            else:
                failed_count += 1
                violations.append(
                    {
                        "rule_id": rule.rule_id,
                        "rule_name": rule.name,
                        "metric_name": rule.metric_name,
                        "metric_value": metric_val,
                        "threshold": rule.threshold_value,
                        "is_blocking": rule.is_blocking,
                    }
                )
                if rule.is_blocking:
                    is_rejected = True

        status = GateStatus.REJECTED if is_rejected else GateStatus.PASSED
        res = GateEvaluationResult(
            session_id=session_id,
            status=status,
            organization_id=organization_id,
            evaluated_rules_count=len(rules),
            passed_rules_count=passed_count,
            failed_rules_count=failed_count,
            violations=violations,
        )
        logger.info(
            f"Evaluated gate for session '{session_id}': status={status.value} failed={failed_count}"
        )
        return res
