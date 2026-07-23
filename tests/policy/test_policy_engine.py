"""Unit tests for Policy Compiler, AST Cache, Validator, Context, and Evaluator."""

from policy_engine.compiler import PolicyCompiler
from policy_engine.validator import PolicyValidator
from policy_engine.context import PolicyContext
from policy_engine.evaluator import PolicyEvaluator
from policy_engine.cache import compiler_cache


def test_compiler_and_cache():
    compiler = PolicyCompiler()
    expr = "risk_score > 80 AND status == UNSUPPORTED"

    ast1 = compiler.compile(expr)
    assert ast1["type"] == "LOGICAL_AND"
    assert len(ast1["terms"]) == 2

    # Check cache hit
    ast2 = compiler.compile(expr)
    assert ast1 == ast2
    assert compiler_cache.get(expr) is not None


def test_validator():
    validator = PolicyValidator()
    compiler = PolicyCompiler()
    expr = "risk_score >= 50"
    ast = compiler.compile(expr)
    assert validator.validate(ast) is True


def test_evaluator_passed():
    compiler = PolicyCompiler()
    evaluator = PolicyEvaluator()

    expr = "risk_score > 50"
    ast = compiler.compile(expr)

    ctx = PolicyContext(
        organization_id="org-1",
        claim={"risk_score": 90, "status": "UNSUPPORTED"},
    )

    decision = evaluator.evaluate("pol-1", "ver-1", ast, ctx)
    assert decision.allowed is True
    assert decision.policy_id == "pol-1"
    assert decision.policy_version_id == "ver-1"
    assert len(decision.matched_rules) == 1
    assert decision.trace.traces[0].status == "PASSED"


def test_evaluator_failed():
    compiler = PolicyCompiler()
    evaluator = PolicyEvaluator()

    expr = "risk_score < 50"
    ast = compiler.compile(expr)

    ctx = PolicyContext(
        organization_id="org-1",
        claim={"risk_score": 90, "status": "UNSUPPORTED"},
    )

    decision = evaluator.evaluate("pol-1", "ver-1", ast, ctx)
    assert decision.allowed is False
    assert len(decision.blocked_rules) == 1
    assert decision.trace.traces[0].status == "FAILED"
