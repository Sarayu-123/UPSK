from sqlalchemy.orm import Session
from app.logging_config import logger
import app.models as models
from app.routers.websocket import manager

async def notify_mentioned_users(
    db: Session,
    mentions: list[dict],
    team_id: int,
    source_type: str,
    source_id: int,
    actor: str
):
    """
    Notify mentioned users within a team context.
    Matches username prefixes to team memberships and broadcasts events.
    """
    for mention in mentions:
        username = mention["username"]
        
        # Query team membership to resolve username (email prefix) to full email
        membership = db.query(models.TeamMembership).filter(
            models.TeamMembership.team_id == team_id,
            models.TeamMembership.user_email.like(f"{username}@%")
        ).first()
        
        if membership:
            mentioned_email = membership.user_email
            
            # Log the notification
            logger.info("mention_notified",
                mentioned_email=mentioned_email,
                source_type=source_type,
                source_id=source_id,
                actor=actor
            )
            
            # Emit WebSocket notification event
            await manager.broadcast_event(
                team_id=team_id,
                event_type="mention_notified",
                actor=actor,
                payload={
                    "mentioned_email": mentioned_email,
                    "source_type": source_type,
                    "source_id": source_id,
                    "raw": mention["raw"],
                    "position": mention["position"]
                }
            )
        else:
            logger.warning("mention_user_not_found",
                username=username,
                team_id=team_id
            )
