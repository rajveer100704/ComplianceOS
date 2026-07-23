"""PolicyEvaluator executing AST conditions against PolicyContext and generating explainable PolicyDecision."""

import time
from typing import Dict, Any, List
from policy_engine.context import PolicyContext
from policy_engine.decision import PolicyDecision, EvaluationTrace, RuleTrace


class PolicyEvaluator:
    """Evaluates compiled policy AST expressions against a PolicyContext."""

    def evaluate(
        self,
        policy_id: str,
        policy_version_id: str,
        ast: Dict[str, Any],
        context: PolicyContext,
    ) -> PolicyDecision:
        """Executes AST evaluation and returns a PolicyDecision with EvaluationTrace."""
        start_time = time.perf_counter()
        ctx_dict = context.to_dict()

        matched_rules: List[str] = []
        blocked_rules: List[str] = []
        traces: List[RuleTrace] = []

        is_allowed = True

        for idx, term in enumerate(ast.get("terms", [])):
            rule_id = f"term_{idx}"
            field_name = term.get("field")
            op = term.get("op")
            val = term.get("value")

            if op == "TRUE":
                traces.append(
                    RuleTrace(
                        rule_id=rule_id,
                        rule_name=f"Term {idx}",
                        status="PASSED",
                        reason="Always true term",
                    )
                )
                matched_rules.append(rule_id)
                continue

            ctx_val = ctx_dict.get(field_name)
            term_passed = self._eval_term(ctx_val, op, val)

            if term_passed:
                matched_rules.append(rule_id)
                traces.append(
                    RuleTrace(
                        rule_id=rule_id,
                        rule_name=f"{field_name} {op} {val}",
                        status="PASSED",
                        reason=f"Actual context value '{ctx_val}' satisfied condition",
                    )
                )
            else:
                is_allowed = False
                blocked_rules.append(rule_id)
                traces.append(
                    RuleTrace(
                        rule_id=rule_id,
                        rule_name=f"{field_name} {op} {val}",
                        status="FAILED",
                        reason=f"Actual context value '{ctx_val}' failed condition",
                    )
                )

        eval_latency_ms = (time.perf_counter() - start_time) * 1000.0

        trace = EvaluationTrace(
            traces=traces, evaluation_time_ms=round(eval_latency_ms, 2)
        )

        return PolicyDecision(
            allowed=is_allowed,
            policy_id=policy_id,
            policy_version_id=policy_version_id,
            matched_rules=matched_rules,
            blocked_rules=blocked_rules,
            warnings=(
                [] if is_allowed else ["Policy evaluation condition blocked action"]
            ),
            actions=[],
            audit_entries=[
                {
                    "event": "policy.evaluated",
                    "policy_id": policy_id,
                    "version_id": policy_version_id,
                    "allowed": is_allowed,
                }
            ],
            trace=trace,
        )

    def _eval_term(self, ctx_val: Any, op: str, target_val: Any) -> bool:
        if ctx_val is None:
            return False
        try:
            if op == "==":
                return ctx_val == target_val
            elif op == "!=":
                return ctx_val != target_val
            elif op == ">":
                return float(ctx_val) > float(target_val)
            elif op == "<":
                return float(ctx_val) < float(target_val)
            elif op == ">=":
                return float(ctx_val) >= float(target_val)
            elif op == "<=":
                return float(ctx_val) <= float(target_val)
            elif op == "CONTAINS":
                return str(target_val).lower() in str(ctx_val).lower()
        except (ValueError, TypeError):
            return False
        return False
