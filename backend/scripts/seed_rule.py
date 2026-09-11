import sys
import os

# Add backend to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.detection_rule import DetectionRule
from app.models.user import User, UserRole

def seed_rule():
    db: Session = SessionLocal()
    try:
        # Check if it already exists
        existing = db.query(DetectionRule).filter(DetectionRule.name == "Multiple Failed Logins").first()
        if existing:
            print("Rule already exists.")
            return

        admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        admin_id = admin.id if admin else None

        rule = DetectionRule(
            name="Multiple Failed Logins",
            description="Detects multiple failed login attempts from the same IP address within 5 minutes.",
            rule_type="THRESHOLD",
            enabled=True,
            severity="MEDIUM",
            event_type="AUTH_FAILED",
            threshold=5,
            window_seconds=300,
            group_by="source_ip",
            created_by=admin_id
        )
        
        db.add(rule)
        db.commit()
        print("Successfully seeded 'Multiple Failed Logins' detection rule.")
        
    finally:
        db.close()

if __name__ == "__main__":
    seed_rule()
