import pytest

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.main as main_module

# =========================================================
# FASTAPI APP
# =========================================================

app = main_module.app

from app.database import Base, get_db
from app.models import Link, ClickEvent
from app.cache import redis_client

# =========================================================
# TEST DATABASE & CONFIG IMPORTED FROM CONFTEST
# =========================================================
from conftest import TestingSessionLocal, engine

# =========================================================
# CELERY TEST CONFIG
# =========================================================

from app.celery_app import celery_app

# Run Celery tasks synchronously during tests
celery_app.conf.task_always_eager = True

import app.tasks as tasks_module
from app.tasks import record_click_task

# =========================================================
# TEST CLIENT
# =========================================================

client = TestClient(app)

# =========================================================
# TEST SETUP / CLEANUP FOR REDIS
# =========================================================

@pytest.fixture(autouse=True)
def setup_redis():
    if redis_client:
        import asyncio
        try:
            asyncio.run(redis_client.flushdb())
        except Exception:
            pass
    if tasks_module.redis_client:
        try:
            tasks_module.redis_client.flushdb()
        except Exception:
            pass

    yield

    if redis_client:
        import asyncio
        try:
            asyncio.run(redis_client.flushdb())
        except Exception:
            pass

    if tasks_module.redis_client:
        try:
            tasks_module.redis_client.flushdb()
        except Exception:
            pass


# =========================================================
# HEALTH TEST
# =========================================================

def test_health():

    response = client.get("/health")

    assert response.status_code == 200

    assert response.json() == {
        "ok": True
    }

# =========================================================
# HELPER TOKEN
# =========================================================

def get_auth_token():

    response = client.post(
        "/auth/login",
        data={
            "username": "admin@example.com",
            "password": "password123"
        }
    )

    return response.json()["access_token"]

# =========================================================
# 1. LINK CREATION TEST
# =========================================================

def test_create_link():

    token = get_auth_token()

    response = client.post(
        "/links",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "long_url": "https://example.com/test"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["long_url"] == (
        "https://example.com/test"
    )

    assert "code" in data

# =========================================================
# 2. REDIRECT TEST
# =========================================================

def test_redirect_link():

    token = get_auth_token()

    create_response = client.post(
        "/links",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "long_url": "https://google.com/"
        }
    )

    code = create_response.json()["code"]

    redirect_response = client.get(
        f"/{code}",
        follow_redirects=False
    )

    assert redirect_response.status_code == 302

    assert (
        redirect_response.headers["location"]
        == "https://google.com/"
    )

# =========================================================
# 3. AUTH PROTECTION TEST
# =========================================================

def test_auth_required():

    response = client.get("/links")

    assert response.status_code == 401

# =========================================================
# 4. IDOR SCOPING TEST
# =========================================================

def test_idor_protection():

    token = get_auth_token()

    create_response = client.post(
        "/links",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "long_url": "https://example.com/private"
        }
    )

    link_id = create_response.json()["id"]

    response = client.get(
        f"/links/{link_id}",
        headers={
            "Authorization": "Bearer invalidtoken"
        }
    )

    assert response.status_code in [
        401,
        404
    ]

# =========================================================
# 5. RETENTION PURGE TEST
# =========================================================

def test_purge_old_clicks():

    db = TestingSessionLocal()

    link = Link(
        code=f"purgetest_{datetime.utcnow().timestamp()}",
        long_url="https://example.com",
        created_by="admin@example.com"
    )

    db.add(link)
    db.commit()
    db.refresh(link)

    old_click = ClickEvent(
        link_id=link.id,
        ip_hash="oldhash",
        clicked_at=(
            datetime.utcnow()
            - timedelta(days=90)
        )
    )

    db.add(old_click)
    db.commit()

    deleted = (
        db.query(ClickEvent)
        .filter(
            ClickEvent.clicked_at
            < datetime.utcnow() - timedelta(days=30)
        )
        .delete()
    )

    db.commit()

    assert deleted >= 1

    db.close()

# =========================================================
# 6. INVALID URL TEST
# =========================================================

def test_invalid_url_rejected():

    token = get_auth_token()

    response = client.post(
        "/links",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "long_url": "javascript:alert(1)"
        }
    )

    assert response.status_code == 422

# =========================================================
# 7. SEARCH TEST
# =========================================================

def test_search_links():

    token = get_auth_token()

    client.post(
        "/links",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "long_url": (
                "https://example.com/"
                "unique_python_course"
            )
        }
    )

    response = client.get(
        "/links/search?q=python",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["pagination"]["total_count"] >= 1

    assert (
        "python"
        in data["items"][0]["long_url"]
    )

# =========================================================
# 8. PAGE SIZE VALIDATION
# =========================================================

def test_page_size_validation():

    token = get_auth_token()

    response = client.get(
        "/links/search?page_size=1000",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 422

# =========================================================
# 9. INVALID SORT FIELD TEST
# =========================================================

def test_invalid_sort_field():

    token = get_auth_token()

    response = client.get(
        "/links/search?sort_by=DROP_TABLE",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 400

# =========================================================
# 10. CELERY IDEMPOTENCY TEST
# =========================================================

def test_celery_task_idempotency():

    db = TestingSessionLocal()

    # Create test link
    link = Link(
        code=f"idempotenttest_{datetime.utcnow().timestamp()}",
        long_url="https://example.com",
        created_by="admin@example.com"
    )

    db.add(link)
    db.commit()
    db.refresh(link)

    db.close()

    # Same click_id called twice
    click_id = "test_duplicate_click_id"

    record_click_task(
        click_id=click_id,
        link_id=link.id,
        ip_address="127.0.0.1",
        user_agent="pytest",
        referrer="http://localhost"
    )

    record_click_task(
        click_id=click_id,
        link_id=link.id,
        ip_address="127.0.0.1",
        user_agent="pytest",
        referrer="http://localhost"
    )

    # Verify only ONE click exists
    db_verify = TestingSessionLocal()

    try:
        click_count = (
            db_verify.query(ClickEvent)
            .filter(
                ClickEvent.ip_hash == click_id
            )
            .count()
        )

        assert (
            click_count == 1
        ), (
            f"Expected 1 click event, "
            f"found {click_count}"
        )
    finally:
        db_verify.close()