from app.database import SessionLocal
from app.services.audit_logger import record_audit_log

async def _record_comment_event(
    payload: dict,
    action: str,
) -> None:
    # Use context manager to guarantee resource cleanup (session closure and rollback on exception)
    with SessionLocal() as db:
        try:
            record_audit_log(
                db=db,
                action=action,
                resource_type=payload["resource_type"],
                resource_id=payload["resource_id"],
                actor_email=payload["actor_email"],
                details=payload.get("details", {}),
            )
            # record_audit_log handles commit internally, but we can commit explicitly if needed
            db.commit()
        except Exception:
            db.rollback()
            raise

async def handle_comment_created(payload: dict) -> None:
    await _record_comment_event(payload, action="create")

async def handle_comment_updated(payload: dict) -> None:
    await _record_comment_event(payload, action="update")

async def handle_comment_deleted(payload: dict) -> None:
    await _record_comment_event(payload, action="delete")
