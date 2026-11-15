import os
import sys

sys.path.insert(0, r"c:\Users\ayush\OneDrive\Desktop\CyberSOC\backend")

from app.db.session import SessionLocal
from app.models.security_event import SecurityEvent
from app.models.alert import Alert

db = SessionLocal()

# Check latest alert
latest_alert = db.query(Alert).order_by(Alert.created_at.desc()).first()
if latest_alert:
    print(f"Latest Alert: {latest_alert.title} at {latest_alert.created_at} | rule_id: {latest_alert.rule_id} | event_id: {latest_alert.security_event_id}")
else:
    print("No alerts found.")

# Check latest event
latest_event = db.query(SecurityEvent).order_by(SecurityEvent.timestamp.desc()).first()
if latest_event:
    print(f"Latest Event: {latest_event.event_type} at {latest_event.timestamp} | message: {latest_event.message}")
else:
    print("No events found.")

db.close()
