import sys
import os
import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.db.session import SessionLocal
from app.models.application import Application
from app.models.security_event import SecurityEvent
from app.detection.service import DetectionService
from app.correlation.service import CorrelationService

def generate_timestamp(offset_minutes: int):
    now = datetime.datetime.now(datetime.timezone.utc)
    return now + datetime.timedelta(minutes=offset_minutes)

def run():
    db = SessionLocal()
    try:
        demo_app = db.query(Application).filter(Application.name == "SentinelSOC Demo Application").first()
        if not demo_app:
            print("Demo app not found! Please run seed_demo_scenario first.")
            return

        events = []
        
        # Attack 1: SQL Injection Attempt
        events.append(SecurityEvent(
            application_id=demo_app.id,
            event_type="API_REQUEST",
            severity="INFO",
            source_ip="203.0.113.10",
            request_path="/api/users?id=1' OR '1'='1",
            timestamp=generate_timestamp(-2)
        ))
        
        # Attack 2: Cross-Site Scripting (XSS) Attempt
        events.append(SecurityEvent(
            application_id=demo_app.id,
            event_type="API_REQUEST",
            severity="INFO",
            source_ip="203.0.113.11",
            request_path="/api/search?q=<script>alert(1)</script>",
            timestamp=generate_timestamp(-1)
        ))

        # Attack 3: API Error Spike (Denial of Service precursor)
        for i in range(30):
            events.append(SecurityEvent(
                application_id=demo_app.id,
                event_type="API_ERROR",
                severity="LOW",
                source_ip="198.51.100.99",
                request_path="/api/resource",
                timestamp=generate_timestamp(0)
            ))
            
        db.add_all(events)
        db.commit()
        
        print(f"[*] Successfully injected {len(events)} new attack events (SQLi, XSS, and Error Spikes).")
        print("[*] Evaluating events through Detection Engine...")
        
        for e in events:
            DetectionService.evaluate_event(db, e)
            CorrelationService.evaluate_event(db, e)
            
        print("[+] Processing complete! Check the Events and Alerts tabs.")
    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run()
