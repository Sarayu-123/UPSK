import sys
from app.services.audit_logger import record_audit_log
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
import app.crud as crud
import app.models as models
import app.schemas as schemas
from app.auth import create_access_token
from datetime import datetime

def setup_test_data(db):
    user_a = "user_a_audit@example.com"
    user_b = "user_b_audit@example.com"
    
    # Cleanup
    db.query(models.AuditLog).delete()
    db.query(models.Comment).delete()
    db.query(models.Task).delete()
    db.query(models.TeamMembership).filter(models.TeamMembership.user_email.in_([user_a, user_b])).delete(synchronize_session=False)
    db.query(models.Team).filter(models.Team.created_by.in_([user_a, user_b])).delete(synchronize_session=False)
    db.commit()
    
    # Create Team A under User A
    team_in = schemas.TeamCreate(name="Audit Team A")
    team_a = crud.create_team(db, team_in, user_a)
    
    # Generate tokens
    token_a = create_access_token({"sub": user_a})
    token_b = create_access_token({"sub": user_b})
    
    return team_a, token_a, token_b, user_a, user_b

def test_audit_endpoints():
    print("=== Running Audit Logging (Agent 3) Tests ===")
    db = SessionLocal()
    client = TestClient(app)
    try:
        team_a, token_a, token_b, user_a, user_b = setup_test_data(db)
        
        # 1. Manually write audit log and fetch
        print("Testing manual audit log insertion and retrieval...")
        record_audit_log(
            db=db,
            action="create",
            resource_type="team",
            resource_id=team_a.id,
            actor_email=user_a,
            details={"team_name": team_a.name}
        )
        
        # Query via endpoint
        resp = client.get(
            f"/teams/{team_a.id}/audit-logs",
            headers={
                "Authorization": f"Bearer {token_a}"
            }
        )
        assert resp.status_code == 200, f"Failed to get audit logs: {resp.text}"
        logs = resp.json()
        assert len(logs) == 1
        assert logs[0]["action"] == "create"
        assert logs[0]["resource_type"] == "team"
        assert logs[0]["resource_id"] == team_a.id
        assert logs[0]["actor_email"] == user_a
        assert logs[0]["details"]["team_name"] == "Audit Team A"
        print("PASS: Audit log entry successfully created and retrieved")

        # 2. Test: Non-member cannot read audit logs
        print("Testing: Non-member cannot read audit logs...")
        forbidden_read = client.get(
            f"/teams/{team_a.id}/audit-logs",
            headers={
                "Authorization": f"Bearer {token_b}"
            }
        )
        assert forbidden_read.status_code == 403
        print("PASS: Non-member read blocked with 403")

        # 3. Test: Timestamps are timezone-aware
        print("Testing: Timestamp timezone awareness...")
        ts_str = logs[0]["timestamp"]
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        assert dt.tzinfo is not None, "Timestamp must be timezone-aware"
        print("PASS: Audit log timestamp is timezone-aware")

        print("=== ALL AGENT 3 TESTS PASSED ===")
    finally:
        db.close()

if __name__ == "__main__":
    test_audit_endpoints()
