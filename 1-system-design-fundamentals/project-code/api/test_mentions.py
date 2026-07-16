import sys
from app.utils.mention_parser import parse_mentions
from app.services.mention_notification import notify_mentioned_users
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
import app.crud as crud
import app.models as models
import app.schemas as schemas
from app.auth import create_access_token
import asyncio

def setup_test_data(db):
    user_a = "user_a_mentions@example.com"
    user_b = "user_b_mentions@example.com"
    
    # Cleanup
    db.query(models.Comment).delete()
    db.query(models.Task).delete()
    db.query(models.TeamMembership).filter(models.TeamMembership.user_email.in_([user_a, user_b])).delete(synchronize_session=False)
    db.query(models.Team).filter(models.Team.created_by.in_([user_a, user_b])).delete(synchronize_session=False)
    db.commit()
    
    # Create Team A under User A
    team_in = schemas.TeamCreate(name="Mentions Team A")
    team_a = crud.create_team(db, team_in, user_a)
    
    # Add User B to Team A as member
    db_membership = models.TeamMembership(
        team_id=team_a.id,
        user_email=user_b,
        role="member"
    )
    db.add(db_membership)
    db.commit()
    db.refresh(team_a)
    
    # Generate tokens
    token_a = create_access_token({"sub": user_a})
    token_b = create_access_token({"sub": user_b})
    
    return team_a, token_a, token_b, user_a, user_b

def test_mentions_endpoints():
    print("=== Running @Mention Parsing and Notification (Agent 2) Tests ===")
    
    # 1. Test Parser Unit
    print("Testing parser unit...")
    text = "Hello @user_a_mentions and @user_b_mentions. Also @non_existent."
    parsed = parse_mentions(text)
    assert len(parsed) == 3
    assert parsed[0]["username"] == "user_a_mentions"
    assert parsed[0]["raw"] == "@user_a_mentions"
    assert parsed[1]["username"] == "user_b_mentions"
    assert parsed[2]["username"] == "non_existent"
    print("PASS: Parser parsed @mentions correctly with start/end positions")

    # 2. Test Notification Resolution and Broadcast
    print("Testing notification service...")
    db = SessionLocal()
    client = TestClient(app)
    try:
        team_a, token_a, token_b, user_a, user_b = setup_test_data(db)
        
        # Connect User B to WebSocket (User B is the one who will be mentioned by User A)
        with client.websocket_connect(f"/teams/ws?token={token_b}") as ws_b:
            print("PASS: User B connected to WS")
            
            # Setup notification test
            # User A mentions User B: "Hey @user_b_mentions check this out!"
            text_with_mention = "Hey @user_b_mentions check this out!"
            
            # Trigger notification by posting a task and comment via REST client
            headers_a = {"Authorization": f"Bearer {token_a}"}
            task_resp = client.post(
                f"/teams/{team_a.id}/tasks",
                json={"title": "Test Task"},
                headers=headers_a
            )
            assert task_resp.status_code == 201, f"Failed to create task: {task_resp.text}"
            task_id = task_resp.json()["id"]
            
            comment_resp = client.post(
                f"/tasks/{task_id}/comments",
                json={"body": text_with_mention},
                headers=headers_a
            )
            assert comment_resp.status_code == 201, f"Failed to create comment: {comment_resp.text}"
            comment_id = comment_resp.json()["id"]
            print("PASS: Comment created via REST API to trigger notification")
            
            # User B should receive WS notification event
            event = ws_b.receive_json()
            assert event["event_type"] == "mention_notified"
            assert event["actor"] == user_a
            assert event["payload"]["mentioned_email"] == user_b
            assert event["payload"]["source_type"] == "comment"
            assert event["payload"]["source_id"] == comment_id
            print("PASS: User B successfully received correctly scoped mention notification event")

        print("=== ALL AGENT 2 TESTS PASSED ===")
    finally:
        db.close()

if __name__ == "__main__":
    test_mentions_endpoints()
