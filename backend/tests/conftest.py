import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.db.base import Base

# Using SQLite in-memory for basic unit tests if a real Postgres is unavailable,
# but we need to handle UUID and JSONB properly. 
# This file provides a fixture that tests can use to interact with the database.

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB

@compiles(JSONB, 'sqlite')
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "TEXT"

from sqlalchemy.pool import StaticPool
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session() -> Session: # type: ignore
    """
    Creates a fresh database for each test and drops it after.
    Note: SQLite doesn't natively support JSONB or UUID perfectly,
    but SQLAlchemy emulates UUID. For real tests, configure a real DB url.
    """
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    
    # Override get_db for FastAPI app
    from app.main import app
    from app.api.deps import get_db
    
    def override_get_db():
        try:
            yield session
        finally:
            pass # Session closed by fixture teardown
            
    app.dependency_overrides[get_db] = override_get_db
    
    yield session
    
    app.dependency_overrides.clear()
    session.close()
    Base.metadata.drop_all(bind=engine)
