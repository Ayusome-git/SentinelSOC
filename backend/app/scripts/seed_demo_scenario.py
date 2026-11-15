import asyncio
import uuid
import datetime
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.application import Application
from app.models.application_api_key import ApplicationApiKey as APIKey
from app.models.security_event import SecurityEvent as Event
import argparse
import sys

def generate_timestamp(offset_minutes: int):
    # Generates a UTC timestamp offset from current time
    now = datetime.datetime.now(datetime.timezone.utc)
    target = now + datetime.timedelta(minutes=offset_minutes)
    return target

async def run_scenario(reset: bool):
    print("SentinelSOC Demo Scenario Seeder")
    print("--------------------------------")
    
    db = SessionLocal()
    try:
        # Check if Demo Application already exists
        demo_app = db.query(Application).filter(Application.name == "SentinelSOC Demo Application").first()
        
        if reset:
            print("[*] Resetting demo scenario...")
            if demo_app:
                # Delete related events
                db.query(Event).filter(Event.application_id == demo_app.id).delete()
                # Delete application (which cascades to API keys usually, but let's be safe)
                db.query(APIKey).filter(APIKey.application_id == demo_app.id).delete()
                db.delete(demo_app)
                db.commit()
                print("[+] Demo data purged.")
            else:
                print("[-] No demo application found to reset.")
            return

        if not demo_app:
            print("[*] Creating Demo Application...")
            from app.models.user import User
            admin_user = db.query(User).filter(User.role == "ADMIN").first()
            if not admin_user:
                raise Exception("No ADMIN user found in the database. Please create an admin first.")
            demo_app = Application(
                name="SentinelSOC Demo Application",
                slug="sentinelsoc-demo-app",
                description="Synthetic application for demonstration scenarios.",
                environment="testing",
                owner_id=admin_user.id
            )
            db.add(demo_app)
            db.commit()
            db.refresh(demo_app)
            print(f"[+] Application created with ID: {demo_app.id}")

        print("[*] Injecting 'brute-force-to-admin' scenario events...")
        target_ip = "198.51.100.23" # TEST-NET-2 documentation IP
        target_user = "admin_user_42"
        
        events_to_insert = []
        
        # 1. Inject 15 LOGIN_FAILED events over 3 minutes
        print("  -> Injecting Brute Force (15 failures)...")
        for i in range(15):
            event = Event(
                application_id=demo_app.id,
                event_type="LOGIN_FAILED",
                severity="MEDIUM",
                source_ip=target_ip,
                user_id=target_user,
                timestamp=generate_timestamp(-15 + (i * 0.2)), # spread over 3 mins, starting 15 mins ago
                metadata_={"reason": "invalid_credentials", "attempt": i+1}
            )
            events_to_insert.append(event)
            
        # 2. Inject LOGIN_SUCCESS 1 minute later
        print("  -> Injecting Successful Login...")
        event_success = Event(
            application_id=demo_app.id,
            event_type="LOGIN_SUCCESS",
            severity="INFO",
            source_ip=target_ip,
            user_id=target_user,
            timestamp=generate_timestamp(-11),
            metadata_={"auth_method": "password"}
        )
        events_to_insert.append(event_success)

        # 3. Inject ADMIN_LOGIN and ADMIN_ACTIONs
        print("  -> Injecting Admin Pivot and Abuse...")
        events_to_insert.append(Event(
            application_id=demo_app.id,
            event_type="ADMIN_LOGIN",
            severity="HIGH",
            source_ip=target_ip,
            user_id=target_user,
            timestamp=generate_timestamp(-10),
            metadata_={"escalation": True}
        ))
        
        for i in range(5):
            events_to_insert.append(Event(
                application_id=demo_app.id,
                event_type="ADMIN_ACTION",
                severity="HIGH",
                source_ip=target_ip,
                user_id=target_user,
                timestamp=generate_timestamp(-9 + (i * 0.5)),
                metadata_={"action": "export_database", "table": f"users_{i}"}
            ))

        # 4. Inject SUSPICIOUS_REQUEST
        print("  -> Injecting Suspicious API Requests (Exfiltration)...")
        events_to_insert.append(Event(
            application_id=demo_app.id,
            event_type="SUSPICIOUS_REQUEST",
            severity="CRITICAL",
            source_ip=target_ip,
            user_id=target_user,
            timestamp=generate_timestamp(-5),
            metadata_={"route": "/api/v1/export", "bytes_transferred": 50000000}
        ))
        
        db.add_all(events_to_insert)
        db.commit()
        
        print(f"[+] Successfully injected {len(events_to_insert)} raw events.")
        print("[*] Note: The Detection and Correlation engines will process these events asynchronously in the background.")
        print("[*] Please check the 'Events', 'Alerts', and 'Incidents' tabs in the Dashboard.")

    except Exception as e:
        print(f"[!] Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed SentinelSOC demo scenario.")
    parser.add_argument("--scenario", type=str, help="Scenario to run (e.g., brute-force-to-admin)", default="brute-force-to-admin")
    parser.add_argument("--reset", action="store_true", help="Purge the demo scenario data.")
    args = parser.parse_args()
    
    asyncio.run(run_scenario(args.reset))
