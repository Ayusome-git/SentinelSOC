import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.db.session import SessionLocal
from app.models.security_event import SecurityEvent
from app.detection.service import DetectionService
from app.correlation.service import CorrelationService

def process_events():
    db = SessionLocal()
    try:
        # Only process the most recent 25 events (to avoid the 560 event backlog!)
        events = db.query(SecurityEvent).order_by(SecurityEvent.timestamp.desc()).limit(25).all()
        events.reverse() # Process oldest to newest
        
        print(f"[*] Processing the last {len(events)} events...")
        for e in events:
            DetectionService.evaluate_event(db, e)
            CorrelationService.evaluate_event(db, e)
        print("[+] Processing complete! Check your Alerts and Incidents tabs.")
    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    process_events()
