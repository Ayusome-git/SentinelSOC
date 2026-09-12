import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.correlation_rule import CorrelationRule
from app.models.user import User

def seed_correlations():
    db: Session = SessionLocal()
    admin_user = db.query(User).filter(User.email == "admin@sentinelsoc.local").first()
    
    rules = [
        CorrelationRule(
            name="Brute Force Followed by Successful Login",
            description="A brute-force login detection was followed by a successful login from the same source IP within 15 minutes.",
            severity="CRITICAL",
            time_window_seconds=900,
            sequence=[
                {"type": "alert", "alert_title": "Brute Force Login"},
                {"type": "event", "event_type": "LOGIN_SUCCESS"}
            ],
            relationships=["SAME_APPLICATION", "SAME_SOURCE_IP"],
            created_by=admin_user.id if admin_user else None
        ),
        CorrelationRule(
            name="Suspicious Login to Privileged Activity",
            description="A successful login was followed by an admin login and an admin action.",
            severity="CRITICAL",
            time_window_seconds=900,
            sequence=[
                {"type": "event", "event_type": "LOGIN_SUCCESS"},
                {"type": "event", "event_type": "ADMIN_LOGIN"},
                {"type": "event", "event_type": "ADMIN_ACTION"}
            ],
            relationships=["SAME_APPLICATION", "SAME_USER"],
            created_by=admin_user.id if admin_user else None
        ),
        CorrelationRule(
            name="Brute Force to Privilege Escalation",
            description="Brute force alert followed by successful login and admin action.",
            severity="CRITICAL",
            time_window_seconds=1200,
            sequence=[
                {"type": "alert", "alert_title": "Brute Force Login"},
                {"type": "event", "event_type": "LOGIN_SUCCESS"},
                {"type": "event", "event_type": "ADMIN_ACTION"}
            ],
            relationships=["SAME_APPLICATION", "SAME_SOURCE_IP"],
            created_by=admin_user.id if admin_user else None
        ),
        CorrelationRule(
            name="Web Attack Followed by API Abuse",
            description="SQL Injection followed by Suspicious Request and High API Volume.",
            severity="HIGH",
            time_window_seconds=600,
            sequence=[
                {"type": "alert", "alert_title": "SQL Injection Detected"},
                {"type": "alert", "alert_title": "Suspicious Request"},
                {"type": "alert", "alert_title": "High API Request Volume"}
            ],
            relationships=["SAME_APPLICATION"],
            created_by=admin_user.id if admin_user else None
        )
    ]
    
    for rule in rules:
        existing = db.query(CorrelationRule).filter(CorrelationRule.name == rule.name).first()
        if not existing:
            db.add(rule)
            print(f"Added correlation rule: {rule.name}")
            
    db.commit()
    print("Correlation seed complete.")

if __name__ == "__main__":
    seed_correlations()
