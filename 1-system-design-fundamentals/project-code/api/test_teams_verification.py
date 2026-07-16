from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
import sys

BASE_URL = ""


def login(username, password):
    resp = client.post(
        f"{BASE_URL}/auth/login",
        data={"username": username, "password": password}
    )
    if resp.status_code != 200:
        print(f"Login failed for {username}: {resp.status_code} - {resp.text}")
        sys.exit(1)
    return resp.json()["access_token"]


def run_tests():
    print("=== Starting Team Collaboration Verification Tests ===")

    # 0. Authenticate users
    token_a = login("admin@example.com", "password123")
    token_b = login("user_b@example.com", "password123")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Helper: Create a team for testing
    print("\nPreparing test team...")
    team_name = "Verification Test Team"
    # Delete if exists
    # First, list teams for User A
    list_resp = client.get(f"{BASE_URL}/teams/", headers=headers_a)
    assert list_resp.status_code == 200
    for team in list_resp.json():
        if team["name"] == team_name:
            client.delete(f"{BASE_URL}/teams/{team['id']}", headers=headers_a)

    # Create fresh
    create_resp = client.post(
        f"{BASE_URL}/teams/",
        json={"name": team_name},
        headers=headers_a
    )
    assert create_resp.status_code == 201, f"Failed to create team: {create_resp.text}"
    team_id = create_resp.json()["id"]
    print(f"Created Test Team: ID={team_id}")

    results = {}

    # -------------------------------------------------------------
    # Test 1: Invite a user who is already a team member (User A is admin/member)
    # -------------------------------------------------------------
    print("\n--- Running Test 1: Invite an existing member ---")
    resp_t1 = client.post(
        f"{BASE_URL}/teams/{team_id}/invitations",
        json={"email": "admin@example.com"},
        headers=headers_a
    )
    print(f"Status: {resp_t1.status_code}, Body: {resp_t1.json()}")
    results["Test 1"] = {
        "status": resp_t1.status_code,
        "body": resp_t1.json(),
        "passed": resp_t1.status_code in [400, 409]
    }

    # -------------------------------------------------------------
    # Test 2: Create a team with an empty name
    # -------------------------------------------------------------
    print("\n--- Running Test 2: Create team with empty name ---")
    resp_t2 = client.post(
        f"{BASE_URL}/teams/",
        json={"name": "   "},
        headers=headers_a
    )
    print(f"Status: {resp_t2.status_code}, Body: {resp_t2.json()}")
    results["Test 2"] = {
        "status": resp_t2.status_code,
        "body": resp_t2.json(),
        "passed": resp_t2.status_code == 400
    }

    # -------------------------------------------------------------
    # Test 3: Call the invitation endpoint without authentication
    # -------------------------------------------------------------
    print("\n--- Running Test 3: Invite without auth ---")
    resp_t3 = client.post(
        f"{BASE_URL}/teams/{team_id}/invitations",
        json={"email": "somebody@example.com"}
    )
    print(f"Status: {resp_t3.status_code}, Body: {resp_t3.json() if resp_t3.status_code == 401 else resp_t3.text}")
    results["Test 3"] = {
        "status": resp_t3.status_code,
        "passed": resp_t3.status_code == 401
    }

    # -------------------------------------------------------------
    # Test 4: Call the invitation endpoint as a non-member/non-admin
    # -------------------------------------------------------------
    print("\n--- Running Test 4: Invite as non-member of the team ---")
    resp_t4 = client.post(
        f"{BASE_URL}/teams/{team_id}/invitations",
        json={"email": "other@example.com"},
        headers=headers_b
    )
    print(f"Status: {resp_t4.status_code}, Body: {resp_t4.json()}")
    results["Test 4"] = {
        "status": resp_t4.status_code,
        "body": resp_t4.json(),
        "passed": resp_t4.status_code == 403
    }

    # -------------------------------------------------------------
    # Test 5: Send an invitation with an invalid email format
    # -------------------------------------------------------------
    print("\n--- Running Test 5: Invite with invalid email format ---")
    resp_t5 = client.post(
        f"{BASE_URL}/teams/{team_id}/invitations",
        json={"email": "not-an-email"},
        headers=headers_a
    )
    print(f"Status: {resp_t5.status_code}, Body: {resp_t5.json()}")
    results["Test 5"] = {
        "status": resp_t5.status_code,
        "body": resp_t5.json(),
        "passed": resp_t5.status_code == 400
    }

    print("\n=== Verification Summary ===")
    all_passed = True
    for test_name, res in results.items():
        pass_str = "PASS" if res["passed"] else "FAIL"
        print(f"{test_name}: {pass_str} (HTTP {res['status']})")
        if not res["passed"]:
            all_passed = False

    # Cleanup
    client.delete(f"{BASE_URL}/teams/{team_id}", headers=headers_a)

    return all_passed, results


if __name__ == "__main__":
    success, results = run_tests()
    sys.exit(0 if success else 1)
