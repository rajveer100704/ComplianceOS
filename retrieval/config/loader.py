import yaml
from pathlib import Path
from retrieval.config.validator import ConfigValidator


class ConfigLoader:
    """Loads configuration yaml file and executes schema validations."""

    @staticmethod
    def load() -> dict:
        config_path = Path(__file__).parent.parent.parent / "config" / "app.yaml"
        config = {}
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f) or {}
            except Exception:
                pass

        # Enforce validation checks on load
        ConfigValidator.validate(config)
        return config
