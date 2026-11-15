import os
import sys

# Ensure backend path is added
sys.path.insert(0, r"c:\Users\ayush\OneDrive\Desktop\CyberSOC\backend")

from app.db.session import SessionLocal
from app.models.security_event import SecurityEvent
from app.models.alert import Alert

db = SessionLocal()

print("--- Latest Events ---")
events = db.query(SecurityEvent).order_by(SecurityEvent.timestamp.desc()).limit(10).all()
for e in events:
    print(f"[{e.timestamp}] {e.event_type} - {e.source_ip} - {e.message}")

print("\n--- Latest Alerts ---")
alerts = db.query(Alert).order_by(Alert.created_at.desc()).limit(10).all()
for a in alerts:
    print(f"[{a.created_at}] Rule: {a.rule_id} - Severity: {a.severity} - Status: {a.status}")

db.close()
