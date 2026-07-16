from datetime import datetime
from enum import Enum
from urllib.parse import urlparse

from pydantic import (
    BaseModel,
    HttpUrl,
    field_validator
)


class TeamRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class LinkCreate(BaseModel):
    long_url: HttpUrl
    code: str | None = None
    created_by: str | None = None

    @field_validator("long_url")
    @classmethod
    def validate_long_url(cls, value):
        url = str(value)

        if len(url) > 2048:
            raise ValueError(
                "URL exceeds maximum length"
            )

        url = (
            url.replace("\n", "")
            .replace("\r", "")
        )

        parsed = urlparse(url)

        if parsed.scheme not in {"http", "https"}:
            raise ValueError(
                "URL must use http or https"
            )

        if not parsed.netloc:
            raise ValueError(
                "URL must contain a valid host"
            )

        return HttpUrl(url)

    @field_validator("code")
    @classmethod
    def validate_code(cls, value):
        if value is None:
            return value

        if len(value) < 3:
            raise ValueError(
                "Code must be at least 3 characters"
            )

        if not value.isalnum():
            raise ValueError(
                "Code must be alphanumeric"
            )

        return value


class LinkUpdate(BaseModel):
    long_url: HttpUrl

    @field_validator("long_url")
    @classmethod
    def validate_long_url(cls, value):
        url = str(value)

        if len(url) > 2048:
            raise ValueError(
                "URL exceeds maximum length"
            )

        url = (
            url.replace("\n", "")
            .replace("\r", "")
        )

        parsed = urlparse(url)

        if parsed.scheme not in {"http", "https"}:
            raise ValueError(
                "URL must use http or https"
            )

        if not parsed.netloc:
            raise ValueError(
                "URL must contain a valid host"
            )

        return HttpUrl(url)


class LinkResponse(BaseModel):
    id: int
    code: str
    long_url: str
    created_at: datetime
    created_by: str

    model_config = {
        "from_attributes": True
    }


class PaginationMetadata(BaseModel):
    page: int
    page_size: int
    total_count: int
    total_pages: int
    has_next: bool
    has_previous: bool


class SearchResponse(BaseModel):
    items: list[LinkResponse]
    pagination: PaginationMetadata


class TeamCreate(BaseModel):
    name: str


class TeamOut(BaseModel):
    id: int
    name: str
    created_by: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class TeamMemberOut(BaseModel):
    id: int
    user_email: str
    role: str

    model_config = {
        "from_attributes": True
    }


class UpdateMemberRole(BaseModel):
    role: str


class TeamOutWithMembers(TeamOut):
    memberships: list[TeamMemberOut]


class InvitationCreate(BaseModel):
    email: str



class InvitationOut(BaseModel):
    id: int
    team_id: int
    email: str
    invited_by: str
    status: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class TaskCreate(BaseModel):
    title: str


class TaskOut(BaseModel):
    id: int
    team_id: int
    title: str
    created_by: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class CommentCreate(BaseModel):
    body: str
    parent_id: int | None = None


class CommentOut(BaseModel):
    id: int
    task_id: int
    author_email: str
    body: str
    parent_id: int | None
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class AuditLogOut(BaseModel):
    id: int
    action: str
    resource_type: str
    resource_id: int
    actor_email: str
    timestamp: datetime
    details: dict | None = None

    model_config = {
        "from_attributes": True
    }