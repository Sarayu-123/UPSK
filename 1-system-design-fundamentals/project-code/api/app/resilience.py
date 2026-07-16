import asyncio
import random
import pybreaker
import sqlalchemy.exc
from typing import Callable, Any
from app.logging_config import logger

class BreakerLogger(pybreaker.CircuitBreakerListener):
    def state_change(self, cb, old_state, new_state):
        if new_state.name == "open":
            logger.error("circuit_opened", dependency="database")
        elif new_state.name in ("half-open", "half_open"):
            logger.info("circuit_half_open", dependency="database")
        elif new_state.name == "closed":
            logger.info("circuit_closed", dependency="database")


db_breaker = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=30,
    listeners=[BreakerLogger()]
)

async def retry_with_backoff(
    fn: Callable[[], Any],
    max_retries: int = 3,
    base_delay: float = 0.1,    # 100ms
    max_delay: float = 2.0,     # 2 seconds
    jitter: float = 0.05,       # +/- 50ms
    retryable_exceptions: tuple = (
        ConnectionError, OSError, sqlalchemy.exc.OperationalError
    )
) -> Any:
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            return await fn()
        except retryable_exceptions as e:
            last_error = e

            if attempt == max_retries:
                break

            # Exponential backoff with jitter
            exponential_delay = min(base_delay * (2 ** attempt), max_delay)
            jitter_offset = random.uniform(-jitter, jitter)
            delay = max(0, exponential_delay + jitter_offset)

            logger.warning("retry_attempt",
                dependency="database",
                attempt=attempt + 1,
                max_retries=max_retries,
                delay_ms=round(delay * 1000),
                error_type=type(e).__name__,
                error_message=str(e)
            )

            await asyncio.sleep(delay)
        except Exception as e:
            # Non-retryable error -- fail immediately
            raise e

    raise last_error

from sqlalchemy.orm import Session

async def safe_db_call(
    func: Callable,
    *args,
    timeout: float = 1.0,
    max_retries: int = 3,
    **kwargs
) -> Any:
    """
    Execute a database operation protected by:
    - Circuit breaker
    - Timeout
    - Exponential backoff + jitter
    - Rollback on failure
    """
    # ---------------------------------
    # Find Session object
    # ---------------------------------
    db = kwargs.get("db")
    if db is None:
        for arg in args:
            if hasattr(arg, "rollback"):
                db = arg
                break

    async def call_with_rollback():
        try:
            return await asyncio.to_thread(
                func,
                *args,
                **kwargs
            )
        except Exception as e:
            if db is not None:
                try:
                    db.rollback()
                except Exception as rollback_exc:
                    logger.warning(
                        "rollback_failed",
                        dependency="database",
                        error=str(rollback_exc)
                    )
            raise e

    try:
        # ---------------------------------
        # Circuit breaker gate check
        # ---------------------------------
        state = db_breaker.state
        if state.name == 'open':
            from datetime import datetime, timedelta
            timeout_delta = timedelta(seconds=db_breaker.reset_timeout)
            opened_at = db_breaker._state_storage.opened_at
            if opened_at and datetime.utcnow() < opened_at + timeout_delta:
                raise pybreaker.CircuitBreakerError("Timeout not elapsed yet, circuit breaker still open")
            db_breaker.half_open()

        # ---------------------------------
        # Entire logical transaction (including retries)
        # ---------------------------------
        result = await retry_with_backoff(
            call_with_rollback,
            max_retries=max_retries,
            retryable_exceptions=(ConnectionError, OSError, sqlalchemy.exc.OperationalError)
        )

        # ---------------------------------
        # Logical success
        # ---------------------------------
        db_breaker.state._handle_success()
        return result

    except pybreaker.CircuitBreakerError:
        logger.warning(
            "circuit_open_fallback",
            dependency="database"
        )
        raise

    except (
        asyncio.TimeoutError,
        sqlalchemy.exc.SQLAlchemyError,
        ConnectionError,
        OSError,
    ) as exc:
        # ---------------------------------
        # Count ONE logical failure
        # ---------------------------------
        logger.error(
            "dependency_failure",
            dependency="database",
            error=str(exc)
        )
        db_breaker.state._handle_error(exc)
