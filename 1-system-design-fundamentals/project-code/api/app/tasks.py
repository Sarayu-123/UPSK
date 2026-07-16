from datetime import (
    datetime,
    timedelta
)

import redis

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.celery_app import celery_app
from app.models import ClickEvent
from app.logging_config import logger
from app.config import settings
from celery.exceptions import MaxRetriesExceededError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# =====================================================
# DEDICATED DATABASE ENGINE & SESSION FOR WORKERS
# =====================================================
tasks_engine = create_engine(
    settings.database_url,
    echo=True,
    pool_size=3,
    max_overflow=0,
    connect_args={
        "connect_timeout": 1,
        "options": "-c statement_timeout=500"
    }
)

TasksSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=tasks_engine
)


# =====================================================
# DEDICATED REDIS CLIENT FOR CELERY WORKERS
# =====================================================

redis_client = redis.from_url(
    settings.redis_url,
    decode_responses=True
)


@celery_app.task(bind=True)
def record_click_task(
    self,
    click_id: str,
    link_id: int,
    ip_address: str,
    user_agent: str | None = None,
    referrer: str | None = None
):
    db: Session = TasksSessionLocal()

    try:
        # =================================================
        # ANALYTICS DEDUPLICATION
        # =================================================

        dedup_key = (
            f"analytics:dedup:{click_id}"
        )

        if redis_client.get(dedup_key):
            logger.info(
                f"Duplicate analytics job ignored: {click_id}"
            )
            return

        # =================================================
        # ATOMIC UPSERT FOR CLICK DEDUPLICATION
        # =================================================

        stmt = insert(ClickEvent).values(
            link_id=link_id,
            ip_hash=click_id,
            user_agent=user_agent,
            referrer=referrer
        ).on_conflict_do_nothing(
            index_elements=["ip_hash"]
        )

        result = db.execute(stmt)

        db.commit()

        # =================================================
        # SET DEDUP FLAG ONLY AFTER COMMIT
        # =================================================

        redis_client.set(
            dedup_key,
            "1",
            ex=86400
        )

        if result.rowcount > 0:
            logger.info(
                f"Analytics click recorded: {click_id}"
            )
        else:
            logger.info(
                f"Duplicate click ignored: {click_id}"
            )

    except IntegrityError:
        db.rollback()

        logger.warning(
            f"Duplicate click prevented: {click_id}"
        )

    except Exception as exc:
        db.rollback()

        logger.error(
            f"Analytics task failed: {exc}"
        )

        try:
            # Calculate exponential backoff countdown: 1s, 2s, 4s, 8s, 16s...
            countdown = 2 ** self.request.retries
            raise self.retry(exc=exc, countdown=countdown, max_retries=5)
        except MaxRetriesExceededError:
            logger.error(
                f"Max retries exceeded for click_id={click_id}. Moving to dead-letter queue."
            )
            dead_letter_payload = {
                "click_id": click_id,
                "link_id": link_id,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "referrer": referrer,
                "failed_at": datetime.utcnow().isoformat(),
                "error": str(exc)
            }
            import json
            redis_client.lpush("analytics:dead_letter", json.dumps(dead_letter_payload))
            raise exc

    finally:
        db.close()


@celery_app.task
def purge_old_clicks():
    db: Session = TasksSessionLocal()

    try:
        cutoff_date = (
            datetime.utcnow()
            - timedelta(days=settings.retention_days)
        )

        batch_size = 1000

        total_deleted = 0

        while True:
            old_clicks = (
                db.query(ClickEvent)
                .filter(
                    ClickEvent.clicked_at < cutoff_date
                )
                .limit(batch_size)
                .all()
            )

            if not old_clicks:
                break

            deleted_count = len(old_clicks)

            for click in old_clicks:
                db.delete(click)

            db.commit()

            total_deleted += deleted_count

            logger.info(
                f"Purged batch: {deleted_count}"
            )

        logger.info(
            f"Total purged clicks: {total_deleted}"
        )

    except Exception as exc:
        db.rollback()

        logger.error(
            f"Purge task failed: {exc}"
        )

        raise

    finally:
        db.close()