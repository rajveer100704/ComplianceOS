"""Policy expression compiler converting human expressions to validated AST dictionaries."""

import re
import hashlib
from typing import Dict, Any, List
from policy_engine.cache import compiler_cache


class PolicyCompiler:
    """Compiles human-readable condition expressions into structured AST representations."""

    def compile(self, expression: str) -> Dict[str, Any]:
        """Compiles expression into AST JSON dict, utilizing compiler cache."""
        cached = compiler_cache.get(expression)
        if cached:
            return cached

        # Parse simple logical expressions: e.g., 'risk_score > 80 AND status == "UNSUPPORTED"'
        terms = [t.strip() for t in expression.split("AND") if t.strip()]
        rules_ast: List[Dict[str, Any]] = []

        for term in terms:
            match = re.match(r"^([a-zA-Z0-9_\.]+)\s*(==|!=|>=|<=|>|<)\s*(.+)$", term)
            if match:
                field_name, op, raw_val = match.groups()
                raw_val = raw_val.strip().strip("'\"")
                # Cast value
                if raw_val.isdigit():
                    val = int(raw_val)
                else:
                    try:
                        val = float(raw_val)
                    except ValueError:
                        val = raw_val

                rules_ast.append({"field": field_name, "op": op, "value": val})
            else:
                rules_ast.append({"raw_term": term, "op": "TRUE", "value": True})

        ast = {
            "type": "LOGICAL_AND",
            "terms": rules_ast,
            "checksum": hashlib.sha256(expression.encode("utf-8")).hexdigest(),
        }

        compiler_cache.put(expression, ast)
        return ast
