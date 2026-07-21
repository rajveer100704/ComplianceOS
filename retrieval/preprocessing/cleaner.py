import re


class TextCleaner:
    """Removes duplicate lines, excessive spaces, and formatting artifacts."""

    @staticmethod
    def clean(text: str) -> str:
        # Standardize whitespace and multiple linebreaks
        cleaned = re.sub(r"[ \t]+", " ", text)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

        # Strip header/footer noise patterns like page number footprints
        cleaned = re.sub(r"\nPage \d+ of \d+\n", "\n", cleaned)
        cleaned = re.sub(r"\nPage \d+\n", "\n", cleaned)
        return cleaned.strip()
