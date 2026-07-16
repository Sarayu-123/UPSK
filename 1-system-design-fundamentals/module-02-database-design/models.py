from datetime import datetime

from sqlalchemy import (
    Integer,
    String,
    DateTime,
    ForeignKey,
    Index,
    func,
    text,
    JSON,
    UniqueConstraint
)

from sqlalchemy.orm import (
    mapped_column,
    relationship,
    Mapped
)

from app.database import Base


class Link(Base):
    __tablename__ = "links"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    code: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        nullable=False
    )

    long_url: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )

    created_by: Mapped[str] = mapped_column(
        String,
        index=True,
        nullable=False
    )

    clicks: Mapped[list["ClickEvent"]] = relationship(
        back_populates="link",
        cascade="all, delete"
    )


class ClickEvent(Base):
    __tablename__ = "click_events"

    __table_args__ = (
        Index(
            "ix_click_events_link_id_clicked_at",
            "link_id",
            "clicked_at"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    link_id: Mapped[int] = mapped_column(
        ForeignKey(
            "links.id",
            ondelete="CASCADE"
        )
    )

    clicked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow
    )

    user_agent: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    referrer: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    ip_hash: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False
    )

    link: Mapped["Link"] = relationship(
        back_populates="clicks"
    )


Index(
    "ix_links_search_vector",
    func.to_tsvector(
        text("'english'"),
        func.coalesce(Link.code, "")
        + " "
        + func.replace(
            func.replace(
                func.replace(
                    func.coalesce(Link.long_url, ""),
                    "/",
                    " "
                ),
                "_",
                " "
            ),
            "-",
            " "
        )
    ),
    postgresql_using="gin"
)


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )

    created_by: Mapped[str] = mapped_column(
        String,
        index=True,
        nullable=False
    )

    memberships: Mapped[list["TeamMembership"]] = relationship(
        back_populates="team",
        cascade="all, delete-orphan"
    )

    invitations: Mapped[list["Invitation"]] = relationship(
        back_populates="team",
        cascade="all, delete-orphan"
    )

    tasks: Mapped[list["Task"]] = relationship(
        back_populates="team",
        cascade="all, delete-orphan"
    )



class TeamMembership(Base):
    __tablename__ = "team_memberships"

    __table_args__ = (
        UniqueConstraint("team_id", "user_email", name="uq_team_membership"),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    team_id: Mapped[int] = mapped_column(
        ForeignKey(
            "teams.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    user_email: Mapped[str] = mapped_column(
        String,
        index=True,
        nullable=False
    )

    role: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    team: Mapped["Team"] = relationship(
        back_populates="memberships"
    )


class Invitation(Base):
    __tablename__ = "invitations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    team_id: Mapped[int] = mapped_column(
        ForeignKey(
            "teams.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String,
        index=True,
        nullable=False
    )

    invited_by: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String,
        default="pending",
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )

    team: Mapped["Team"] = relationship(
        back_populates="invitations"
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    team_id: Mapped[int] = mapped_column(
        ForeignKey(
            "teams.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    title: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    created_by: Mapped[str] = mapped_column(
        String,
        index=True,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )

    team: Mapped["Team"] = relationship(
        back_populates="tasks"
    )

    comments: Mapped[list["Comment"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan"
    )


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    task_id: Mapped[int] = mapped_column(
        ForeignKey(
            "tasks.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    author_email: Mapped[str] = mapped_column(
        String,
        index=True,
        nullable=False
    )

    body: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "comments.id",
            ondelete="CASCADE"
        ),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )

    task: Mapped["Task"] = relationship(
        back_populates="comments"
    )

    parent: Mapped["Comment | None"] = relationship(
        back_populates="replies",
        remote_side=[id]
    )

    replies: Mapped[list["Comment"]] = relationship(
        back_populates="parent",
        cascade="all, delete-orphan"
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    action: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    resource_type: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    resource_id: Mapped[int] = mapped_column(
        Integer,
        index=True,
        nullable=False
    )

    actor_email: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )

    details: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )