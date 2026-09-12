import pytest
from uuid import uuid4
from datetime import datetime, timezone
from fastapi import HTTPException
from app.models.alert import Alert, AlertStatus
from app.models.user import User, UserRole
from app.models.application import Application
from app.services.alert_workflow_service import AlertWorkflowService
from app.models.audit_log import AuditLog

@pytest.fixture
def test_user(db_session):
    user = User(
        id=uuid4(),
        email=f"test_analyst_{uuid4()}@example.com",
        password_hash="hash",
        full_name="Test Analyst",
        role=UserRole.ANALYST,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def test_application(db_session, test_user):
    app = Application(
        id=uuid4(),
        name="Test App",
        slug=f"test-app-{uuid4()}",
        owner_id=test_user.id
    )
    db_session.add(app)
    db_session.commit()
    return app

@pytest.fixture
def test_alert(db_session, test_application):
    alert = Alert(
        id=uuid4(),
        application_id=test_application.id,
        title="Test Alert",
        severity="HIGH",
        status=AlertStatus.OPEN,
        detected_at=datetime.now(timezone.utc)
    )
    db_session.add(alert)
    db_session.commit()
    return alert

def test_valid_transitions(db_session, test_alert, test_user):
    # OPEN -> ACKNOWLEDGED
    alert = AlertWorkflowService.acknowledge(db_session, test_alert, test_user)
    assert alert.status == AlertStatus.ACKNOWLEDGED
    assert alert.acknowledged_at is not None
    
    # ACKNOWLEDGED -> RESOLVED
    alert = AlertWorkflowService.resolve(db_session, alert, test_user)
    assert alert.status == AlertStatus.RESOLVED
    assert alert.resolved_at is not None
    
    # Check audit logs
    audits = db_session.query(AuditLog).filter(AuditLog.resource_id == str(alert.id)).order_by(AuditLog.created_at).all()
    assert len(audits) == 2
    assert audits[0].action == "ALERT_ACKNOWLEDGED"
    assert audits[1].action == "ALERT_RESOLVED"

def test_invalid_transitions(db_session, test_alert, test_user):
    # Set alert to RESOLVED
    test_alert.status = AlertStatus.RESOLVED
    db_session.commit()
    
    # RESOLVED -> ACKNOWLEDGED (Should fail)
    with pytest.raises(HTTPException) as exc:
        AlertWorkflowService.acknowledge(db_session, test_alert, test_user)
    assert exc.value.status_code == 409
    
    # RESOLVED -> FALSE_POSITIVE (Should fail)
    with pytest.raises(HTTPException) as exc:
        AlertWorkflowService.mark_false_positive(db_session, test_alert, test_user)
    assert exc.value.status_code == 409

def test_false_positive_workflow(db_session, test_alert, test_user):
    # OPEN -> FALSE_POSITIVE
    alert = AlertWorkflowService.mark_false_positive(db_session, test_alert, test_user)
    assert alert.status == AlertStatus.FALSE_POSITIVE
    assert alert.resolved_at is not None
    
def test_assign_alert(db_session, test_alert, test_user):
    alert = AlertWorkflowService.assign(db_session, test_alert, test_user.id, test_user)
    assert alert.assigned_to == test_user.id
    
    # Unassign
    alert = AlertWorkflowService.assign(db_session, alert, None, test_user)
    assert alert.assigned_to is None

def test_add_comment(db_session, test_alert, test_user):
    comment = AlertWorkflowService.add_comment(db_session, test_alert, "Test comment", test_user)
    assert comment.comment == "Test comment"
    assert comment.alert_id == test_alert.id
    assert comment.user_id == test_user.id
