# System-Level Context

This document defines the architectural context, coding conventions, and constraints for the TaskFlow FastAPI application. All task implementations must adhere to these standards.

---

## 1. Architecture Summary

*   **Framework**: FastAPI (Python 3.11+)
*   **Database & ORM**: SQLAlchemy 2.0 with PostgreSQL. Uses the modern `Mapped` and `mapped_column` type annotations.
*   **Migrations**: Alembic handles schema migrations under the `alembic/` directory.
*   **Codebase Organization**:
    *   `app/main.py`: Application startup, exception handler registration, and router inclusion.
    *   `app/models.py`: SQLAlchemy database models.
    *   `app/schemas.py`: Pydantic models for request validation and response serialization.
    *   `app/crud.py`: Database operations/helpers utilizing SQLAlchemy Session.
    *   `app/auth.py`: Authentication helpers, JWT decoding, and dependency guards.
    *   `app/routers/`: Routers grouped by resource (e.g., `routers/auth.py`).
*   **Router Registration**:
    All routers must be registered in `app/main.py` using `app.include_router(router, prefix="/<resource>", tags=["<resource>"])`.
*   **Middleware**:
    Custom middleware (e.g., for logging or read-only database state checks) is placed in `app/middleware.py` and registered on the FastAPI app instance.

---

## 2. Coding Conventions

*   **Naming Conventions**:
    *   **Variables, Functions, and Column names**: `snake_case` (e.g., `user_email`, `created_at`, `get_current_user()`).
    *   **Classes (Models and Schemas)**: `PascalCase` (e.g., `TeamMembership`, `TeamCreate`).
    *   **Filenames**: `snake_case` (e.g., `models.py`, `routers/teams.py`).
*   **Error Handling**:
    All HTTP error responses must match the standard JSON wrapper format:
    ```json
    {
      "error": {
        "code": "HTTP_ERROR",
        "message": "Detail message here",
        "request_id": "optional-uuid"
      }
    }
    ```
    Standard codes include `VALIDATION_ERROR` (HTTP 422), `HTTP_ERROR` (generic HTTPExceptions), and `INTERNAL_SERVER_ERROR` (HTTP 500). Handlers are registered globally in `app/exceptions.py`.
    
    *   **CRITICAL RULE**: Routes must NEVER return raw error dictionaries (e.g., `return {"error": ...}`). They MUST raise standard FastAPI `HTTPException(status_code=..., detail="...")`. The global exception handlers in `app/exceptions.py` will catch them and automatically format them into the standard error wrapper with the appropriate `request_id`.
*   **Validation**:
    Done via Pydantic v2 schemas. Every POST/PUT payload must have a corresponding Pydantic schema class.
*   **Authentication & Authorization**:
    The authentication guard `Depends(get_current_user)` from `app/auth.py` must be used for protected routes to retrieve the authenticated user's email.

---

## 3. Constraints

1.  **Dependencies**: Do not install any new `pip` dependencies. Use standard Python libraries or existing packages (SQLAlchemy, Pydantic, FastAPI, Jose, etc.).
2.  **Auth Logic**: Use the existing `get_current_user` guard from `app/auth.py` to authenticate routes. Do not write custom token extraction/decoding logic in the routers.
3.  **Error Formats**: Always raise standard FastAPI `HTTPException` with a string detail. The global exception handlers in `app/exceptions.py` will automatically format these into the standard error response wrapper.
4.  **Database Migrations**: Every schema change must be accompanied by an Alembic migration script generated using `alembic revision --autogenerate -m "description"` and tested using `alembic upgrade head`.
