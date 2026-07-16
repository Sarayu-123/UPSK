from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
    Query
)

from fastapi.responses import RedirectResponse

from sqlalchemy.orm import Session
from sqlalchemy import func

import hashlib
from datetime import datetime

from app.tasks import record_click_task

from app.auth import get_current_user
from app.database import get_db
from app.limiter import limiter

from app.models import ClickEvent

from app.schemas import (
    LinkCreate,
    LinkResponse,
    LinkUpdate,
    SearchResponse,
    PaginationMetadata
)

from app.cache import (
    get_cache,
    set_cache,
    delete_cache
)

from app.logging_config import logger

from app.resilience import safe_db_call
import pybreaker
import asyncio

from app import crud
from app.crud import search_links


router = APIRouter()


# =========================================================
# ASYNC ANALYTICS ENQUEUE
# =========================================================

async def enqueue_click_analytics(
    request: Request,
    link_id: int,
    long_url: str
):
    ip_address = (
        request.client.host
        if request.client
        else "127.0.0.1"
    )

    user_agent = request.headers.get(
        "user-agent"
    )

    referrer = request.headers.get(
        "referer"
    )

    timestamp_bucket = datetime.utcnow().strftime(
        "%Y%m%d%H%M"
    )

    raw_click_string = (
        f"{link_id}:"
        f"{ip_address}:"
        f"{user_agent}:"
        f"{timestamp_bucket}"
    )

    click_id = hashlib.sha256(
        raw_click_string.encode()
    ).hexdigest()

    try:
        await asyncio.wait_for(
            asyncio.to_thread(
                record_click_task.delay,
                click_id=click_id,
                link_id=link_id,
                ip_address=ip_address,
                user_agent=user_agent,
                referrer=referrer
            ),
            timeout=0.2
        )
        logger.info(f"Analytics task queued: {click_id}")
    except asyncio.TimeoutError:
        logger.warning("dependency_timeout", dependency="celery", operation="enqueue_analytics", timeout_ms=200)
    except Exception as exc:
        logger.warning(f"Failed to enqueue analytics task: {exc}")

    return RedirectResponse(
        url=long_url,
        status_code=status.HTTP_302_FOUND
    )


# =========================================================
# CREATE SHORT LINK
# =========================================================

@router.post(
    "/links",
    response_model=LinkResponse,
    status_code=status.HTTP_201_CREATED
)
@limiter.limit("30/minute")
async def create_short_link(
    request: Request,
    link_in: LinkCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    logger.info(
        "create_link_requested",
        user=current_user,
        long_url=str(link_in.long_url)
    )

    link_in.created_by = current_user

    try:
        return await safe_db_call(crud.create_link, db, link_in, timeout=1.0)
    except pybreaker.CircuitBreakerError:
        logger.warning("circuit_open_fallback", dependency="database", operation="create_link")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service Unavailable")
    except Exception:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service Unavailable")


# =========================================================
# LIST USER LINKS
# =========================================================

@router.get(
    "/links",
    response_model=list[LinkResponse]
)
@limiter.limit("60/minute")
async def list_user_links(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    try:
        return await safe_db_call(
            crud.get_links_by_user,
            db,
            current_user,
            skip=skip,
            limit=limit,
            timeout=1.0
        )
    except pybreaker.CircuitBreakerError:
        logger.warning("circuit_open_fallback", dependency="database", operation="list_user_links")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service Unavailable")
    except Exception:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service Unavailable")


# =========================================================
# SEARCH USER LINKS
# =========================================================

@router.get(
    "/links/search",
    response_model=SearchResponse
)
@limiter.limit("60/minute")
async def search_user_links(
    request: Request,
    q: str | None = Query(
        default=None,
        max_length=100
    ),
    page: int = Query(
        default=1,
        ge=1
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100
    ),
    sort_by: str = Query(
        default="created_at"
    ),
    sort_order: str = Query(
        default="desc",
        pattern="^(asc|desc)$"
    ),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    allowed_sort_fields = {
        "created_at",
        "code",
        "long_url"
    }

    if sort_by not in allowed_sort_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid sort field"
        )

    skip = (
    (page - 1)
    * page_size
    )

    try:
        results, total_count = await safe_db_call(
            search_links,
            db=db,
            current_user=current_user,
            q=q,
            skip=skip,
            limit=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
            timeout=1.0
        )
    except pybreaker.CircuitBreakerError:
        logger.warning("circuit_open_fallback", dependency="database", operation="search_links")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service Unavailable")
    except Exception:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service Unavailable")

    total_pages = (
        (total_count + page_size - 1)
        // page_size
        if total_count > 0
        else 0
    )

    pagination = PaginationMetadata(
        page=page,
        page_size=page_size,
        total_count=total_count,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1
    )

    return SearchResponse(
        items=results,
        pagination=pagination
    )


# =========================================================
# GET SINGLE LINK
# =========================================================

@router.get(
    "/links/{link_id}",
    response_model=LinkResponse
)
@limiter.limit("60/minute")
async def get_short_link(
    request: Request,
    link_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    try:
        link = await safe_db_call(crud.get_link, db, link_id, timeout=1.0)
    except pybreaker.CircuitBreakerError:
        logger.warning("circuit_open_fallback", dependency="database", operation="get_link")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service Unavailable")
    except Exception:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service Unavailable")

    if not link or link.created_by != current_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    return link


# =========================================================
# ANALYTICS ENDPOINT
# =========================================================

@router.get(
    "/links/{link_id}/analytics"
)
@limiter.limit("30/minute")
async def get_link_analytics(
    request: Request,
    link_id: int,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    try:
        link = await safe_db_call(crud.get_link, db, link_id, timeout=1.0)
    except pybreaker.CircuitBreakerError:
        logger.warning("circuit_open_fallback", dependency="database", operation="analytics_get_link")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service Unavailable")
    except Exception:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service Unavailable")

    if not link or link.created_by != current_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")

    try:
        click_count = await safe_db_call(crud.get_link_analytics_count, db, link_id, from_date, to_date, timeout=1.0)
    except pybreaker.CircuitBreakerError:
        logger.warning("circuit_open_fallback", dependency="database", operation="analytics_count")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service Unavailable")
    except Exception:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service Unavailable")

    return {
        "link_id": link_id,
        "code": link.code,
        "click_count": click_count,
        "from_date": from_date,
        "to_date": to_date
    }


# =========================================================
# UPDATE LINK
# =========================================================

@router.patch(
    "/links/{link_id}",
    response_model=LinkResponse
)
@limiter.limit("30/minute")
async def update_short_link(
    request: Request,
    link_id: int,
    link_update: LinkUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    try:
        link = await safe_db_call(crud.get_link, db, link_id, timeout=1.0)
    except pybreaker.CircuitBreakerError:
        logger.warning("circuit_open_fallback", dependency="database", operation="update_get_link")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service Unavailable")
    except Exception:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service Unavailable")

    if not link or link.created_by != current_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")

    try:
        link = await safe_db_call(crud.update_link, db, link, str(link_update.long_url), timeout=1.0)
    except pybreaker.CircuitBreakerError:
        logger.warning("circuit_open_fallback", dependency="database", operation="update_link")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service Unavailable")
    except Exception:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service Unavailable")

    await delete_cache(
        f"link:redirect:{link.code}"
    )

    logger.info(
        f"Cache invalidated for code={link.code}"
    )

    return link


# =========================================================
# DELETE LINK
# =========================================================

@router.delete(
    "/links/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
@limiter.limit("30/minute")
async def delete_short_link(
    request: Request,
    link_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    try:
        link = await safe_db_call(crud.get_link, db, link_id, timeout=1.0)
    except pybreaker.CircuitBreakerError:
        logger.warning("circuit_open_fallback", dependency="database", operation="delete_get_link")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service Unavailable")
    except Exception:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service Unavailable")

    if not link or link.created_by != current_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")

    code = link.code
    try:
        await safe_db_call(crud.delete_link, db, link, timeout=1.0)
    except pybreaker.CircuitBreakerError:
        logger.warning("circuit_open_fallback", dependency="database", operation="delete_link")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service Unavailable")
    except Exception:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service Unavailable")

    await delete_cache(
        f"link:redirect:{code}"
    )

    logger.info(
        f"Cache invalidated for deleted code={code}"
    )


# =========================================================
# REDIRECT
# =========================================================

@router.get("/{code}")
@limiter.limit("120/minute")
async def redirect_link(
    request: Request,
    code: str,
    db: Session = Depends(get_db)
):
    cache_key = f"link:redirect:{code}"

    cached_value = await get_cache(cache_key)

    # Negative cache hit
    if cached_value == "__NOT_FOUND__":
        logger.info(
            f"Negative cache hit for code={code}"
        )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )

    # Positive cache hit
    if cached_value:
        logger.info(
            f"Cache hit for code={code}"
        )

        cached_link_id, cached_long_url = (
            cached_value.split("|", 1)
        )

        return await enqueue_click_analytics(
            request=request,
            link_id=int(cached_link_id),
            long_url=cached_long_url
        )

    logger.info(
        f"Cache miss for code={code}"
    )

    # Database fallback
    try:
        link = await safe_db_call(crud.get_link_by_code, db, code, timeout=1.0)
    except pybreaker.CircuitBreakerError:
        logger.warning("circuit_open_fallback", dependency="database", operation="redirect_get_link")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service Unavailable")
    except Exception:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service Unavailable")

    if not link:
        await set_cache(
            cache_key,
            "__NOT_FOUND__",
            ttl_seconds=60
        )

        logger.info(
            f"Negative cache stored for code={code}"
        )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )

    # Cache successful lookup
    cache_payload = (
        f"{link.id}|{link.long_url}"
    )

    await set_cache(
        cache_key,
        cache_payload,
        ttl_seconds=300
    )

    logger.info(
        f"Cached redirect for code={code}"
    )

    return await enqueue_click_analytics(
        request=request,
        link_id=link.id,
        long_url=link.long_url
    )