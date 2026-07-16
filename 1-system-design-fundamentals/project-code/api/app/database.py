from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import logging

from app.config import settings

engine = create_engine(
    settings.database_url,
    echo=True,
    pool_size=17,
    max_overflow=0,
    connect_args={
        "connect_timeout": 1,
        "options": "-c statement_timeout=500"
    }
)

# Send SQLAlchemy logs to stdout (Docker-friendly)
sql_logger = logging.getLogger("sqlalchemy.engine")
sql_logger.setLevel(logging.INFO)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)

# Avoid duplicate handlers on reloads
if not sql_logger.handlers:
    sql_logger.addHandler(stream_handler)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        try:
            db.close()
        except Exception as exc:
            from app.logging_config import logger
            logger.warning(f"Session close deferred or errored: {exc}")