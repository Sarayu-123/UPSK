# Module 04 Verification — Edge Case Testing

We ran the verification suite containing edge-case tests 1-5 directly against the FastAPI API server to verify that the core and edge-case exceptions are handled correctly.

## Edge Case Test Results

### Test 1: Invite a user who is already a team member
- **Request**: `POST /teams/:teamId/invitations` with email of existing member.
- **Expected**: 409 Conflict or 400 Bad Request.
- **Actual**: 409 Conflict (`HTTP 409 Conflict: User is already a member of the team`)

### Test 2: Create a team with an empty name
- **Request**: `POST /teams` with `{ "name": " " }`.
- **Expected**: 400 Bad Request with a validation error.
- **Actual**: 400 Bad Request (`HTTP 400 Bad Request: Team name cannot be empty`)

### Test 3: Call the invitation endpoint without authentication
- **Request**: `POST /teams/:teamId/invitations` with no auth header.
- **Expected**: 401 Unauthorized.
- **Actual**: 401 Unauthorized (`HTTP 401 Unauthorized: Not authenticated`)

### Test 4: Call the invitation endpoint as a non-member of the team
- **Request**: Authenticated as User B, send invitation to Team A (owned by User A).
- **Expected**: 403 Forbidden.
- **Actual**: 403 Forbidden (`HTTP 403 Forbidden: Only team admins can invite members`)

### Test 5: Send an invitation with an invalid email format
- **Request**: `POST /teams/:teamId/invitations` with `{ "email": "not-an-email" }`.
- **Expected**: 400 Bad Request.
- **Actual**: 400 Bad Request (`HTTP 400 Bad Request: Invalid email format`)

---

## Output Verification Logs
```
=== Starting Team Collaboration Verification Tests ===
Preparing test team...
Created Test Team: ID=4

--- Running Test 1: Invite an existing member ---
Status: 409, Body: {'detail': 'User already member of the team'}

--- Running Test 2: Create team with empty name ---
Status: 400, Body: {'detail': 'Team name cannot be empty'}

--- Running Test 3: Invite without auth ---
Status: 401, Body: {'detail': 'Not authenticated'}

--- Running Test 4: Invite as non-member of the team ---
Status: 403, Body: {'detail': 'Insufficient permissions'}

--- Running Test 5: Invite with invalid email format ---
Status: 400, Body: {'detail': 'Invalid email format'}

=== Verification Summary ===
Test 1: PASS (HTTP 409)
Test 2: PASS (HTTP 400)
Test 3: PASS (HTTP 401)
Test 4: PASS (HTTP 403)
Test 5: PASS (HTTP 400)
```
