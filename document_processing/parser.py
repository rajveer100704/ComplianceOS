"""Layout-aware document parser registry & normalization interface."""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from document_processing.schemas import DocumentElement, ElementType

logger = logging.getLogger("document_processing.parser")


class BaseDocumentParser(ABC):
    """Abstract base class for layout document parsers."""

    name: str

    @abstractmethod
    async def parse(
        self, file_path: str, text_content: Optional[str] = None
    ) -> List[DocumentElement]:
        """Parses a document file into a list of normalized DocumentElements."""
        pass


class SimpleTextParser(BaseDocumentParser):
    """Fallback text parser converting raw text into normalized paragraph and heading elements."""

    name = "simple_text"

    async def parse(
        self, file_path: str, text_content: Optional[str] = None
    ) -> List[DocumentElement]:
        elements = []
        raw_text = text_content or ""

        if not raw_text and file_path:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    raw_text = f.read()
            except Exception as err:
                logger.warning(f"Error reading file {file_path}: {err}")

        lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
        element_id_counter = 1

        for idx, line in enumerate(lines):
            is_heading = (
                line.startswith("#")
                or line.isupper()
                or (len(line) < 60 and line.endswith(":"))
                or (
                    len(line) < 50
                    and any(
                        line.startswith(prefix)
                        for prefix in (
                            "Section",
                            "Clause",
                            "Part",
                            "1.",
                            "2.",
                            "3.",
                            "4.",
                        )
                    )
                )
            )
            elem_type = ElementType.HEADING if is_heading else ElementType.PARAGRAPH

            elements.append(
                DocumentElement(
                    id=f"elem-{element_id_counter}",
                    type=elem_type,
                    page=1,
                    text=line,
                    reading_order=element_id_counter,
                )
            )
            element_id_counter += 1

        return elements


class ParserRegistry:
    """Registry maintaining active document parser implementations."""

    def __init__(self):
        self._parsers: Dict[str, BaseDocumentParser] = {}
        self._default_parser: Optional[BaseDocumentParser] = None

    def register(self, parser: BaseDocumentParser, default: bool = False) -> None:
        self._parsers[parser.name] = parser
        if default or not self._default_parser:
            self._default_parser = parser
        logger.info(f"Document parser '{parser.name}' registered")

    def get(self, name: Optional[str] = None) -> BaseDocumentParser:
        if name and name in self._parsers:
            return self._parsers[name]
        if self._default_parser:
            return self._default_parser
        return SimpleTextParser()


parser_registry = ParserRegistry()
parser_registry.register(SimpleTextParser(), default=True)
