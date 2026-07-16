"""
Role Management Authorization Tests — complete 13 test cases plus regression and cross-team checks.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

BASE_URL = ""


import random

SESSION_IP = f"10.0.{random.randint(1, 254)}.{random.randint(1, 254)}"


def login(username, password):
    resp = client.post(
        f"{BASE_URL}/auth/login",
        data={"username": username, "password": password},
        headers={"X-Forwarded-For": SESSION_IP}
    )
    if resp.status_code != 200:
        print(f"[FATAL] Login failed for {username}: {resp.status_code}")
        sys.exit(1)
    return resp.json()["access_token"]


def auth(token):
    return {
        "Authorization": f"Bearer {token}",
        "X-Forwarded-For": SESSION_IP
    }


def create_team(token, name):
    resp = client.post(f"{BASE_URL}/teams/", json={"name": name}, headers=auth(token))
    assert resp.status_code == 201, f"create_team failed: {resp.text}"
    return resp.json()["id"]


def invite_and_accept(admin_token, team_id, email, member_token):
    inv = client.post(f"{BASE_URL}/teams/{team_id}/invitations", json={"email": email}, headers=auth(admin_token))
    assert inv.status_code == 201, f"invite failed: {inv.text}"
    inv_id = inv.json()["id"]
    acc = client.post(f"{BASE_URL}/invitations/{inv_id}/accept", headers=auth(member_token))
    assert acc.status_code == 200, f"accept failed: {acc.text}"


def put_role(token, team_id, target_email, role):
    return client.put(
        f"{BASE_URL}/teams/{team_id}/members/{target_email}",
        json={"role": role},
        headers=auth(token)
    )


def record(results, name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    results[name] = status
    print(f"  [{status}] {name}" + (f" - {detail}" if detail else ""))


def test_role_management_privileges():
    print("\n=== Running Role Management & Privilege Escalation Tests ===\n")
    
    # 0. Login
    token_owner  = login("admin@example.com", "password123")
    token_admin  = login("admin_user@example.com", "password123")
    token_member = login("member@example.com", "password123")
    token_viewer = login("viewer@example.com", "password123")
    
    # Setup team 1
    # Clean up
    for name in ["RoleTest-Team1", "RoleTest-Team2"]:
        existing = client.get(f"{BASE_URL}/teams/", headers=auth(token_owner))
        for t in existing.json():
            if t["name"] == name:
                client.delete(f"{BASE_URL}/teams/{t['id']}", headers=auth(token_owner))
                
    team1_id = create_team(token_owner, "RoleTest-Team1")
    team2_id = create_team(token_owner, "RoleTest-Team2")
    
    # Add actors to team1
    invite_and_accept(token_owner, team1_id, "admin_user@example.com", token_admin)
    put_role(token_owner, team1_id, "admin_user@example.com", "admin")
    
    invite_and_accept(token_owner, team1_id, "member@example.com", token_member)
    
    invite_and_accept(token_owner, team1_id, "viewer@example.com", token_viewer)
    put_role(token_owner, team1_id, "viewer@example.com", "viewer")
    
    results = {}
    
    # --- 13 SPECIFIC VERIFY TESTS ---
    
    # 1. Viewer tries to update own role to admin: 403
    resp = put_role(token_viewer, team1_id, "viewer@example.com", "admin")
    record(results, "Viewer tries to update own role to admin", resp.status_code == 403, f"status={resp.status_code}")
    
    # 2. Viewer tries to update another member's role: 403
    resp = put_role(token_viewer, team1_id, "member@example.com", "admin")
    record(results, "Viewer tries to update another member's role", resp.status_code == 403, f"status={resp.status_code}")
    
    # 3. Member tries to update own role to admin: 403
    resp = put_role(token_member, team1_id, "member@example.com", "admin")
    record(results, "Member tries to update own role to admin", resp.status_code == 403, f"status={resp.status_code}")
    
    # 4. Member tries to update another member's role: 403
    resp = put_role(token_member, team1_id, "viewer@example.com", "admin")
    record(results, "Member tries to update another member's role", resp.status_code == 403, f"status={resp.status_code}")
    
    # 5. Admin updates a viewer to member: 200
    resp = put_role(token_admin, team1_id, "viewer@example.com", "member")
    record(results, "Admin updates a viewer to member", resp.status_code == 200, f"status={resp.status_code}")
    # Restore
    put_role(token_owner, team1_id, "viewer@example.com", "viewer")
    
    # 6. Admin updates a member to viewer: 200
    resp = put_role(token_admin, team1_id, "member@example.com", "viewer")
    record(results, "Admin updates a member to viewer", resp.status_code == 200, f"status={resp.status_code}")
    # Restore
    put_role(token_owner, team1_id, "member@example.com", "member")
    
    # 7. Admin tries to promote member to owner: 403
    resp = put_role(token_admin, team1_id, "member@example.com", "owner")
    record(results, "Admin tries to promote member to owner", resp.status_code == 403, f"status={resp.status_code}")
    
    # 8. Admin tries to update own role: 403
    resp = put_role(token_admin, team1_id, "admin_user@example.com", "viewer")
    record(results, "Admin tries to update own role", resp.status_code == 403, f"status={resp.status_code}")
    
    # 9. Owner updates a member to admin: 200
    resp = put_role(token_owner, team1_id, "member@example.com", "admin")
    record(results, "Owner updates a member to admin", resp.status_code == 200, f"status={resp.status_code}")
    # Restore
    put_role(token_owner, team1_id, "member@example.com", "member")
    
    # 10. Owner promotes a member to owner: 200
    resp = put_role(token_owner, team1_id, "member@example.com", "owner")
    record(results, "Owner promotes a member to owner", resp.status_code == 200, f"status={resp.status_code}")
    # Restore
    put_role(token_owner, team1_id, "member@example.com", "member")
    
    # 11. Owner tries to update own role: 403
    resp = put_role(token_owner, team1_id, "admin@example.com", "admin")
    record(results, "Owner tries to update own role", resp.status_code == 403, f"status={resp.status_code}")
    
    # 12. Any user sends role value "superadmin": 400
    resp = put_role(token_owner, team1_id, "member@example.com", "superadmin")
    record(results, "Any user sends role value 'superadmin'", resp.status_code == 400, f"status={resp.status_code}")
    
    # 13. Any user sends role value "": 400
    resp = put_role(token_owner, team1_id, "member@example.com", "")
    record(results, "Any user sends role value ''", resp.status_code == 400, f"status={resp.status_code}")
    
    # --- CROSS-TEAM & REGRESSION ---
    
    # 14. Cross-team role update blocked
    resp = put_role(token_owner, team2_id, "member@example.com", "viewer")
    record(results, "Cross-team role update blocked", resp.status_code in (403, 404), f"status={resp.status_code}")
    
    # Summary
    print("\n=== Summary ===")
    passed = sum(1 for v in results.values() if v == "PASS")
    total  = len(results)
    for name, status in results.items():
        print(f"  {status:4s}  {name}")
    print(f"\n{passed}/{total} tests passed")
    assert passed == total, f"Only {passed}/{total} role privilege tests passed"


if __name__ == "__main__":
    test_role_management_privileges()
