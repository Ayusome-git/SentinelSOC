import pytest
from sqlalchemy.exc import IntegrityError
from app.models.user import User, UserRole
from app.models.application import Application, AppEnvironment, AppStatus
from app.models.security_event import SecurityEvent, EventSeverity
from app.models.alert import Alert, AlertStatus
from app.models.incident import Incident, IncidentStatus
from app.models.audit_log import AuditLog

def test_create_user(db_session):
    user = User(
        email="admin@sentinelsoc.test",
        password_hash="fakehash",
        full_name="Admin User",
        role=UserRole.ADMIN.value
    )
    db_session.add(user)
    db_session.commit()
    assert user.id is not None
    assert user.created_at is not None
    assert user.updated_at is not None
    assert user.email == "admin@sentinelsoc.test"

def test_user_email_unique(db_session):
    user1 = User(email="test@sentinelsoc.test", password_hash="hash1")
    user2 = User(email="test@sentinelsoc.test", password_hash="hash2")
    db_session.add(user1)
    db_session.commit()
    db_session.add(user2)
    with pytest.raises(IntegrityError):
        db_session.commit()

def test_create_application(db_session):
    user = User(email="owner@sentinelsoc.test", password_hash="hash")
    db_session.add(user)
    db_session.commit()

    app = Application(
        name="Test App",
        slug="test-app",
        owner_id=user.id
    )
    db_session.add(app)
    db_session.commit()
    assert app.id is not None
    assert app.slug == "test-app"
    assert app.owner.email == "owner@sentinelsoc.test"

def test_create_security_event_and_alert(db_session):
    user = User(email="sec@sentinelsoc.test", password_hash="hash")
    db_session.add(user)
    db_session.commit()

    app = Application(name="Sec App", slug="sec-app", owner_id=user.id)
    db_session.add(app)
    db_session.commit()

    event = SecurityEvent(
        application_id=app.id,
        event_type="FAILED_LOGIN",
        severity=EventSeverity.HIGH.value,
        source_ip="192.168.1.10",
        metadata_={"failed_attempts": 5}
    )
    db_session.add(event)
    db_session.commit()
    assert event.id is not None
    
    # Test Alert
    alert = Alert(
        application_id=app.id,
        security_event_id=event.id,
        title="High rate of failed logins",
        severity=EventSeverity.HIGH.value,
        detected_at=event.timestamp
    )
    db_session.add(alert)
    db_session.commit()
    assert alert.id is not None
    assert alert.security_event.event_type == "FAILED_LOGIN"

def test_create_incident(db_session):
    user = User(email="inc@sentinelsoc.test", password_hash="hash")
    app = Application(name="Inc App", slug="inc-app", owner_id=user.id)
    db_session.add_all([user, app])
    db_session.commit()

    incident = Incident(
        incident_number="INC-001",
        title="Brute Force Attack",
        severity="HIGH",
        application_id=app.id,
        detected_at=app.created_at
    )
    db_session.add(incident)
    db_session.commit()
    assert incident.id is not None

def test_audit_log(db_session):
    user = User(email="audit@sentinelsoc.test", password_hash="hash")
    db_session.add(user)
    db_session.commit()

    log = AuditLog(
        user_id=user.id,
        action="USER_LOGIN",
        ip_address="10.0.0.1",
        details={"browser": "Chrome"}
    )
    db_session.add(log)
    db_session.commit()
    assert log.id is not None
    assert log.user.email == "audit@sentinelsoc.test"
