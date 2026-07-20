import yaml
import logging
from pathlib import Path
from parsers.base import BaseParser
from parsers.registry import PARSER_REGISTRY
from parsers.pymupdf_parser import PyMuPDFParser

logger = logging.getLogger("parser_factory")

class ParserFactory:
    """Factory for resolving and instantiating document parser engines based on config."""

    @staticmethod
    def load_config() -> dict:
        config_path = Path(__file__).parent.parent / "config" / "app.yaml"
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"Failed to load app.yaml configuration: {e}")
        return {}

    @staticmethod
    def get_parser(engine_name: str = None, allow_fallback: bool = None) -> BaseParser:
        config = ParserFactory.load_config()
        parser_config = config.get("parser", {})
        
        selected_engine = engine_name or parser_config.get("engine", "pymupdf")
        fallback_flag = allow_fallback if allow_fallback is not None else parser_config.get("allow_fallback", True)
        
        if selected_engine not in PARSER_REGISTRY:
            raise ValueError(f"Unknown parser engine: {selected_engine}")
            
        parser_cls = PARSER_REGISTRY[selected_engine]
        
        try:
            return parser_cls()
        except ImportError as e:
            if fallback_flag:
                logger.warning(f"Failed to initialize parser '{selected_engine}', falling back to 'pymupdf': {e}")
                # We also want to record the fallback warning on whatever parser we return, or let the caller know.
                # Returning PyMuPDFParser is the fallback behavior.
                return PyMuPDFParser()
            else:
                raise e
