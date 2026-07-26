"""Benchmark Suite & Evaluation Engine package for v2.0 AI Platform."""

from evaluation.schemas import (
    BenchmarkTestCase,
    EvaluationRun,
    RegressionReport,
)
from evaluation.metrics.evaluators import MetricEvaluator
from evaluation.runners.runner import PlatformRunner
from evaluation.telemetry.prof import RegressionReporter
from evaluation.manager import EvaluationManager

__all__ = [
    "BenchmarkTestCase",
    "EvaluationRun",
    "RegressionReport",
    "MetricEvaluator",
    "PlatformRunner",
    "RegressionReporter",
    "EvaluationManager",
]
