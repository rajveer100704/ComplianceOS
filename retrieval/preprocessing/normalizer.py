import unicodedata

class TextNormalizer:
    """Standardizes unicode characters across all documents."""
    
    @staticmethod
    def normalize(text: str) -> str:
        return unicodedata.normalize('NFKC', text)
