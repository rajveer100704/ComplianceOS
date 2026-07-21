from parsers.base import BaseParser, ParserCapabilities


class DoclingParser(BaseParser):
    """Placeholder for Docling layout parser engine."""

    def __init__(self):
        try:
            # Check availability of docling conversion module on init
            import docling  # type: ignore
        except ImportError:
            raise ImportError(
                "Docling parsing engine is not installed in the current environment."
            )

    @property
    def capabilities(self) -> ParserCapabilities:
        return ParserCapabilities(
            tables=True, ocr=True, layout=True, images=True, formulas=True
        )

    @property
    def version(self) -> str:
        return "1.0.0"

    def parse(self, data: bytes, doc_name: str) -> tuple[str, dict]:
        return "Parsed via Docling", {
            "parser_engine": "docling",
            "parser_version": self.version,
            "engine_version": "1.0",
            "ocr_used": False,
            "tables_found": 0,
            "layout": "docling_layout",
            "capabilities": self.capabilities.to_dict(),
        }
