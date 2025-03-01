import asyncio
import logging
import os
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from sqlalchemy import log as sql_log
from sqlalchemy import update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from config_reader import config
from db.models import Player

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
sql_log._add_default_handler = lambda x: None


async def run():
    logger.info("Initializing database connection")
    logger.info(f"URL: {config.db_url.unicode_string()}")
    engine = create_async_engine(
        url=config.db_url.unicode_string(),
        echo=True,
        pool_size=5,
        max_overflow=5,
        pool_timeout=5,
    )

    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    async with sessionmaker() as session:
        logger.info("Open session")
        query = (
            update(Player)
            .filter(Player.card_battle_rating.is_(None))
            .values(card_battle_rating=0)
        )
        await session.execute(query)
        await session.commit()


if __name__ == "__main__":
    file_name = __file__.split("\\")[-1]
    logger.info(f"Starting {file_name} script")
    asyncio.run(run())
    logger.info("Script completed")
