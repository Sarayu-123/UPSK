import sys
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
import app.crud as crud
import app.models as models
import app.schemas as schemas
from app.auth import create_access_token

def setup_test_data(db):
    user_a = "user_a_ws@example.com"
    user_b = "user_b_ws@example.com"
    
    # Clean up existing teams and memberships for these users if they exist
    db.query(models.TeamMembership).filter(models.TeamMembership.user_email.in_([user_a, user_b])).delete(synchronize_session=False)
    db.query(models.Team).filter(models.Team.created_by.in_([user_a, user_b])).delete(synchronize_session=False)
    db.commit()
    
    # Create Team A under User A
    team_in = schemas.TeamCreate(name="WS Team A")
    existing = db.query(models.Team).filter(models.Team.name == "WS Team A").first()
    if existing:
        db.delete(existing)
        db.commit()
        
    team_a = crud.create_team(db, team_in, user_a)
    
    # Generate tokens
    token_a = create_access_token({"sub": user_a})
    token_b = create_access_token({"sub": user_b})
    
    return team_a, token_a, token_b

def test_websocket_endpoints():
    print("=== Running WebSocket Activity Feed Tests ===")
    db = SessionLocal()
    try:
        team_a, token_a, token_b = setup_test_data(db)
        client = TestClient(app)
        
        # Test 1: Missing token (V2)
        print("Testing missing token...")
        try:
            with client.websocket_connect("/teams/ws") as ws:
                ws.receive_text()
            raise AssertionError("Connection without token succeeded but should have failed")
        except Exception as e:
            if isinstance(e, AssertionError):
                raise
            print(f"PASS: Connection without token rejected ({type(e).__name__})")
            
        # Test 2: Invalid token (V2)
        print("Testing invalid token...")
        try:
            with client.websocket_connect("/teams/ws?token=invalid_token") as ws:
                ws.receive_text()
            raise AssertionError("Connection with invalid token succeeded but should have failed")
        except Exception as e:
            if isinstance(e, AssertionError):
                raise
            print(f"PASS: Connection with invalid token rejected ({type(e).__name__})")

        # Test 3: Valid JWT connect (V1) and event scoping (V3)
        print("Testing connection with valid token and scoping...")
        
        # User A connects (is member of Team A)
        with client.websocket_connect(f"/teams/ws?token={token_a}") as ws_a:
            print("PASS: User A authenticated and connected")
            
            # User B connects (is NOT member of Team A)
            with client.websocket_connect(f"/teams/ws?token={token_b}") as ws_b:
                print("PASS: User B authenticated and connected")
                
                # Trigger invitation on Team A using User A token via REST client
                headers_a = {"Authorization": f"Bearer {token_a}"}
                post_resp = client.post(
                    f"/teams/{team_a.id}/invitations",
                    json={"email": "invited_user@example.com"},
                    headers=headers_a
                )
                assert post_resp.status_code == 201, f"Failed to invite: {post_resp.text}"
                print("PASS: Invitation created successfully")
                
                # User A should receive the invitation_created event
                event_a = ws_a.receive_json()
                print(f"User A received event: {event_a}")
                assert event_a["event_type"] == "invitation_created"
                assert event_a["team_id"] == team_a.id
                assert event_a["actor"] == "user_a_ws@example.com"
                assert event_a["payload"]["email"] == "invited_user@example.com"
                print("PASS: User A received correctly scoped event")
                
                # User B should NOT receive the event (scoping validation)
                ws_b.send_text("ping")
                resp_b = ws_b.receive_text()
                assert resp_b == "pong", "User B connection dead or blocked"
                print("PASS: User B did not receive unauthorized Team A event (Scoping is secure!)")

        print("=== ALL TESTS PASSED ===")
    finally:
        db.close()

if __name__ == "__main__":
    test_websocket_endpoints()
