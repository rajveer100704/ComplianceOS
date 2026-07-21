from parsers.pymupdf_parser import PyMuPDFParser
from parsers.marker_parser import MarkerParser
from parsers.docling_parser import DoclingParser

# Central registry for resolving document parsing engines
PARSER_REGISTRY = {
    "pymupdf": PyMuPDFParser,
    "marker": MarkerParser,
    "docling": DoclingParser,
}
