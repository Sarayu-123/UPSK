import sys
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
import app.crud as crud
import app.models as models
import app.schemas as schemas
from app.auth import create_access_token
from datetime import datetime, timezone

def setup_test_data(db):
    user_a = "user_a_comments@example.com"
    user_b = "user_b_comments@example.com"
    
    # Cleanup existing data
    db.query(models.Comment).delete()
    db.query(models.Task).delete()
    db.query(models.TeamMembership).filter(models.TeamMembership.user_email.in_([user_a, user_b])).delete(synchronize_session=False)
    db.query(models.Team).filter(models.Team.created_by.in_([user_a, user_b])).delete(synchronize_session=False)
    db.commit()
    
    # Create Team A under User A
    team_in = schemas.TeamCreate(name="Comments Team A")
    team_a = crud.create_team(db, team_in, user_a)
    
    # Generate tokens
    token_a = create_access_token({"sub": user_a})
    token_b = create_access_token({"sub": user_b})
    
    return team_a, token_a, token_b, user_a, user_b

def test_comments_endpoints():
    print("=== Running Comment Threads (Agent 1) Integration Tests ===")
    db = SessionLocal()
    client = TestClient(app)
    
    try:
        team_a, token_a, token_b, user_a, user_b = setup_test_data(db)
        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}
        
        # 1. Create a task for Team A
        print("Creating a task for testing...")
        task_resp = client.post(
            f"/teams/{team_a.id}/tasks",
            json={"title": "Sprint Planning Task"},
            headers=headers_a
        )
        assert task_resp.status_code == 201, f"Failed to create task: {task_resp.text}"
        task_id = task_resp.json()["id"]
        task_created_at = task_resp.json()["created_at"]
        print(f"PASS: Task created successfully (ID={task_id}, created_at={task_created_at})")
        
        # Verify timezone-aware created_at on task
        # Pydantic parsing datetime string with Z or timezone offset
        task_dt = datetime.fromisoformat(task_created_at.replace("Z", "+00:00"))
        assert task_dt.tzinfo is not None, "Task created_at must be timezone-aware"
        print("PASS: Task created_at is timezone-aware")

        # 2. Test: Team member can create comment
        print("Testing: Team member can create comment...")
        comment_resp = client.post(
            f"/tasks/{task_id}/comments",
            json={"body": "This is a main comment by User A"},
            headers=headers_a
        )
        assert comment_resp.status_code == 201, f"Failed to create comment: {comment_resp.text}"
        comment_id = comment_resp.json()["id"]
        comment_created_at = comment_resp.json()["created_at"]
        assert comment_resp.json()["author_email"] == user_a
        assert comment_resp.json()["body"] == "This is a main comment by User A"
        print(f"PASS: Team member successfully created comment (ID={comment_id})")

        # Verify timezone-aware created_at on comment
        comment_dt = datetime.fromisoformat(comment_created_at.replace("Z", "+00:00"))
        assert comment_dt.tzinfo is not None, "Comment created_at must be timezone-aware"
        print("PASS: Comment created_at is timezone-aware")

        # 3. Test: Non-member receives 403 on create comment
        print("Testing: Non-member receives 403 on create comment...")
        forbidden_resp = client.post(
            f"/tasks/{task_id}/comments",
            json={"body": "Unauthorized comment by User B"},
            headers=headers_b
        )
        assert forbidden_resp.status_code == 403, f"Expected 403, got {forbidden_resp.status_code}"
        print("PASS: Non-member creation blocked with 403")

        # 4. Test: Non-member receives 403 on read comments
        print("Testing: Non-member receives 403 on read comments...")
        forbidden_read = client.get(
            f"/tasks/{task_id}/comments",
            headers=headers_b
        )
        assert forbidden_read.status_code == 403, f"Expected 403, got {forbidden_read.status_code}"
        print("PASS: Non-member read blocked with 403")

        # 5. Test: Reply creation works
        print("Testing: Reply creation works...")
        reply_resp = client.post(
            f"/comments/{comment_id}/replies",
            json={"body": "This is a reply to the main comment"},
            headers=headers_a
        )
        assert reply_resp.status_code == 201, f"Failed to create reply: {reply_resp.text}"
        reply_id = reply_resp.json()["id"]
        assert reply_resp.json()["parent_id"] == comment_id
        assert reply_resp.json()["task_id"] == task_id
        print(f"PASS: Threaded reply created successfully (ID={reply_id}, parent_id={comment_id})")

        # 6. Test: Event emitted successfully via WebSocket
        print("Testing: WebSocket event emission...")
        with client.websocket_connect(f"/teams/ws?token={token_a}") as ws:
            # Trigger another reply via HTTP REST client
            client.post(
                f"/comments/{comment_id}/replies",
                json={"body": "WebSocket test reply"},
                headers=headers_a
            )
            
            # User A should receive the event
            event = ws.receive_json()
            assert event["event_type"] == "comment_created"
            assert event["team_id"] == team_a.id
            assert event["actor"] == user_a
            assert event["payload"]["body"] == "WebSocket test reply"
            assert event["payload"]["parent_id"] == comment_id
            print("PASS: Websocket broadcast event validated with correct payload")

        # 7. Test: Parent deletion cascades correctly
        print("Testing: Parent comment deletion cascade...")
        # Verify reply exists in DB first
        reply_in_db = db.query(models.Comment).filter(models.Comment.id == reply_id).first()
        assert reply_in_db is not None
        
        # Delete parent comment
        delete_resp = client.delete(
            f"/comments/{comment_id}",
            headers=headers_a
        )
        assert delete_resp.status_code == 200, f"Failed to delete comment: {delete_resp.text}"
        
        # Verify parent comment and reply are deleted from database
        parent_deleted = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
        reply_deleted = db.query(models.Comment).filter(models.Comment.id == reply_id).first()
        assert parent_deleted is None, "Parent comment was not deleted"
        assert reply_deleted is None, "Reply comment was not cascade deleted"
        print("PASS: Parent comment deletion cascade-deleted the reply")

        # 8. Test: Task deletion cascades comments
        print("Testing: Task deletion cascade...")
        # Create a new comment on task
        c_resp = client.post(
            f"/tasks/{task_id}/comments",
            json={"body": "Another test comment to check task cascade"},
            headers=headers_a
        )
        assert c_resp.status_code == 201
        new_comment_id = c_resp.json()["id"]
        
        # Verify comment exists
        comment_in_db = db.query(models.Comment).filter(models.Comment.id == new_comment_id).first()
        assert comment_in_db is not None
        
        # Delete task directly in DB or via cascading team delete
        # Since we cascade delete team -> tasks -> comments, let's delete the team
        team_delete_resp = client.delete(
            f"/teams/{team_a.id}",
            headers=headers_a
        )
        assert team_delete_resp.status_code == 200
        
        # Verify task and comment are gone
        task_in_db = db.query(models.Task).filter(models.Task.id == task_id).first()
        comment_gone = db.query(models.Comment).filter(models.Comment.id == new_comment_id).first()
        assert task_in_db is None, "Task was not deleted on team deletion"
        assert comment_gone is None, "Comment was not cascade deleted on task deletion"
        print("PASS: Team deletion cascade-deleted tasks, which cascade-deleted comments successfully")

        print("=== ALL AGENT 1 TESTS PASSED ===")
    finally:
        db.close()

if __name__ == "__main__":
    test_comments_endpoints()
