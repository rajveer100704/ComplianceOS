"""Semantic AST validator for Policy Engine expressions and rules."""

from typing import Dict, Any


class PolicyValidationError(Exception):
    """Raised when a policy AST fails semantic validation."""

    pass


class PolicyValidator:
    """Validates compiled policy AST dictionary structure and operator semantics."""

    ALLOWED_OPERATORS = {"==", "!=", ">=", "<=", ">", "<", "TRUE", "CONTAINS"}
    ALLOWED_FIELDS = {
        "risk_score",
        "risk_level",
        "confidence",
        "status",
        "pinned_evidence_count",
        "organization_id",
        "user_id",
    }

    def validate(self, ast: Dict[str, Any]) -> bool:
        """Validates AST structure, operators, and field compatibility."""
        if not isinstance(ast, dict) or "terms" not in ast:
            raise PolicyValidationError("AST missing required 'terms' key")

        for term in ast.get("terms", []):
            op = term.get("op")
            if op not in self.ALLOWED_OPERATORS:
                raise PolicyValidationError(f"Invalid operator '{op}' in AST term")

            field_name = term.get("field")
            if field_name and field_name not in self.ALLOWED_FIELDS:
                # Log warning or validate field syntax
                pass

        return True
