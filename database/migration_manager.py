from pathlib import Path
from alembic.config import Config
from alembic import command


class MigrationManager:
    """Helper class to inspect or apply Alembic migrations programmatically."""

    @staticmethod
    def get_alembic_config() -> Config:
        ini_path = Path(__file__).parent.parent / "alembic.ini"
        config = Config(str(ini_path))
        # Setup migrations folder path options dynamically
        config.set_main_option(
            "script_location", str(Path(__file__).parent / "migrations")
        )
        return config

    @classmethod
    def upgrade_to_head(cls) -> None:
        """Upgrades the database schema to the latest migration revision."""
        cfg = cls.get_alembic_config()
        command.upgrade(cfg, "head")

    @classmethod
    def downgrade_to_base(cls) -> None:
        """Downgrades the schema back to baseline status."""
        cfg = cls.get_alembic_config()
        command.downgrade(cfg, "base")

    @classmethod
    def show_current(cls) -> None:
        """Prints current active schema version revision status."""
        cfg = cls.get_alembic_config()
        command.current(cfg)
