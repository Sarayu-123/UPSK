from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app import schemas
import app.models as models

router = APIRouter()


@router.post("/{invitation_id}/accept", response_model=schemas.InvitationOut)
async def accept_invitation(
    invitation_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    # Retrieve invitation
    invitation = db.query(models.Invitation).filter(models.Invitation.id == invitation_id).first()
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )
    
    # Verify the invitation belongs to the accepting user
    if invitation.email != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only accept invitations sent to your email address"
        )
    
    # Check if already accepted
    if invitation.status == "accepted":
        # Check if membership already exists, if not create it
        existing_membership = db.query(models.TeamMembership).filter(
            models.TeamMembership.team_id == invitation.team_id,
            models.TeamMembership.user_email == current_user
        ).first()
        if not existing_membership:
            membership = models.TeamMembership(
                team_id=invitation.team_id,
                user_email=current_user,
                role="member"
            )
            db.add(membership)
            db.commit()
        return invitation

    # Check if membership already exists
    existing_membership = db.query(models.TeamMembership).filter(
        models.TeamMembership.team_id == invitation.team_id,
        models.TeamMembership.user_email == current_user
    ).first()
    
    if not existing_membership:
        membership = models.TeamMembership(
            team_id=invitation.team_id,
            user_email=current_user,
            role="member"
        )
        db.add(membership)

    invitation.status = "accepted"
    db.commit()
    db.refresh(invitation)

    # Record audit log entry
    from app.services.audit_logger import record_audit_log
    record_audit_log(
        db=db,
        action="accept",
        resource_type="invitation",
        resource_id=invitation.id,
        actor_email=current_user,
        details={"team_id": invitation.team_id, "email": invitation.email}
    )

    # Broadcast event via websocket connection manager
    try:
        from app.routers.websocket import manager
        await manager.broadcast_event(
            team_id=invitation.team_id,
            event_type="invitation_accepted",
            actor=current_user,
            payload={
                "id": invitation.id,
                "email": invitation.email,
                "invited_by": invitation.invited_by,
                "status": "accepted"
            }
        )
    except Exception as e:
        import structlog
        logger = structlog.get_logger()
        logger.warning("Websocket broadcast failed", error=str(e), team_id=invitation.team_id, invitation_id=invitation.id)

    return invitation
