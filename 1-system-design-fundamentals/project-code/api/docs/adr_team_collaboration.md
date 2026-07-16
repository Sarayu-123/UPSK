# Architecture Decision Record (ADR): Role-Based Access Control and Activity Feed

## Status
Accepted

## Context
As the URL Shortener application evolves into a collaboration platform, we need robust authorization (RBAC) to ensure users can only perform actions on teams and resources they have access to. Additionally, we need to track user actions securely and notify users of real-time events via an Activity Feed.

## Decisions

### 1. Role-Based Access Control (RBAC)
We opted for a 4-tier hierarchical role structure within Teams:
- `owner`: Can manage team settings, delete the team, and manage all roles.
- `admin`: Can invite users, manage `member` and `viewer` roles, and view audit logs.
- `member`: Can create tasks and comments, and perform standard team operations.
- `viewer`: Can only read team resources.

**Reasoning**: This provides granular control over team resources without creating an overly complex permissions matrix. Role escalation is explicitly prevented in the API layer, requiring the requester to have a higher or equal role to assign a role.

### 2. Audit Logging via Event Bus
Instead of tightly coupling business logic with audit logging, we implemented an asynchronous Event Bus. 
- Controllers publish domain events (e.g., `comment.created`, `invitation.accepted`) to the Event Bus.
- Subscribers listen for these events and record them in the `AuditLog` table.

**Reasoning**: This decouples the core API logic from auditing, improves maintainability, and allows us to easily add more event listeners in the future (e.g., for analytics or external webhooks).

### 3. Real-Time Activity Feed
Real-time notifications are delivered via WebSockets, scoped securely to individual teams.
- When an event occurs, the domain publishes a payload to the WebSocket `ConnectionManager`.
- The manager broadcasts the event strictly to active connections authenticated and authorized for that specific `team_id`.

**Reasoning**: WebSockets provide the necessary low latency for collaboration features like mentions and task comments. Scoping by `team_id` prevents data leakage across teams.

## Consequences
- **Positive**: Clean separation of concerns between domain logic and side-effects (auditing/notifications). Secure role escalation prevention is enforced at the controller level.
- **Negative**: The Event Bus introduces slight indirection, meaning developers must trace subscribers to understand the full lifecycle of an action. Testing requires executing the FastAPI lifespan to ensure event subscribers are registered properly (which is handled natively by `TestClient`).
