import asyncio
import logging

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from db.queries.scheduled_queries import new_season

DB_URL = "postgresql+asyncpg://fint_user:fint_user@localhost:5000/fint_dbr"


async def season_reset():
    engine = create_async_engine(
        url=DB_URL, echo=False, pool_size=5, max_overflow=5, pool_timeout=5
    )

    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    await new_season(sessionmaker)
    logging.info("SEASON RESETED")


if __name__ == "__main__":
    try:
        asyncio.run(season_reset())
    except (KeyboardInterrupt, SystemExit):
        logging.error("season reset stopped!")
