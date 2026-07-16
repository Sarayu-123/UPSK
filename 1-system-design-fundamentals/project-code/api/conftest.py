import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.database as database_module
import app.tasks as tasks_module

TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/upsk_sdf_test"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Patch SessionLocal at the module levels BEFORE importing app.main
database_module.SessionLocal = TestingSessionLocal
tasks_module.SessionLocal = TestingSessionLocal
tasks_module.TasksSessionLocal = TestingSessionLocal


from app.main import app
from app.database import get_db, Base

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Globally override the database dependency for all TestClients
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_database():
    import app.models as models
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    db.query(models.AuditLog).delete()
    db.query(models.Comment).delete()
    db.query(models.Task).delete()
    db.query(models.TeamMembership).delete()
    db.query(models.Team).delete()
    db.query(models.Invitation).delete()
    try:
        db.query(models.ClickEvent).delete()
        db.query(models.Link).delete()
    except Exception:
        pass
    db.commit()
    db.close()
