# Team Collaboration Feature Decomposition Plan

This document outlines the **Top-Down Decomposition Plan** and **Medium-Grained Task Tree** (10 tasks total) for implementing the Team Collaboration feature in our FastAPI codebase.

---

## 1. Task Tree Overview

```
[Task 1: Team & Membership Models]
       ↓
[Task 2: Team CRUD Endpoints]
       ↓
[Task 3: Role & Permission Validation]
       ↓
[Task 4: Invitation Database Schema]
       ↓
[Task 5: Invitation API & Task]
       ↓
[Task 6: Acceptance & Joining Flow]
       ↓
[Task 7: Activity Feed Event Model]
       ↓
[Task 8: Activity Feed API]
       ↓
[Task 9: Audit Logging System]
       ↓
[Task 10: E2E Integration Verification]
```

*   **Critical Path**: Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6 → Task 10
*   **Riskiest Task**: **Task 6 (Invitation Acceptance Flow)**. It involves complex verification state transitions: validating token signature/expiry, updating user role/membership atomically within a database transaction, and preventing duplicate or expired tokens.

---

## 2. Interface Contracts

To prevent AI-agent integration errors and conflicting assumptions, the following interface contracts are established:

### Contract: Task 1 to Task 2 (Data Model & Schema)
*   **Task 1 Produces**:
    - Table `teams` with columns: `id` (int, PK), `name` (string, unique), `created_by` (string), `created_at` (datetime).
    - Table `team_memberships` with columns: `id` (int, PK), `team_id` (FK to `teams.id`, cascading delete), `user_email` (string), `role` (string: `'admin'`, `'member'`, `'viewer'`).
*   **Task 2 Expects**:
    - Table `team_memberships` exists exactly with those fields.
    - An automatic membership entry is created for the creator of a team as `'admin'` in the same transaction.
*   **Shared Contract Agreement**: Both tasks agree to refer to the join table as `team_memberships` (not `team_members` or `user_teams`) and roles as string enums (`'admin'`, `'member'`, `'viewer'`).

### Contract: Task 2 to Task 3 (Authorization)
*   **Task 2 Produces**:
    - Router file `api/app/routers/teams.py` prefix `/teams` with routes: `POST /teams`, `GET /teams`, `DELETE /teams/{id}`.
*   **Task 3 Expects**:
    - `teams.py` routes are already defined and require token authentication via `Depends(get_current_user)`.
*   **Shared Contract Agreement**: Authorization checks are decoupled into dependency guards in `auth.py` and applied to the existing router endpoints in `teams.py`.

### Contract: Task 4 to Task 5 & Task 6 (Invitation Lifecycle)
*   **Task 4 Produces**:
    - Table `team_invitations` with columns: `id` (int, PK), `team_id` (FK), `email` (string), `token` (string, unique), `status` (string: `'pending'`, `'accepted'`, `'expired'`), `expires_at` (datetime).
*   **Task 5 & Task 6 Expect**:
    - Invitation status is updated to `'accepted'` on successful accept, and memberships are populated accordingly.
*   **Shared Contract Agreement**: Tokens are unique and verification includes validating the `'pending'` status and comparing `expires_at` with the current time.

---

## 3. Decomposed Tasks Detail

### Task 1: Create Team and Membership Database Schema
- **Description**: Define SQLAlchemy models and database tables for `teams` and `team_memberships`.
- **Input Context**: [models.py](file:///c:/Users/shiva/CAW/api/app/models.py), [database.py](file:///c:/Users/shiva/CAW/api/app/database.py).
- **Expected Output**:
  - `Team` model in `api/app/models.py`.
  - `TeamMembership` model in `api/app/models.py`.
  - Alembic migration script in `api/alembic/versions/`.
- **Acceptance Criteria**: Database migration applies cleanly (`alembic upgrade head`). `Team` table has columns: `id` (int, PK), `name` (string, unique), `created_at` (datetime), `created_by` (string). `TeamMembership` has columns: `id` (int, PK), `team_id` (FK to teams.id), `user_email` (string), `role` (string: admin/member/viewer).
- **Dependencies**: None.

### Task 2: Implement Team CRUD Router and Endpoints
- **Description**: Add API endpoints for team management.
- **Input Context**: [main.py](file:///c:/Users/shiva/CAW/api/app/main.py), [schemas.py](file:///c:/Users/shiva/CAW/api/app/schemas.py), [crud.py](file:///c:/Users/shiva/CAW/api/app/crud.py).
- **Expected Output**:
  - New endpoints in `api/app/routers/teams.py` registered in `api/app/main.py`.
  - Pydantic schemas in `api/app/schemas.py` for Team requests and responses.
  - CRUD helper functions in `api/app/crud.py`.
- **Acceptance Criteria**:
  - `POST /teams` creates a team and adds the creator as `admin`.
  - `GET /teams` returns all teams current user belongs to.
  - `DELETE /teams/{id}` deletes the team (cascading memberships).
- **Dependencies**: Task 1.

### Task 3: Role and Permission Validation Middleware
- **Description**: Implement role-based dependency checks for endpoints.
- **Input Context**: [auth.py](file:///c:/Users/shiva/CAW/api/app/auth.py), [routers/teams.py](file:///c:/Users/shiva/CAW/api/app/routers/teams.py).
- **Expected Output**:
  - Permission dependency functions in `api/app/auth.py`.
- **Acceptance Criteria**: Endpoints requiring admin role return HTTP 403 Forbidden when called by a user with a `member` or `viewer` role in that team.
- **Dependencies**: Task 2.

### Task 4: Invitation Database Schema
- **Description**: Add tables and models for managing invitations.
- **Input Context**: [models.py](file:///c:/Users/shiva/CAW/api/app/models.py).
- **Expected Output**: `TeamInvitation` model and migration file.
- **Acceptance Criteria**: Alembic schema has `id` (int, PK), `team_id` (FK), `email` (string), `token` (string, unique), `status` (string: pending/accepted/expired), `expires_at` (datetime).
- **Dependencies**: Task 3.

### Task 5: Invitation API & Mock Delivery Task
- **Description**: API to invite team members and background celery task simulation.
- **Input Context**: [tasks.py](file:///c:/Users/shiva/CAW/api/app/tasks.py), [routers/teams.py](file:///c:/Users/shiva/CAW/api/app/routers/teams.py).
- **Expected Output**: `POST /teams/{id}/invitations` endpoint and a celery task.
- **Acceptance Criteria**: Sending invite returns HTTP 201, inserts invitation record, and triggers Celery task logging the mock email delivery.
- **Dependencies**: Task 4.

### Task 6: Invitation Acceptance Flow
- **Description**: Acceptance API endpoint to validate token and add user to team.
- **Input Context**: [routers/teams.py](file:///c:/Users/shiva/CAW/api/app/routers/teams.py).
- **Expected Output**: `POST /invitations/accept` receiving token.
- **Acceptance Criteria**: Valid token adds user as `member`, updates invitation status to `accepted`, invalid/expired token returns HTTP 400.
- **Dependencies**: Task 5.

### Task 7: Activity Feed Event Model
- **Description**: Models to represent activity log events.
- **Input Context**: [models.py](file:///c:/Users/shiva/CAW/api/app/models.py).
- **Expected Output**: `ActivityLog` SQLAlchemy model and migration.
- **Dependencies**: Task 1.

### Task 8: Activity Feed API Endpoints
- **Description**: API to fetch feed history for a team.
- **Input Context**: [routers/teams.py](file:///c:/Users/shiva/CAW/api/app/routers/teams.py).
- **Expected Output**: `GET /teams/{id}/activity` return feed events.
- **Dependencies**: Task 7.

### Task 9: System Audit Logging
- **Description**: Hook events like database transactions or endpoint invocations into audit logging.
- **Input Context**: [middleware.py](file:///c:/Users/shiva/CAW/api/app/middleware.py).
- **Expected Output**: Structured logs showing actor, action, source IP, timestamp, and target resource.
- **Dependencies**: Task 3.

### Task 10: E2E Integration Verification
- **Description**: End-to-end flow test suite.
- **Expected Output**: Integration test file in `api/tests/test_teams_e2e.py`.
- **Dependencies**: Task 6, Task 8.

---

## 4. Prompts for First 3 Tasks

### Prompt 1 (Task 1: Models & Migrations)
```text
Create SQLAlchemy database models and migrations for Teams and Team Memberships.

1. In api/app/models.py:
   - Add a class Team(Base):
     __tablename__ = "teams"
     id: Mapped[int] = mapped_column(Integer, primary_key=True)
     name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
     created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
     created_by: Mapped[str] = mapped_column(String, index=True, nullable=False)
     memberships: Mapped[list["TeamMembership"]] = relationship(back_populates="team", cascade="all, delete-orphan")

   - Add a class TeamMembership(Base):
     __tablename__ = "team_memberships"
     id: Mapped[int] = mapped_column(Integer, primary_key=True)
     team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
     user_email: Mapped[str] = mapped_column(String, index=True, nullable=False)
     role: Mapped[str] = mapped_column(String, nullable=False) # Roles must be one of: 'admin', 'member', 'viewer'
     team: Mapped["Team"] = relationship(back_populates="memberships")

2. Run 'alembic revision --autogenerate -m "add_teams_and_memberships"' and verify the migration file generates clean tables mapping to the SQLAlchemy definition.
3. Ensure base model imports in api/alembic/env.py are updated so autogenerate registers the models. Do not add any extra fields or use external packages.
```

### Prompt 2 (Task 2: Team CRUD Endpoints)
```text
Implement Team CRUD routes and CRUD helper methods in the FastAPI application.

1. In api/app/schemas.py, define Pydantic schemas:
   - TeamCreate: has field name (str)
   - TeamOut: has fields id (int), name (str), created_by (str), created_at (datetime)
   - TeamOutWithMembers: has fields id (int), name (str), created_by (str), created_at (datetime), memberships (list of members)

2. In api/app/crud.py, add functions:
   - create_team(db: Session, team_in: TeamCreate, user_email: str) -> models.Team
     (Should insert the Team and automatically create a TeamMembership for user_email with role 'admin' in a transaction)
   - get_user_teams(db: Session, user_email: str) -> list[models.Team]
   - delete_team(db: Session, team_id: int) -> bool

3. In api/app/routers/teams.py (New File):
   - POST /teams (Requires authentication, returns TeamOut)
   - GET /teams (Requires authentication, returns list[TeamOut])
   - DELETE /teams/{id} (Requires authentication, deletes team, returns {"ok": True})

4. Register the new router in api/app/main.py with prefix "/teams". Ensure all route dependencies verify user token using Depends(get_current_user).
```

### Prompt 3 (Task 3: Roles and Permissions)
```text
Implement role-based authorization guards for team routes.

1. In api/app/auth.py, implement helper dependency:
   - require_team_role(allowed_roles: list[str]):
     Returns a FastAPI dependency that takes team_id (int) and user_email (str = Depends(get_current_user)). It queries the team_memberships table to verify if the user has a membership on that team with one of the allowed_roles.
     If no membership exists, or the user's role is not in allowed_roles, raise HTTPException(status_code=403, detail="Permission denied").

2. In api/app/routers/teams.py, apply these guards:
   - DELETE /teams/{id} must require role 'admin'.
   - Add a new route GET /teams/{id} returning TeamOutWithMembers, which requires role 'admin', 'member', or 'viewer'.
```
