# Team Collaboration API Documentation

## Overview
This API provides endpoints for team collaboration, including team management, invitations, role-based access control, task tracking, commenting, mentions, and audit logging.

## Authentication
All endpoints require a valid JWT bearer token in the `Authorization` header, except for `/auth/login`.

## Endpoints

### Teams

#### `POST /teams/`
Creates a new team and assigns the creator as the "owner".
- **Request Body**: `{"name": "Team Name"}`
- **Response (201)**: `Team` object.

#### `GET /teams/`
Lists all teams the authenticated user belongs to.
- **Response (200)**: Array of `Team` objects.

#### `DELETE /teams/{team_id}`
Deletes a team. Requires "admin" or "owner" privileges.
- **Response (200)**: `{"ok": True}`

### Team Memberships & Roles

#### `PUT /teams/{team_id}/members/{user_email}`
Updates a member's role. Requires "owner" or "admin" privileges. Owners can elevate to admin/owner; Admins can elevate to member/viewer.
- **Request Body**: `{"role": "admin" | "member" | "viewer" | "owner"}`
- **Response (200)**: `{"ok": True}`

### Invitations

#### `POST /teams/{team_id}/invitations`
Sends an invitation to a user. Requires "admin" or "owner" privileges.
- **Request Body**: `{"email": "user@example.com"}`
- **Response (201)**: `Invitation` object.

#### `POST /invitations/{invitation_id}/accept`
Accepts an invitation. Can only be accepted by the invited user.
- **Response (200)**: `Invitation` object with status `accepted`.

### Tasks

#### `POST /teams/{team_id}/tasks`
Creates a new task within a team. Requires team membership.
- **Request Body**: `{"title": "Task Title"}`
- **Response (201)**: `Task` object.

#### `GET /teams/{team_id}/tasks`
Lists all tasks for a given team.
- **Response (200)**: Array of `Task` objects.

### Comments

#### `POST /tasks/{task_id}/comments`
Creates a new comment on a task. Supports mentions using `@user@example.com`.
- **Request Body**: `{"body": "Comment text"}`
- **Response (201)**: `Comment` object.

#### `GET /tasks/{task_id}/comments`
Retrieves all comments for a task.
- **Response (200)**: Array of `Comment` objects.

#### `POST /comments/{comment_id}/replies`
Replies to an existing comment.
- **Request Body**: `{"body": "Reply text"}`
- **Response (201)**: `Comment` object (with `parent_id` set).

#### `DELETE /comments/{comment_id}`
Deletes a comment. Only the author or a team admin can delete.
- **Response (200)**: `{"ok": True}`

### Mentions

#### `GET /mentions`
Retrieves all unread mentions for the authenticated user.
- **Response (200)**: Array of `Mention` objects.

#### `POST /mentions/{mention_id}/read`
Marks a specific mention as read.
- **Response (200)**: `{"ok": True}`

### Audit Logs

#### `GET /teams/{team_id}/audit-logs`
Retrieves the audit log for a team. Requires "admin" or "owner" privileges.
- **Response (200)**: Array of `AuditLog` objects, sorted by timestamp descending.

## Real-Time Events (WebSockets)
Connect to `/ws/teams/{team_id}` to receive real-time notifications for:
- `comment_created`
- `comment_deleted`
- `invitation_accepted`
- `mention_notified`
