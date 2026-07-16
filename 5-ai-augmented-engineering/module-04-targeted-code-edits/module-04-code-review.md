# Module 04 Code Review — Team Collaboration

## Review Findings

### File: api/app/models.py

| Category | Finding | Severity | Evidence |
|----------|---------|----------|----------|
| Security | None | low | Parameterized SQLAlchemy ORM used. |
| Edge Cases | Missing database-level UniqueConstraint on `TeamMembership(team_id, user_email)`. Concurrent accepts could lead to duplicate memberships. | high | `class TeamMembership(Base):` (no unique constraint) |
| Error Handling | None | low | Standard database types. |
| Naming | Conventions match existing models. | low | `Team`, `TeamMembership`, `Invitation`, `Task`, `Comment` |
| Tests | Covered via API integration tests. | low | - |

---

### File: api/app/routers/teams.py

| Category | Finding | Severity | Evidence |
|----------|---------|----------|----------|
| Security | Checks roles correctly but the UUID validation check does not apply since team IDs are integer. | low | `/teams/{team_id}/invitations` uses `team_id: int` |
| Edge Cases | Allows multiple pending invitations for the same user to the same team. | medium | `invite_to_team` did not check `status == "pending"` |
| Error Handling | None | low | Checked team existence and raises 404. |
| Naming | Follows URL patterns and naming conventions. | low | `create_new_team`, `list_teams`, `remove_team`, `invite_to_team` |
| Tests | Exposes solid coverage. | low | Tested in `test_teams_verification.py` |

---

### File: api/app/routers/invitations.py

| Category | Finding | Severity | Evidence |
|----------|---------|----------|----------|
| Security | Verified user owns the invitation before acceptance. | low | Line 26: `if invitation.email != current_user:` |
| Edge Cases | None | low | Checked if membership already exists before inserting. |
| Error Handling | Silently swallowed WebSocket broadcast errors. | medium | Line 92: `except Exception: pass` |
| Naming | Variable naming and endpoint URLs are standard. | low | `accept_invitation` |
| Tests | Role privileges and cross-team accepts are well tested. | low | Tested in `test_role_management_auth.py` |

---

### File: api/app/crud.py

| Category | Finding | Severity | Evidence |
|----------|---------|----------|----------|
| Security | None | low | Uses SQLAlchemy query filters (safe against SQLi). |
| Edge Cases | Returns None if target membership doesn't exist. | low | `update_member_role` returns `None` |
| Error Handling | None | low | Clean db exception handling. |
| Naming | CRUD helper names are clean. | low | `create_team`, `get_team`, `create_invitation` |
| Tests | Fully covered by integration routers test. | low | - |

---

## FIX LIST — Priority Order
1. **[HIGH] Missing database unique constraint on `TeamMembership(team_id, user_email)`**
   - File: `api/app/models.py`
   - Fix: Added `UniqueConstraint("team_id", "user_email", name="uq_team_membership")` to `TeamMembership`'s `__table_args__`.
2. **[MEDIUM] Duplicate pending invitations allowed**
   - File: `api/app/routers/teams.py`
   - Fix: Added check in `invite_to_team` to verify if a pending invitation already exists for the email and team, raising 409 Conflict if so.
3. **[MEDIUM] Silent exception swallow in WebSocket broadcasting**
   - File: `api/app/routers/invitations.py`
   - Fix: Replaced `except Exception: pass` with proper `structlog` logging of errors.

---

## Follow-up Validation Prompts and Execution
The fixes were successfully implemented in:
1. `api/app/models.py`
2. `api/app/routers/teams.py`
3. `api/app/routers/invitations.py`

All tests pass successfully.
