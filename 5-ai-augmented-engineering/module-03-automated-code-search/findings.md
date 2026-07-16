# Security and Architecture Review Findings

This document contains the security, architecture, and quality review findings for the LinkOps API codebase across all modules (02 through 06).

---

## Security Review

### 1. Auth Check Audit
Every endpoint has been mapped to verify that the requester is both authenticated and authorized:

| ENDPOINT | AUTH CHECK | AUTHORIZATION CHECK | STATUS |
| :--- | :--- | :--- | :--- |
| **POST** `/teams` | `get_current_user` middleware | Any authenticated user | **OK** |
| **GET** `/teams` | `get_current_user` middleware | Returns only teams where user is member | **OK** |
| **DELETE** `/teams/:id` | `get_current_user` middleware | `is_team_admin(team_id, current_user)` check | **OK** |
| **POST** `/teams/:id/invitations` | `get_current_user` middleware | `is_team_admin(team_id, current_user)` check | **OK** |
| **PUT** `/teams/:id/members/:user_email` | `get_current_user` middleware | Requester must be `admin` or `owner` | **OK** |
| **POST** `/invitations/:id/accept` | `get_current_user` middleware | Token matching accepting user email | **OK** |
| **POST** `/links` | `get_current_user` middleware | Any authenticated user | **OK** |
| **GET** `/links` | `get_current_user` middleware | Only returns user's own created links | **OK** |
| **GET** `/links/:id` | `get_current_user` middleware | Checks `link.created_by == current_user` | **OK** |
| **PATCH** `/links/:id` | `get_current_user` middleware | Checks `link.created_by == current_user` | **OK** |
| **DELETE** `/links/:id` | `get_current_user` middleware | Checks `link.created_by == current_user` | **OK** |
| **GET** `/links/:id/analytics` | `get_current_user` middleware | Checks `link.created_by == current_user` | **OK** |
| **GET** `/:code` | (None - public redirect) | Anyone can access public short link | **OK** |
| **GET** `/teams/:team_id/audit-logs` | `get_current_user` middleware | `is_team_member(team_id, current_user)` check | **OK** |
| **GET** `/teams/:team_id/tasks` | `get_current_user` middleware | `is_team_member(team_id, current_user)` check | **OK** |
| **POST** `/teams/:team_id/tasks` | `get_current_user` middleware | `is_team_member(team_id, current_user)` check | **OK** |
| **GET** `/tasks/:id/comments` | `get_current_user` middleware | `is_team_member(task.team_id, current_user)` check | **OK** |
| **POST** `/tasks/:id/comments` | `get_current_user` middleware | `is_team_member(task.team_id, current_user)` check | **OK** |
| **POST** `/comments/:id/replies` | `get_current_user` middleware | `is_team_member(task.team_id, current_user)` check | **OK** |
| **DELETE** `/comments/:id` | `get_current_user` middleware | Author of comment OR team admin | **OK** |
| **WS** `/ws` | Custom token query validation | Returns only scoped team updates | **OK** |

---

### 2. Input Validation Audit
Mapping of incoming inputs to verification rules:

| ENDPOINT | INPUT FIELD | VALIDATION | STATUS |
| :--- | :--- | :--- | :--- |
| **POST** `/teams` | `name` | Non-empty, unique | **OK** |
| **POST** `/teams/:id/invitations` | `email` | Standard email format check | **OK** |
| **PUT** `/teams/:id/members/:user_email` | `role` | Enum: `owner`, `admin`, `member`, `viewer` | **OK** |
| **POST** `/teams/:team_id/tasks` | `title` | Non-empty | **OK** |
| **POST** `/tasks/:id/comments` | `body` | Non-empty | **OK** |
| **POST** `/comments/:id/replies` | `body` | Non-empty | **OK** |
| **POST** `/links` | `long_url` | Valid URL formatting | **OK** |

---

### 3. IDOR Check
Validation of resources being accessed only by their rightful owners/members:
- `/links/{link_id}`: Checked against `link.created_by == current_user` (verified in GET, PATCH, DELETE, and GET analytics).
- `/teams/{team_id}`: Audited such that team existence is checked, and team membership is checked through database lookup before exposing any resources.
- `/comments/{comment_id}`: Deletes are verified using `is_author = comment.author_email == current_user` or team admin checks.

---

### 4. Secrets Audit
- **Findings**:
  - The `.env` template / example files contain placeholders.
  - The API environment runs with custom JWT secret keys fetched from configuration environment variables, avoiding hardcoding.
  - Error handlers are customized to avoid leaking tracebacks in production environments.

---

### 5. Dependency Audit
- **Packages**:
  - `slowapi` (added for rate limiting): Verified, actively maintained, standard choice.
  - `pybreaker` (added for circuit breaker pattern): Verified, actively maintained.
  - `structlog` (for structured logging): Standard, well-maintained.
- **Vulnerabilities**: None found through `pip check` or audit checks.

---

## Architecture Review

### 1. Pattern Consistency
- Database queries consistently utilize SQLAlchemy Session and standard helper methods in `crud.py`.
- Routers use Depends injection for db sessions and auth.
- Domain events are consistently published to `event_bus` and handled asynchronously.

### 2. Naming Consistency
- Database models: Standardized `snake_case` field naming.
- Database tables: Consistent naming conventions.
- Function naming: Consistently uses `get_...`, `create_...`, etc.

### 3. Error Handling Consistency
- Exceptions consistently return JSON formatted errors through custom handlers in `app.exceptions.py`.

### 4. Test Coverage Map

| FEATURE | UNIT TESTS | INTEGRATION TESTS | AUTH TESTS | EDGE CASES | STATUS |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Teams CRUD** | Yes | Yes | Yes | Yes | **OK** |
| **Invitations** | Yes | Yes | Yes | Yes | **OK** |
| **Role Management** | Yes | Yes | Yes | Yes | **OK** |
| **Comments & Mentions** | Yes | Yes | Yes | Yes | **OK** |
| **Audit Log** | Yes | Yes | Yes | Yes | **OK** |
| **WebSocket** | Yes | Yes | Yes | Yes | **OK** |

---

## Prioritized Findings Document

### Finding 1: Lack of explicit audit logs for database operational failures (Low Priority)
- **Severity**: Low
- **Category**: Security / Data Integrity
- **Description**: If database connections drop, fallback paths handle the error gracefully but do not record an offline audit log.
- **Impact**: Slight visibility gap under DB failures.
- **Fix Plan**: Implement local buffering or file-based logging for events in `audit_subscriber.py` when DB is down.

### Finding 2: Missing Rate Limiting on WebSocket connection endpoint (Medium Priority)
- **Severity**: Medium
- **Category**: Security
- **Description**: The `/ws` connection handshake does not have active rate limit filters.
- **Impact**: Vulnerability to connection exhaustion / DOS.
- **Fix Plan**: Add connection limiter hook to `/ws` handshake.
