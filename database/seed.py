import json
import logging
from pathlib import Path
from database.services.persistence_service import PersistenceService

logger = logging.getLogger("database_seed")


async def seed_data() -> None:
    """Reads regulations.json from the workspace root and seeds the requirements database table."""
    regs_path = Path(__file__).parent.parent / "regulations.json"
    if regs_path.exists():
        try:
            with open(regs_path, "r", encoding="utf-8") as f:
                regulations = json.load(f)
            await PersistenceService.seed_requirements(regulations)
            logger.info("Successfully seeded requirements corpus.")
        except Exception as e:
            logger.error(f"Error seeding database: {e}")
    else:
        logger.warning("regulations.json not found. Seeding skipped.")
