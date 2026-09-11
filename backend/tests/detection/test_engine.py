from datetime import datetime, timedelta, timezone
from app.models.security_event import SecurityEvent
from app.models.detection_rule import DetectionRule
from app.detection.evaluator import ThresholdEvaluator
import uuid

def test_threshold_evaluator(db_session):
    app_id = uuid.uuid4()
    
    rule = DetectionRule(
        name="Test Rule",
        severity="HIGH",
        event_type="TEST_EVENT",
        threshold=3,
        window_seconds=60,
        group_by="source_ip",
        enabled=True,
        application_id=None
    )
    db_session.add(rule)
    db_session.commit()
    
    # Add 2 events
    now = datetime.now(timezone.utc)
    for i in range(2):
        ev = SecurityEvent(
            application_id=app_id,
            event_type="TEST_EVENT",
            severity="LOW",
            timestamp=now - timedelta(seconds=10+i),
            source_ip="1.1.1.1"
        )
        db_session.add(ev)
    db_session.commit()
    
    # 3rd event triggers
    ev3 = SecurityEvent(
        application_id=app_id,
        event_type="TEST_EVENT",
        severity="LOW",
        timestamp=now,
        source_ip="1.1.1.1"
    )
    db_session.add(ev3)
    db_session.commit()
    
    # Evaluate
    result = ThresholdEvaluator.evaluate(db_session, rule, ev3)
    assert result == True

    # 4th event with different IP does not trigger
    ev4 = SecurityEvent(
        application_id=app_id,
        event_type="TEST_EVENT",
        severity="LOW",
        timestamp=now,
        source_ip="2.2.2.2"
    )
    db_session.add(ev4)
    db_session.commit()
    result4 = ThresholdEvaluator.evaluate(db_session, rule, ev4)
    assert result4 == False
