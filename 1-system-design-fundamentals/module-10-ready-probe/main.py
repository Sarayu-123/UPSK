from contextlib import asynccontextmanager
import os
import tracemalloc
import time
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from app.config import settings
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.logging_config import logger
from app.database import engine
from prometheus_client import (
    generate_latest,
    CONTENT_TYPE_LATEST
)
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Link
from app.metrics import urls_total
from fastapi import Response
# =====================================================
# CACHE IMPORTS
# =====================================================

import app.cache as cache

from app.cache import (
    init_redis,
    close_redis
)

from app.middleware import request_context_middleware

from app.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler
)

from app.limiter import limiter

from app.routers.auth import router as auth_router
from app.routers.links import router as links_router
from app.routers.teams import router as teams_router
from app.routers.websocket import router as websocket_router
from app.routers.comments import router as comments_router
from app.routers.audit import router as audit_router
from app.routers.invitations import router as invitations_router



# =====================================================
# APP LIFESPAN
# =====================================================

from app.utils.event_bus import event_bus
from app.services.audit_subscriber import (
    handle_comment_created,
    handle_comment_updated,
    handle_comment_deleted,
)

@asynccontextmanager
async def lifespan(app: FastAPI):

    await init_redis()
    try:
        with Session(engine) as db:
            total_links = (
                db.query(
                    func.count(Link.id)
                ).scalar()
                or 0
            )
            urls_total.set(total_links)
    except Exception as e:
        logger.warning(
            "failed_to_populate_initial_metrics_on_startup",
            error=str(e)
        )

    logger.info(
        {
            "event": "application_startup",
            "environment": settings.app_env,
            "port": settings.port,
            "log_level": settings.log_level
        }
    )
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_links_search_vector
                ON links
                USING gin (
                    to_tsvector(
                        'english',
                        coalesce(code, '')
                        || ' '
                        || replace(
                            replace(
                                replace(
                                    coalesce(long_url, ''),
                                    '/',
                                    ' '
                                ),
                                '_',
                                ' '
                            ),
                            '-',
                            ' '
                        )
                    )
                );
            """))
            conn.commit()
        logger.info("search_index_ready")
    except Exception as e:
        logger.warning(
            "failed_to_create_search_index_on_startup",
            error=str(e)
        )

    # Register event subscribers before accepting traffic
    event_bus.subscribe(
        "comment.created",
        handle_comment_created,
    )

    event_bus.subscribe(
        "comment.updated",
        handle_comment_updated,
    )

    event_bus.subscribe(
        "comment.deleted",
        handle_comment_deleted,
    )

    yield

    await close_redis()

# =====================================================
# MEMORY PROFILING (DEVELOPMENT ONLY)
# =====================================================

start_time = time.time()

if settings.app_env.value == "development":
    tracemalloc.start()

# =====================================================
# FASTAPI APP
# =====================================================

app = FastAPI(
    title="Link Shortener & Analytics API",
    description=(
        "A production-grade link shortener "
        "and analytics service built with FastAPI."
    ),
    version="1.0.0",
    lifespan=lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# =====================================================
# RATE LIMITER
# =====================================================

app.state.limiter = limiter

app.add_middleware(
    SlowAPIMiddleware
)

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)


# =====================================================
# MIDDLEWARE
# =====================================================

app.middleware("http")(
    request_context_middleware
)


# =====================================================
# EXCEPTION HANDLERS
# =====================================================

app.add_exception_handler(
    HTTPException,
    http_exception_handler
)

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler
)

app.add_exception_handler(
    Exception,
    generic_exception_handler
)


# =====================================================
# AUTH ROUTER
# =====================================================

app.include_router(
    auth_router,
    prefix="/auth"
)

# =====================================================
# TEAMS ROUTER
# =====================================================

app.include_router(
    teams_router,
    prefix="/teams",
    tags=["Teams"]
)

# =====================================================
# INVITATIONS ROUTER
# =====================================================

app.include_router(
    invitations_router,
    prefix="/invitations",
    tags=["Invitations"]
)



# =====================================================
# HEALTH CHECK
# =====================================================

@app.get(
    "/health",
    tags=["Health"]
)
async def health_check():
    return {
        "ok": True
    }


# =====================================================
# LIVENESS CHECK
# =====================================================

@app.get(
    "/live",
    tags=["Health"]
)
async def liveness_check():
    return {
        "ok": True
    }


# =====================================================
# READINESS CHECK
# =====================================================

@app.get(
    "/ready",
    tags=["Health"]
)
async def readiness_check():
    checks = {}
    ready = True

    # Check database connectivity
    def check_db():
        with engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM links LIMIT 1"))
            read_only = conn.execute(text("SHOW transaction_read_only")).scalar()
            if read_only == 'on':
                raise Exception("Database is in read-only mode (writes disabled)")

    try:
        await asyncio.wait_for(asyncio.to_thread(check_db), timeout=2.0)
        checks["database"] = "connected"
    except Exception as e:
        checks["database"] = f"disconnected: {str(e)}"
        ready = False

    # Check cache connectivity (if applicable)
    try:
        if cache.redis_client is None:
            raise Exception("Redis client not initialized")
        await asyncio.wait_for(cache.redis_client.ping(), timeout=2.0)
        checks["cache"] = "connected"
    except Exception as e:
        checks["cache"] = f"disconnected: {str(e)}"
        ready = False

    # Include uptime
    checks["uptime_seconds"] = int(time.time() - start_time)

    status_code = 200 if ready else 503
    return JSONResponse(
        status_code=status_code,
        content={"ok": ready, "checks": checks}
    )

# =====================================================
# MEMORY DEBUG ENDPOINT (DEVELOPMENT ONLY)
# =====================================================

if settings.app_env.value == "development":
    @app.get(
        "/debug/memory",
        tags=["Debug"]
    )
    async def memory_debug():

        snapshot = tracemalloc.take_snapshot()

        top_stats = snapshot.statistics("lineno")[:10]

        return {
            "top_allocations": [
                {
                    "location": str(stat.traceback[0]),
                    "size_kb": round(
                        stat.size / 1024,
                        2
                    ),
                    "count": stat.count
                }
                for stat in top_stats
            ]
        }
@app.get("/metrics")
async def metrics():
    # Update process memory gauge before generating metrics
    try:
        from app.metrics import process_memory_bytes
        # Read RSS from /proc/self/status (Linux containers)
        with open("/proc/self/status", "r") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    rss_kb = int(line.split()[1])
                    process_memory_bytes.set(rss_kb * 1024)
                    break
    except FileNotFoundError:
        pass  # not on Linux; skip memory metric
    except Exception:
        pass  # best-effort; don't break /metrics

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

# =====================================================
# LINKS ROUTER
# =====================================================

app.include_router(
    links_router
)

# =====================================================
# WEBSOCKET ROUTER
# =====================================================

app.include_router(
    websocket_router,
    prefix="/teams",
    tags=["Teams"]
)

# =====================================================
# COMMENTS ROUTER
# =====================================================

app.include_router(
    comments_router,
    tags=["Comments"]
)

# =====================================================
# AUDIT ROUTER
# =====================================================

app.include_router(
    audit_router,
    tags=["Audit"]
)