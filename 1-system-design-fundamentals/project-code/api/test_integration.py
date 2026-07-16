import sys
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
import app.crud as crud
import app.models as models
import app.schemas as schemas
from app.auth import create_access_token
import logging
logging.getLogger("sqlalchemy.engine").disabled = True
from datetime import datetime

def setup_test_data(db):
    user_a = "user_a_int@example.com"
    user_b = "user_b_int@example.com"
    
    # Cleanup
    db.query(models.AuditLog).delete()
    db.query(models.Comment).delete()
    db.query(models.Task).delete()
    db.query(models.TeamMembership).filter(models.TeamMembership.user_email.in_([user_a, user_b])).delete(synchronize_session=False)
    db.query(models.Team).filter(models.Team.created_by.in_([user_a, user_b])).delete(synchronize_session=False)
    db.commit()
    
    # Create Team A under User A
    team_in = schemas.TeamCreate(name="Integration Team A")
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

def test_sprint_integration_flow():
    print("=== Running Parallel Sprint Integrated E2E Tests ===")
    db = SessionLocal()
    with TestClient(app) as client:
        try:
            team_a, token_a, token_b, user_a, user_b = setup_test_data(db)
            headers_a = {"Authorization": f"Bearer {token_a}"}
            headers_b = {"Authorization": f"Bearer {token_b}"}
            
            # User B connects to WebSocket activity feed to listen for mention notifications
            with client.websocket_connect(f"/teams/ws?token={token_b}") as ws_b:
                print("PASS: User B connected to WS")

                # 1. User A creates a task on Team A
                print("User A creating task...")
                task_resp = client.post(
                    f"/teams/{team_a.id}/tasks",
                    json={"title": "E2E Feature Integration"},
                    headers=headers_a
                )
                assert task_resp.status_code == 201
                task_id = task_resp.json()["id"]
                print("PASS: Task created successfully")

                # 2. User A comments on the task, mentioning User B
                print("User A creating comment with mention...")
                comment_resp = client.post(
                    f"/tasks/{task_id}/comments",
                    json={"body": "Hey @user_b_int, check if this is working!"},
                    headers=headers_a
                )
                assert comment_resp.status_code == 201
                comment_id = comment_resp.json()["id"]
                print("PASS: Comment created successfully")

                # 3. Verify User B receives WebSocket mention notification
                print("Waiting for WebSocket mention notification event for User B...")
                event = ws_b.receive_json()
                assert event["event_type"] == "mention_notified"
                assert event["actor"] == user_a
                assert event["payload"]["mentioned_email"] == user_b
                assert event["payload"]["source_id"] == comment_id
                print("PASS: WebSocket mention notification validated successfully!")

            # 4. Verify Audit Logs recorded in DB via Audit Logs REST API
            print("Fetching and verifying audit logs...")
            audit_resp = client.get(
                f"/teams/{team_a.id}/audit-logs",
                headers=headers_a
            )
            assert audit_resp.status_code == 200
            logs = audit_resp.json()
            print("LOGS IN TEST:", logs)
            
            # We expect 2 logs: task creation (earlier) and comment creation (later)
            # Order is desc timestamp
            assert len(logs) == 2
            assert logs[0]["action"] == "create"
            assert logs[0]["resource_type"] == "comment"
            assert logs[0]["resource_id"] == comment_id
            assert logs[0]["actor_email"] == user_a

            assert logs[1]["action"] == "create"
            assert logs[1]["resource_type"] == "task"
            assert logs[1]["resource_id"] == task_id
            assert logs[1]["actor_email"] == user_a
            print("PASS: Audit log entries for task and comment creation verified successfully!")

            print("=== ALL INTEGRATION E2E TESTS PASSED ===")
        finally:
            db.close()

def test_capstone_journey():
    print("=== Running Capstone 6-Step Integration Journey ===")
    db = SessionLocal()
    with TestClient(app) as client:
        # Cleanup test users data to ensure clean state
        user_a = "user_a_capstone@example.com"
        user_b = "user_b_capstone@example.com"
        db.query(models.AuditLog).delete()
        db.query(models.Comment).delete()
        db.query(models.Task).delete()
        db.query(models.TeamMembership).filter(models.TeamMembership.user_email.in_([user_a, user_b])).delete(synchronize_session=False)
        db.query(models.Team).filter(models.Team.created_by.in_([user_a, user_b])).delete(synchronize_session=False)
        db.query(models.Invitation).filter(models.Invitation.email == user_b).delete(synchronize_session=False)
        db.commit()
        
        # Setup auth tokens
        token_a = create_access_token({"sub": user_a})
        token_b = create_access_token({"sub": user_b})
        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}
        
        try:
            # Step 1: User A creates a team
            team_resp = client.post(
                "/teams/",
                json={"name": "Capstone Team"},
                headers=headers_a
            )
            assert team_resp.status_code == 201, f"Failed to create team: {team_resp.text}"
            team_id = team_resp.json()["id"]
            print("PASS: Step 1 - User A created team successfully")
            
            # Step 2: User A invites User B to the team as a member
            invite_resp = client.post(
                f"/teams/{team_id}/invitations",
                json={"email": user_b},
                headers=headers_a
            )
            assert invite_resp.status_code == 201, f"Failed to send invitation: {invite_resp.text}"
            invitation_id = invite_resp.json()["id"]
            print("PASS: Step 2 - User A invited User B successfully")
            
            # Step 3: User B accepts the invitation
            accept_resp = client.post(
                f"/invitations/{invitation_id}/accept",
                headers=headers_b
            )
            assert accept_resp.status_code == 200, f"Failed to accept invitation: {accept_resp.text}"
            print("PASS: Step 3 - User B accepted invitation successfully")
            
            # Connect User A to WebSocket feed to verify they see User B's comment
            with client.websocket_connect(f"/teams/ws?token={token_a}") as ws_a:
                print("PASS: User A connected to WebSocket activity feed")
                
                # Step 4: User B comments on a task in the team, with an @mention of User A
                # First, User B creates a task
                task_resp = client.post(
                    f"/teams/{team_id}/tasks",
                    json={"title": "Capstone Task"},
                    headers=headers_b
                )
                assert task_resp.status_code == 201, f"Failed to create task: {task_resp.text}"
                task_id = task_resp.json()["id"]
                
                # User B comments on the task and @mentions User A
                comment_resp = client.post(
                    f"/tasks/{task_id}/comments",
                    json={"body": "Hello @user_a_capstone check this out!"},
                    headers=headers_b
                )
                assert comment_resp.status_code == 201, f"Failed to create comment: {comment_resp.text}"
                comment_id = comment_resp.json()["id"]
                print("PASS: Step 4 - User B commented on task with @mention of User A")
                
                # Step 5: User A checks the activity feed and sees User B's comment
                events = [ws_a.receive_json(), ws_a.receive_json()]
                event_types = [e["event_type"] for e in events]
                assert "comment_created" in event_types, f"Expected comment_created event, got {event_types}"
                assert "mention_notified" in event_types, f"Expected mention_notified event, got {event_types}"
                
                # Check properties of the comment_created event
                comment_event = next(e for e in events if e["event_type"] == "comment_created")
                assert comment_event["actor"] == user_b
                assert comment_event["payload"]["id"] == comment_id
                print("PASS: Step 5 - User A saw User B's comment in activity feed via WebSocket")
                
            # Step 6: An admin (User A) checks the audit log and sees entries for:
            # team creation, invitation sent, invitation accepted, comment posted.
            audit_resp = client.get(
                f"/teams/{team_id}/audit-logs",
                headers=headers_a
            )
            assert audit_resp.status_code == 200, f"Failed to get audit logs: {audit_resp.text}"
            logs = audit_resp.json()
            
            actions = [(l["resource_type"], l["action"]) for l in logs]
            print(f"Audit log actions recorded: {actions}")
            
            assert ("team", "create") in actions, "Missing team creation audit log entry"
            assert ("invitation", "invite") in actions, "Missing invitation sent audit log entry"
            assert ("invitation", "accept") in actions, "Missing invitation accepted audit log entry"
            assert ("comment", "create") in actions, "Missing comment creation audit log entry"
            print("PASS: Step 6 - Admin successfully verified all audit log entries!")
            
        finally:
            db.close()

if __name__ == "__main__":
    test_sprint_integration_flow()
    test_capstone_journey()
