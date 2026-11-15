import os
import sys

sys.path.insert(0, r"c:\Users\ayush\OneDrive\Desktop\CyberSOC\backend")

from app.db.session import SessionLocal
from app.models.security_event import SecurityEvent, EventSeverity
from app.models.application import Application
from app.models.alert import Alert
from app.schemas.security_event import EventCreate
from app.services.event_service import normalize_and_store_event
from datetime import datetime, timezone

db = SessionLocal()

app = db.query(Application).first()

print(f"Using App ID: {app.id}")

# Let's delete existing alerts for XSS just in case
existing_xss_alerts = db.query(Alert).filter(Alert.title.ilike("%XSS%")).all()
for a in existing_xss_alerts:
    db.delete(a)
db.commit()

# Inject XSS event
event_in = EventCreate(
    event_type="API_REQUEST",
    severity=EventSeverity.HIGH,
    timestamp=datetime.now(timezone.utc),
    source_ip="127.0.0.1",
    message="API request payload matching XSS pattern",
    username="anonymous",
    request_path="/api/comments?body=<script>alert('XSS')</script>",
    http_method="POST"
)

try:
    print("Normalizing and storing event...")
    event_id = normalize_and_store_event(db=db, application=app, event_in=event_in)
    print(f"Event stored with ID: {event_id}")
    
    # Check if alert was generated
    alert = db.query(Alert).filter(Alert.security_event_id == event_id).first()
    if alert:
        print(f"Alert generated successfully! Title: {alert.title}, Status: {alert.status}")
    else:
        print("NO ALERT GENERATED.")
        
        # Check if the rule exists
        from app.models.detection_rule import DetectionRule
        rules = db.query(DetectionRule).all()
        print("Existing rules:")
        for r in rules:
            if "XSS" in r.name or r.pattern:
                print(f" - {r.name}: pattern={r.pattern}, type={r.rule_type}, active={r.is_active}")
                
except Exception as e:
    import traceback
    traceback.print_exc()

db.close()
