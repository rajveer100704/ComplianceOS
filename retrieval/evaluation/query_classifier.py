import re

class QueryClassifier:
    """Heuristically classifies queries into easy, medium, or hard difficulty classes."""

    @staticmethod
    def classify(query: str) -> str:
        """Classifies a query based on token count, boolean operators, punctuation, quotes, and section references."""
        query_stripped = query.strip()
        if not query_stripped:
            return "easy"

        # 1. Feature extraction
        words = query_stripped.split()
        word_count = len(words)

        has_quotes = '"' in query_stripped or "'" in query_stripped
        
        boolean_pattern = r"\b(AND|OR|NOT)\b"
        has_boolean = bool(re.search(boolean_pattern, query_stripped, re.IGNORECASE))
        
        punctuation_count = sum(1 for char in query_stripped if char in "?.,:;-()")
        
        sec_pattern = r"\b(section|sec|part|chapter|clause|article|§)\b"
        has_sec_ref = bool(re.search(sec_pattern, query_stripped, re.IGNORECASE))

        # 2. Heuristic Scoring
        score = 0
        if word_count > 12:
            score += 3
        elif word_count > 6:
            score += 1

        if has_quotes:
            score += 2
        if has_boolean:
            score += 2
        if punctuation_count >= 2:
            score += 1
        if has_sec_ref:
            score += 2

        # 3. Class assignments
        if score >= 5:
            return "hard"
        elif score >= 2:
            return "medium"
        else:
            return "easy"
