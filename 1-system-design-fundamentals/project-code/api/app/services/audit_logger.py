from sqlalchemy.orm import Session
import app.models as models

def record_audit_log(
    db: Session,
    action: str,
    resource_type: str,
    resource_id: int,
    actor_email: str,
    details: dict | None = None
) -> models.AuditLog:
    """
    Record an audit log entry in the database.
    """
    db_log = models.AuditLog(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        actor_email=actor_email,
        details=details
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log
