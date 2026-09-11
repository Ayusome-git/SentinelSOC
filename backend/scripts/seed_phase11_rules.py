import asyncio
import os
import sys

# Add backend to path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.detection_rule import DetectionRule
from app.models.user import User, UserRole

def seed_rules():
    db: Session = SessionLocal()
    
    # Try to find an admin to assign as creator
    admin = db.query(User).filter(User.role == UserRole.ADMIN.value).first()
    creator_id = admin.id if admin else None

    rules_to_seed = [
        {
            "name": "Brute Force Login Attempt",
            "description": "Detects 5 or more failed login attempts from the same source IP within a 5-minute window.",
            "rule_type": "THRESHOLD",
            "category": "AUTHENTICATION",
            "severity": "HIGH",
            "event_type": "LOGIN_FAILED",
            "threshold": 5,
            "window_seconds": 300,
            "group_by": "source_ip",
        },
        {
            "name": "Credential Stuffing Detected",
            "description": "Detects multiple failed logins from the same IP using different usernames within a 5-minute window.",
            "rule_type": "THRESHOLD",
            "category": "AUTHENTICATION",
            "severity": "HIGH",
            "event_type": "LOGIN_FAILED",
            "threshold": 5,
            "window_seconds": 300,
            "group_by": "source_ip",
            "distinct_field": "username",
        },
        {
            "name": "Password Spray Detected",
            "description": "Detects multiple failed logins against the same username from different IP addresses within a 5-minute window.",
            "rule_type": "THRESHOLD",
            "category": "AUTHENTICATION",
            "severity": "HIGH",
            "event_type": "LOGIN_FAILED",
            "threshold": 5,
            "window_seconds": 300,
            "group_by": "username",
            "distinct_field": "source_ip",
        },
        {
            "name": "Repeated Authorization Failures",
            "description": "Detects 5 or more permission denied errors for the same user within 5 minutes.",
            "rule_type": "THRESHOLD",
            "category": "AUTHORIZATION",
            "severity": "HIGH",
            "event_type": "PERMISSION_DENIED",
            "threshold": 5,
            "window_seconds": 300,
            "group_by": "user_id",
        },
        {
            "name": "High API Request Volume",
            "description": "Detects an unusually high volume of API requests from a single IP.",
            "rule_type": "THRESHOLD",
            "category": "API_ABUSE",
            "severity": "MEDIUM",
            "event_type": "API_REQUEST",
            "threshold": 100,
            "window_seconds": 60,
            "group_by": "source_ip",
        },
        {
            "name": "API Error Spike",
            "description": "Detects a spike in API errors from a single IP.",
            "rule_type": "THRESHOLD",
            "category": "ANOMALY",
            "severity": "MEDIUM",
            "event_type": "API_ERROR",
            "threshold": 20,
            "window_seconds": 60,
            "group_by": "source_ip",
        },
        {
            "name": "Suspicious Privileged Activity",
            "description": "Detects an unusually high number of admin actions by a single user.",
            "rule_type": "THRESHOLD",
            "category": "PRIVILEGE_ABUSE",
            "severity": "HIGH",
            "event_type": "ADMIN_ACTION",
            "threshold": 20,
            "window_seconds": 300,
            "group_by": "user_id",
        },
        {
            "name": "Privilege Escalation Indicator",
            "description": "Detects an admin action occurring shortly after a permission denied error for the same user.",
            "rule_type": "SEQUENCE",
            "category": "PRIVILEGE_ABUSE",
            "severity": "CRITICAL",
            "event_type": "ADMIN_ACTION",
            "window_seconds": 300,
        },
        {
            "name": "Suspicious Request Path",
            "description": "Detects requests targeting known sensitive configuration files or admin paths.",
            "rule_type": "PATTERN",
            "category": "WEB_ATTACK",
            "severity": "HIGH",
            "event_type": "API_REQUEST", # applies to incoming requests
            "pattern": r"(?i)(/etc/passwd|/etc/shadow|/wp-admin|/\.env|/config|/admin)",
        },
        {
            "name": "Possible SQL Injection",
            "description": "Detects SQL injection patterns in requests.",
            "rule_type": "PATTERN",
            "category": "WEB_ATTACK",
            "severity": "HIGH",
            "event_type": "API_REQUEST",
            "pattern": r"(?i)(' OR|\" OR|UNION SELECT|SELECT .* FROM|DROP TABLE|SLEEP\(|BENCHMARK\()",
        },
        {
            "name": "Possible XSS Attack",
            "description": "Detects Cross-Site Scripting (XSS) patterns in requests.",
            "rule_type": "PATTERN",
            "category": "WEB_ATTACK",
            "severity": "HIGH",
            "event_type": "API_REQUEST",
            "pattern": r"(?i)(<script|javascript:|onerror=|onload=|<svg|<iframe)",
        },
        {
            "name": "Possible Path Traversal",
            "description": "Detects directory traversal indicators in request paths.",
            "rule_type": "PATTERN",
            "category": "WEB_ATTACK",
            "severity": "HIGH",
            "event_type": "API_REQUEST",
            "pattern": r"(?i)(\.\./|\.\.\\|%2e%2e|%252e%252e)",
        },
        {
            "name": "Suspicious Request Spike",
            "description": "Detects a spike in explicitly flagged suspicious requests.",
            "rule_type": "THRESHOLD",
            "category": "ANOMALY",
            "severity": "HIGH",
            "event_type": "SUSPICIOUS_REQUEST",
            "threshold": 10,
            "window_seconds": 60,
            "group_by": "source_ip",
        },
    ]

    print(f"Seeding {len(rules_to_seed)} Phase 11 rules...")

    for rule_data in rules_to_seed:
        # Check if rule exists by name
        existing = db.query(DetectionRule).filter(DetectionRule.name == rule_data["name"]).first()
        if existing:
            print(f"Rule '{rule_data['name']}' already exists. Updating...")
            for k, v in rule_data.items():
                setattr(existing, k, v)
        else:
            print(f"Creating rule '{rule_data['name']}'...")
            new_rule = DetectionRule(**rule_data, created_by=creator_id)
            db.add(new_rule)
            
    db.commit()
    print("Seeding complete.")

if __name__ == "__main__":
    seed_rules()
