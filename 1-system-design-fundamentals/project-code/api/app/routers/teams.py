from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app import schemas, crud
import app.models as models

router = APIRouter()


@router.post("/", response_model=schemas.TeamOut, status_code=status.HTTP_201_CREATED)
def create_new_team(
    team_in: schemas.TeamCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    if not team_in.name or not team_in.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team name cannot be empty"
        )

    # Check duplicate team name
    existing_team = db.query(models.Team).filter(models.Team.name == team_in.name).first()
    if existing_team:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Team name already exists"
        )

    team = crud.create_team(db=db, team_in=team_in, user_email=current_user)
    
    # Record audit log entry
    from app.services.audit_logger import record_audit_log
    record_audit_log(
        db=db,
        action="create",
        resource_type="team",
        resource_id=team.id,
        actor_email=current_user,
        details={"name": team.name}
    )
    
    return team


@router.get("/", response_model=list[schemas.TeamOut])
def list_teams(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    return crud.get_user_teams(db=db, user_email=current_user)


@router.delete("/{id}")
def remove_team(
    id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    team = crud.get_team(db=db, team_id=id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )

    # Verify authorization (only admins can delete)
    if not crud.is_team_admin(db=db, team_id=id, email=current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team admins can delete the team"
        )

    success = crud.delete_team(db=db, team_id=id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    return {"ok": True}


@router.post("/{team_id}/invitations", response_model=schemas.InvitationOut, status_code=status.HTTP_201_CREATED)
async def invite_to_team(
    team_id: int,
    invitation_in: schemas.InvitationCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    team = crud.get_team(db=db, team_id=team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )

    # Verify authorization (only admins can invite)
    if not crud.is_team_admin(db=db, team_id=team_id, email=current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team admins can invite members"
        )

    # Verify email format
    email = invitation_in.email
    if not email or "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )

    # Check if user is already a member
    if crud.is_team_member(db=db, team_id=team_id, email=email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of the team"
        )

    # Check if a pending invitation already exists
    existing_invitation = db.query(models.Invitation).filter(
        models.Invitation.team_id == team_id,
        models.Invitation.email == email,
        models.Invitation.status == "pending"
    ).first()
    if existing_invitation:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An invitation is already pending for this user"
        )

    invitation = crud.create_invitation(
        db=db,
        team_id=team_id,
        email=email,
        invited_by=current_user
    )

    # Record audit log entry
    from app.services.audit_logger import record_audit_log
    record_audit_log(
        db=db,
        action="invite",
        resource_type="invitation",
        resource_id=invitation.id,
        actor_email=current_user,
        details={"team_id": team_id, "invitee_email": email}
    )

    # Broadcast event via websocket connection manager
    from app.routers.websocket import manager
    await manager.broadcast_event(
        team_id=team_id,
        event_type="invitation_created",
        actor=current_user,
        payload={
            "id": invitation.id,
            "email": invitation.email,
            "invited_by": invitation.invited_by,
            "status": invitation.status
        }
    )

    return invitation


@router.put("/{team_id}/members/{user_email}", response_model=schemas.TeamMemberOut)
def update_member_role(
    team_id: int,
    user_email: str,
    body: schemas.UpdateMemberRole,
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

    # Verify requester membership
    requester_membership = db.query(models.TeamMembership).filter(
        models.TeamMembership.team_id == team_id,
        models.TeamMembership.user_email == current_user
    ).first()
    if not requester_membership or requester_membership.role not in ("admin", "owner"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team admins and owners can modify member roles"
        )

    # A user cannot modify their own role
    if user_email == current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify your own role"
        )

    # Validate role value (must be owner, admin, member, or viewer)
    if not body.role or body.role.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role cannot be empty"
        )
    if body.role not in ("owner", "admin", "member", "viewer"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role value"
        )

    # Verify target is a member of this team
    target_membership = db.query(models.TeamMembership).filter(
        models.TeamMembership.team_id == team_id,
        models.TeamMembership.user_email == user_email
    ).first()
    if not target_membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member not found"
        )

    # An admin cannot promote another user to owner
    if body.role == "owner" and requester_membership.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can promote other users to owner"
        )

    # An admin cannot modify an owner's role
    if target_membership.role == "owner" and requester_membership.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can modify owner roles"
        )

    old_role = target_membership.role
    membership = crud.update_member_role(
        db=db,
        team_id=team_id,
        target_email=user_email,
        new_role=body.role
    )

    # Record audit log entry
    from app.services.audit_logger import record_audit_log
    record_audit_log(
        db=db,
        action="role_change",
        resource_type="team",
        resource_id=team_id,
        actor_email=current_user,
        details={
            "team_id": team_id,
            "target_user": user_email,
            "old_role": old_role,
            "new_role": body.role,
            "requesting_user": current_user
        }
    )

    return membership
