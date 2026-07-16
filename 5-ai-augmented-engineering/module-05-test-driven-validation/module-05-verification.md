# Module 05 Verification — WebSocket Activity Feed Tests

We ran the WebSocket activity feed verification suite (`test_websocket.py`) directly inside the API container to verify connection lifecycle, token authentication, and secure event scoping.

## Test Results

### Test 1: Missing Token
- **Scenario**: Connect to WebSocket endpoint `/teams/ws` without a JWT token.
- **Expected**: Rejected with HTTP 400 or WebSocket policy violation.
- **Actual**: Connection rejected (fastapi.testclient.WebSocketTestSession closed).
- **Result**: PASS

### Test 2: Invalid Token
- **Scenario**: Connect to WebSocket endpoint with an invalid token: `/teams/ws?token=invalid_token`.
- **Expected**: Rejected.
- **Actual**: Connection rejected.
- **Result**: PASS

### Test 3: Valid JWT Connection and Event Scoping
- **Scenario**:
  - Connect User A (member of Team A) using a valid JWT.
  - Connect User B (not member of Team A) using a valid JWT.
  - User A triggers an invitation on Team A.
- **Expected**:
  - User A receives the `invitation_created` event broadcast.
  - User B does NOT receive the event (secured scoping).
- **Actual**:
  - User A authenticated and connected.
  - User B authenticated and connected.
  - User A successfully received the correct scoped event:
    ```json
    {
      "event_type": "invitation_created",
      "team_id": 5,
      "actor": "user_a_ws@example.com",
      "payload": {
        "id": 4,
        "email": "invited_user@example.com",
        "invited_by": "user_a_ws@example.com",
        "status": "pending"
      }
    }
    ```
  - User B did not receive any unauthorized event. User B responded to ping-pong request normally, proving their connection remained active and secure.
- **Result**: PASS

---

## Output Verification Logs
```
=== Running WebSocket Activity Feed Tests ===
Testing missing token...
PASS: Connection without token rejected (WebSocketDisconnect)
Testing invalid token...
PASS: Connection with invalid token rejected (WebSocketDisconnect)
Testing connection with valid token and scoping...
PASS: User A authenticated and connected
PASS: User B authenticated and connected
PASS: Invitation created successfully
User A received event: {'event_type': 'invitation_created', 'team_id': 5, 'actor': 'user_a_ws@example.com', 'timestamp': '2026-06-12T04:14:57.464360+00:00', 'payload': {'id': 4, 'email': 'invited_user@example.com', 'invited_by': 'user_a_ws@example.com', 'status': 'pending'}}
PASS: User A received correctly scoped event
PASS: User B did not receive unauthorized Team A event (Scoping is secure!)
=== ALL TESTS PASSED ===
```
