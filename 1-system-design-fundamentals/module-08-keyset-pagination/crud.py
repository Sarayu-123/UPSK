from datetime import datetime

import random
import string
import hashlib
from app.metrics import urls_total
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import (
    func,
    asc,
    desc
)

from app.models import (
    Link,
    ClickEvent
)
import app.schemas as schemas
import app.models as models



# =========================================================
# SHORT CODE GENERATION
# =========================================================

def generate_short_code(
    length: int = 6
):
    alphabet = (
        string.ascii_letters
        + string.digits
    )

    return "".join(
        random.choices(
            alphabet,
            k=length
        )
    )


# =========================================================
# GET LINK BY CODE
# =========================================================

def get_link_by_code(
    db: Session,
    code: str
):
    return (
        db.query(Link)
        .filter(Link.code == code)
        .first()
    )


# =========================================================
# CREATE LINK
# =========================================================

def create_link(
    db: Session,
    link_in
):
    code = (
        link_in.code
        if link_in.code
        else generate_short_code()
    )

    while get_link_by_code(db, code):
        code = generate_short_code()

    db_link = Link(
        code=code,
        long_url=str(link_in.long_url),
        created_by=link_in.created_by
    )

    db.add(db_link)

    db.commit()

    db.refresh(db_link)

    urls_total.inc()

    return db_link


# =========================================================
# RECORD CLICK
# =========================================================

def record_click(
    db: Session,
    link_id: int,
    ip_address: str,
    user_agent: str | None = None,
    referrer: str | None = None
):
    ip_hash = hashlib.sha256(
        ip_address.encode()
    ).hexdigest()

    click = ClickEvent(
        link_id=link_id,
        ip_hash=ip_hash,
        user_agent=user_agent,
        referrer=referrer
    )

    db.add(click)

    db.commit()

    db.refresh(click)

    return click


# =========================================================
# GET LINK
# =========================================================

def get_link(
    db: Session,
    link_id: int
):
    return (
        db.query(Link)
        .filter(Link.id == link_id)
        .first()
    )


# =========================================================
# GET LINKS BY USER
# =========================================================

def get_links_by_user(
    db: Session,
    current_user: str,
    skip: int = 0,
    limit: int = 100
):
    return (
        db.query(Link)
        .options(joinedload(Link.clicks))
        .filter(
            Link.created_by == current_user
        )
        .order_by(
            Link.created_at.desc(),
            Link.id.desc()
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


# =========================================================
# DELETE LINK
# =========================================================

def delete_link(
    db: Session,
    link: Link
):
    db.delete(link)

    db.commit()

    urls_total.dec()


# =========================================================
# SEARCH LINKS
# =========================================================

def search_links(
    db: Session,
    current_user: str,
    q: str | None,
    skip: int,
    limit: int,
    sort_by: str,
    sort_order: str
):
    query = db.query(Link).filter(
        Link.created_by == current_user
    )

    if q:
        search_vector = func.to_tsvector(
            "english",
            func.coalesce(Link.code, "")
            + " "
            + func.replace(
                func.replace(
                    func.replace(
                        func.coalesce(
                            Link.long_url,
                            ""
                        ),
                        "/",
                        " "
                    ),
                    "_",
                    " "
                ),
                "-",
                " "
            )
        )

        search_query = func.plainto_tsquery(
            "english",
            q
        )

        query = query.filter(
            search_vector.op("@@")(search_query)
        )

    allowed_sort_fields = {
        "created_at": Link.created_at,
        "code": Link.code,
        "long_url": Link.long_url
    }

    sort_column = allowed_sort_fields.get(
        sort_by,
        Link.created_at
    )

    if sort_order == "asc":
        query = query.order_by(
            asc(sort_column),
            asc(Link.id)
        )
    else:
        query = query.order_by(
            desc(sort_column),
            desc(Link.id)
        )

    total_count = query.count()

    results = (
        query
        .offset(skip)
        .limit(limit)
        .all()
    )

    return results, total_count
# =========================================================
# UPDATE LINK
# =========================================================

def update_link(
    db: Session,
    link: Link,
    new_long_url: str
):
    link.long_url = new_long_url
    db.commit()
    db.refresh(link)
    return link


# =========================================================
# GET LINK ANALYTICS COUNT
# =========================================================

def get_link_analytics_count(
    db: Session,
    link_id: int,
    from_date,
    to_date
):
    query = (
        db.query(
            func.count(ClickEvent.id)
        )
        .filter(
            ClickEvent.link_id == link_id
        )
    )

    if from_date:
        query = query.filter(
            ClickEvent.clicked_at >= from_date
        )

    if to_date:
        query = query.filter(
            ClickEvent.clicked_at <= to_date
        )

    return query.scalar()


# =========================================================
# TEAM CRUD HELPERS
# =========================================================

def create_team(db: Session, team_in: schemas.TeamCreate, user_email: str) -> models.Team:
    db_team = models.Team(
        name=team_in.name,
        created_by=user_email
    )
    db.add(db_team)
    db.flush()
    db_membership = models.TeamMembership(
        team_id=db_team.id,
        user_email=user_email,
        role="owner"
    )
    db.add(db_membership)
    db.commit()
    db.refresh(db_team)
    return db_team


def get_user_teams(db: Session, user_email: str) -> list[models.Team]:
    return db.query(models.Team).join(models.TeamMembership).filter(models.TeamMembership.user_email == user_email).all()


def delete_team(db: Session, team_id: int) -> bool:
    db_team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not db_team:
        return False
    db.delete(db_team)
    db.commit()
    return True


def get_team(db: Session, team_id: int) -> models.Team | None:
    return db.query(models.Team).filter(models.Team.id == team_id).first()


def is_team_member(db: Session, team_id: int, email: str) -> bool:
    return db.query(models.TeamMembership).filter(
        models.TeamMembership.team_id == team_id,
        models.TeamMembership.user_email == email
    ).first() is not None


def is_team_admin(db: Session, team_id: int, email: str) -> bool:
    membership = db.query(models.TeamMembership).filter(
        models.TeamMembership.team_id == team_id,
        models.TeamMembership.user_email == email
    ).first()
    return membership is not None and membership.role in ("admin", "owner")


def create_invitation(db: Session, team_id: int, email: str, invited_by: str) -> models.Invitation:
    db_invitation = models.Invitation(
        team_id=team_id,
        email=email,
        invited_by=invited_by,
        status="pending"
    )
    db.add(db_invitation)
    db.commit()
    db.refresh(db_invitation)
    return db_invitation


def get_user_team_ids(db: Session, email: str) -> list[int]:
    memberships = db.query(models.TeamMembership.team_id).filter(
        models.TeamMembership.user_email == email
    ).all()
    return [m[0] for m in memberships]


def update_member_role(
    db: Session,
    team_id: int,
    target_email: str,
    new_role: str
) -> models.TeamMembership | None:
    membership = db.query(models.TeamMembership).filter(
        models.TeamMembership.team_id == team_id,
        models.TeamMembership.user_email == target_email
    ).first()
    if not membership:
        return None
    membership.role = new_role
    db.commit()
    db.refresh(membership)
    return membership
