from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, select
from app.database import get_db
from app.auth import get_current_user
from app import schemas, crud
import app.models as models

router = APIRouter()

@router.get("/teams/{team_id}/audit-logs", response_model=list[schemas.AuditLogOut])
def get_team_audit_logs(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    # Verify team exists
    team = crud.get_team(db=db, team_id=team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )

    # Verify authorization (must be a team member)
    if not crud.is_team_member(db=db, team_id=team_id, email=current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team members can read audit logs"
        )

    # Subquery for tasks belonging to the team
    task_ids_subquery = select(models.Task.id).where(models.Task.team_id == team_id)
    
    # Subquery for comments belonging to those tasks
    comment_ids_subquery = select(models.Comment.id).join(
        models.Task, models.Comment.task_id == models.Task.id
    ).where(models.Task.team_id == team_id)

    # Subquery for invitations belonging to the team
    invitation_ids_subquery = select(models.Invitation.id).where(models.Invitation.team_id == team_id)

    # Fetch audit logs matching team, task, comment, or invitation resource criteria
    logs = db.query(models.AuditLog).filter(
        or_(
            (models.AuditLog.resource_type == "team") & (models.AuditLog.resource_id == team_id),
            (models.AuditLog.resource_type == "task") & (models.AuditLog.resource_id.in_(task_ids_subquery)),
            (models.AuditLog.resource_type == "comment") & (models.AuditLog.resource_id.in_(comment_ids_subquery)),
            (models.AuditLog.resource_type == "invitation") & (models.AuditLog.resource_id.in_(invitation_ids_subquery))
        )
    ).order_by(models.AuditLog.timestamp.desc()).all()

    return logs
