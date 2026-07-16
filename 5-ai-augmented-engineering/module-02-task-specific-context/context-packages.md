# Per-Task Context Bundles

This document defines the context packages for the first three tasks of the Team Collaboration feature implementation.

---

## TASK 1: Create Team and Membership Database Schema

### SYSTEM CONTEXT
[progress/system-context.md](file:///c:/Users/shiva/CAW/progress/system-context.md)

### FILES TO READ (with reasons)
1.  **[app/models.py](file:///c:/Users/shiva/CAW/api/app/models.py)**:
    *   **Reason**: Demonstrates how models are declared using modern SQLAlchemy 2.0 annotations (`Mapped`, `mapped_column`, relationships, cascade rules).
    *   *If omitted*: The agent might write models in the old SQLAlchemy 1.x syntax or define invalid cascade rules.
2.  **[app/database.py](file:///c:/Users/shiva/CAW/api/app/database.py)**:
    *   **Reason**: Shows the declarative `Base` class used by all models to register in the metadata registry.
    *   *If omitted*: The agent might import a wrong base or define models disconnected from the main migration metadata.

### FILES TO MODIFY
*   **[app/models.py](file:///c:/Users/shiva/CAW/api/app/models.py)**: To append the `Team` and `TeamMembership` models.

### EXPECTED OUTPUT
*   **Modified file**: `api/app/models.py` (with the new models)
*   **New file**: Alembic migration script under `api/alembic/versions/` (generated via autogenerate)

---

## TASK 2: Implement Team CRUD Router and Endpoints

### SYSTEM CONTEXT
[progress/system-context.md](file:///c:/Users/shiva/CAW/progress/system-context.md)

### FILES TO READ (with reasons)
1.  **[app/main.py](file:///c:/Users/shiva/CAW/api/app/main.py)**:
    *   **Reason**: Shows how other routers are registered in the FastAPI app.
    *   *If omitted*: The agent might register the router incorrectly or omit registering it altogether.
2.  **[app/schemas.py](file:///c:/Users/shiva/CAW/api/app/schemas.py)**:
    *   **Reason**: Shows how other response and request schemas are defined using Pydantic.
    *   *If omitted*: The agent might use invalid types, or write Pydantic v1 schemas.
3.  **[app/crud.py](file:///c:/Users/shiva/CAW/api/app/crud.py)**:
    *   **Reason**: Shows patterns for database queries, insertions, and sessions.
    *   *If omitted*: The agent might use direct raw SQL queries or improper Session transaction contexts.
4.  **[app/exceptions.py](file:///c:/Users/shiva/CAW/api/app/exceptions.py)**:
    *   **Reason**: Explains the global exception handler logic mapping raised HTTPExceptions to standard `{ "error": { "code": ..., "message": ... } }` responses.
    *   *If omitted*: The agent might manually format and return raw error dictionaries inside routes instead of raising exceptions.

### FILES TO MODIFY
*   **[app/main.py](file:///c:/Users/shiva/CAW/api/app/main.py)**: To include/register the new team router.
*   **[app/schemas.py](file:///c:/Users/shiva/CAW/api/app/schemas.py)**: To add the team-related Pydantic schemas.
*   **[app/crud.py](file:///c:/Users/shiva/CAW/api/app/crud.py)**: To add CRUD helper functions for Teams and TeamMemberships.

### EXPECTED OUTPUT
*   **Modified files**: `api/app/main.py`, `api/app/schemas.py`, `api/app/crud.py`
*   **New file**: `api/app/routers/teams.py` (containing route handlers for `/teams`)

---

## TASK 3: Role and Permission Validation Middleware

### SYSTEM CONTEXT
[progress/system-context.md](file:///c:/Users/shiva/CAW/progress/system-context.md)

### FILES TO READ (with reasons)
1.  **[app/auth.py](file:///c:/Users/shiva/CAW/api/app/auth.py)**:
    *   **Reason**: Shows how current user extraction (`get_current_user`) and token validations are implemented.
    *   *If omitted*: The agent might duplicate the extraction logic or decode JWTs differently, causing authentication drift.
2.  **[app/routers/teams.py](file:///c:/Users/shiva/CAW/api/app/routers/teams.py)** (created in Task 2):
    *   **Reason**: Shows where the permissions guard needs to be integrated.
    *   *If omitted*: The agent cannot know which routes need restriction and what route parameter names are used.
3.  **[app/exceptions.py](file:///c:/Users/shiva/CAW/api/app/exceptions.py)**:
    *   **Reason**: Outlines standard error HTTP handlers. Guards must raise `HTTPException` to allow central processing.
    *   *If omitted*: The agent might return custom JSON responses in dependencies instead of raising standard exceptions.

### FILES TO MODIFY
*   **[app/auth.py](file:///c:/Users/shiva/CAW/api/app/auth.py)**: To add the permission guard dependency function `require_team_role`.
*   **[app/routers/teams.py](file:///c:/Users/shiva/CAW/api/app/routers/teams.py)**: To secure the endpoints (e.g. DELETE `/teams/{id}`) using the new guard.

### EXPECTED OUTPUT
*   **Modified files**: `api/app/auth.py`, `api/app/routers/teams.py`
