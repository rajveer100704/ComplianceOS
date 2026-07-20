from abc import ABC, abstractmethod

class ParserCapabilities:
    """Represents the feature capabilities of a parser engine."""
    def __init__(self, tables: bool = True, ocr: bool = True, layout: bool = True, images: bool = False, formulas: bool = False):
        self.tables = tables
        self.ocr = ocr
        self.layout = layout
        self.images = images
        self.formulas = formulas

    def to_dict(self) -> dict:
        return {
            "tables": self.tables,
            "ocr": self.ocr,
            "layout": self.layout,
            "images": self.images,
            "formulas": self.formulas
        }

class BaseParser(ABC):
    """Abstract Base Class for all document parsing engines."""
    
    @property
    @abstractmethod
    def capabilities(self) -> ParserCapabilities:
        """Returns the capabilities of the parser engine."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Returns the version of the parser engine."""
        pass

    @abstractmethod
    def parse(self, data: bytes, doc_name: str) -> tuple[str, dict]:
        """
        Parses document bytes and returns (text, metadata).
        """
        pass
