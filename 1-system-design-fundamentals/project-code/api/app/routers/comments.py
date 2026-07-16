from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app import schemas, crud
import app.models as models
from app.routers.websocket import manager
from app.utils.mention_parser import parse_mentions
from app.services.mention_notification import notify_mentioned_users
from app.services.audit_logger import record_audit_log
from app.utils.event_bus import event_bus

router = APIRouter()

# =========================================================
# TASKS ENDPOINTS (Helper endpoints for verification)
# =========================================================

@router.post("/teams/{team_id}/tasks", response_model=schemas.TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    team_id: int,
    task_in: schemas.TaskCreate,
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

    # Verify authorization
    if not crud.is_team_member(db=db, team_id=team_id, email=current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team members can create tasks"
        )

    if not task_in.title or not task_in.title.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task title cannot be empty"
        )

    db_task = models.Task(
        team_id=team_id,
        title=task_in.title,
        created_by=current_user
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    record_audit_log(
        db=db,
        action="create",
        resource_type="task",
        resource_id=db_task.id,
        actor_email=current_user,
        details={"title": db_task.title}
    )

    return db_task


@router.get("/teams/{team_id}/tasks", response_model=list[schemas.TaskOut])
def list_tasks(
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

    # Verify authorization
    if not crud.is_team_member(db=db, team_id=team_id, email=current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team members can list tasks"
        )

    return db.query(models.Task).filter(models.Task.team_id == team_id).all()


# =========================================================
# COMMENTS ENDPOINTS (Agent 1 Core)
# =========================================================

@router.post("/tasks/{task_id}/comments", response_model=schemas.CommentOut, status_code=status.HTTP_201_CREATED)
async def create_comment(
    task_id: int,
    comment_in: schemas.CommentCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    # Verify task exists
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Verify authorization (Must be a member of the team owning the task)
    if not crud.is_team_member(db=db, team_id=task.team_id, email=current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team members can comment on this task"
        )

    if not comment_in.body or not comment_in.body.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment body cannot be empty"
        )

    # If parent_id is specified, verify it exists and belongs to the same task
    if comment_in.parent_id is not None:
        parent_comment = db.query(models.Comment).filter(models.Comment.id == comment_in.parent_id).first()
        if not parent_comment or parent_comment.task_id != task_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent comment not found or belongs to a different task"
            )

    db_comment = models.Comment(
        task_id=task_id,
        author_email=current_user,
        body=comment_in.body,
        parent_id=comment_in.parent_id
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)

    # Parse and notify mentions
    mentions = parse_mentions(db_comment.body)
    if mentions:
        await notify_mentioned_users(
            db=db,
            mentions=mentions,
            team_id=task.team_id,
            source_type="comment",
            source_id=db_comment.id,
            actor=current_user
        )

    # Publish domain event for auditing
    await event_bus.publish(
        "comment.created",
        {
            "event_type": "comment.created",
            "resource_type": "comment",
            "resource_id": db_comment.id,
            "actor_email": current_user,
            "details": {"body": db_comment.body, "task_id": task_id}
        }
    )

    # Emit Domain Event via Websocket manager
    await manager.broadcast_event(
        team_id=task.team_id,
        event_type="comment_created",
        actor=current_user,
        payload={
            "id": db_comment.id,
            "task_id": db_comment.task_id,
            "author_email": db_comment.author_email,
            "body": db_comment.body,
            "parent_id": db_comment.parent_id
        }
    )

    return db_comment


@router.get("/tasks/{task_id}/comments", response_model=list[schemas.CommentOut])
def get_comments(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    # Verify task exists
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Verify authorization
    if not crud.is_team_member(db=db, team_id=task.team_id, email=current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team members can read comments on this task"
        )

    # Default to returning comments associated with the task
    # (Front-end can build a tree or nest as needed; or we can filter parent_id is null if wanted,
    # but returning a flat list is clean and allows the API to keep nesting simple).
    return db.query(models.Comment).filter(models.Comment.task_id == task_id).all()


@router.post("/comments/{comment_id}/replies", response_model=schemas.CommentOut, status_code=status.HTTP_201_CREATED)
async def create_reply(
    comment_id: int,
    reply_in: schemas.CommentCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    # Verify parent comment exists
    parent_comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not parent_comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent comment not found"
        )

    # Get task
    task = db.query(models.Task).filter(models.Task.id == parent_comment.task_id).first()
    if not task:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Verify authorization
    if not crud.is_team_member(db=db, team_id=task.team_id, email=current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team members can reply to comments on this task"
        )

    if not reply_in.body or not reply_in.body.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reply body cannot be empty"
        )

    db_reply = models.Comment(
        task_id=parent_comment.task_id,
        author_email=current_user,
        body=reply_in.body,
        parent_id=comment_id
    )
    db.add(db_reply)
    db.commit()
    db.refresh(db_reply)

    # Parse and notify mentions
    mentions = parse_mentions(db_reply.body)
    if mentions:
        await notify_mentioned_users(
            db=db,
            mentions=mentions,
            team_id=task.team_id,
            source_type="comment",
            source_id=db_reply.id,
            actor=current_user
        )

    # Publish domain event for auditing
    await event_bus.publish(
        "comment.created",
        {
            "event_type": "comment.created",
            "resource_type": "comment",
            "resource_id": db_reply.id,
            "actor_email": current_user,
            "details": {"body": db_reply.body, "parent_id": comment_id, "task_id": parent_comment.task_id}
        }
    )

    # Emit Domain Event via Websocket manager
    await manager.broadcast_event(
        team_id=task.team_id,
        event_type="comment_created",
        actor=current_user,
        payload={
            "id": db_reply.id,
            "task_id": db_reply.task_id,
            "author_email": db_reply.author_email,
            "body": db_reply.body,
            "parent_id": db_reply.parent_id
        }
    )

    return db_reply


@router.delete("/comments/{comment_id}", status_code=status.HTTP_200_OK)
async def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )

    task = db.query(models.Task).filter(models.Task.id == comment.task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Verify authorization (only comment author or team admin can delete)
    is_author = comment.author_email == current_user
    is_admin = crud.is_team_admin(db=db, team_id=task.team_id, email=current_user)

    if not (is_author or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only comment author or team admin can delete comments"
        )

    db.delete(comment)
    db.commit()

    # Publish domain event for auditing
    await event_bus.publish(
        "comment.deleted",
        {
            "event_type": "comment.deleted",
            "resource_type": "comment",
            "resource_id": comment_id,
            "actor_email": current_user,
            "details": {"task_id": task.id}
        }
    )

    # Emit Domain Event
    await manager.broadcast_event(
        team_id=task.team_id,
        event_type="comment_deleted",
        actor=current_user,
        payload={
            "id": comment_id,
            "task_id": task.id
        }
    )

    return {"ok": True}
