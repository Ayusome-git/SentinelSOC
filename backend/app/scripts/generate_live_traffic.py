"""
Live Traffic and Attack Simulator for SentinelSOC Presentations.

Enables live interactive demonstration of the SOC platform during presentations:
1. Trigger instant attack scenarios on demand (Brute Force, SQL Injection, DDoS, Exfiltration)
2. Run continuous background traffic simulation that continuously updates the dashboard
3. Inject immediate bursts of random events

Usage examples:
    # Trigger a live Brute Force attack:
    python -m app.scripts.generate_live_traffic --attack brute-force

    # Trigger a live SQL Injection attack:
    python -m app.scripts.generate_live_traffic --attack sqli

    # Trigger a full multi-stage attack chain:
    python -m app.scripts.generate_live_traffic --attack full-chain

    # Inject 20 random benign/user events instantly:
    python -m app.scripts.generate_live_traffic --batch 20

    # Stream continuous live traffic (press Ctrl+C to stop):
    python -m app.scripts.generate_live_traffic --continuous --interval 2
"""

import sys
import os
import time
import uuid
import random
import argparse
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.application import Application
from app.models.security_event import SecurityEvent, EventSeverity
from app.detection.service import DetectionService
from app.correlation.service import CorrelationService


BENIGN_USERS = ["emma.watson", "david.miller", "sarah.connor", "alex.turner", "lucas.scott", "maria.garcia"]
BENIGN_PATHS = [
    ("/api/v1/dashboard/overview", "GET"),
    ("/api/v1/users/profile", "GET"),
    ("/api/v1/payments/history", "GET"),
    ("/api/v1/orders/checkout", "POST"),
    ("/api/v1/notifications", "GET"),
    ("/api/v1/auth/refresh", "POST"),
]
BENIGN_IPS = ["192.168.1.10", "192.168.1.45", "10.0.4.12", "172.20.10.5", "64.233.160.1", "151.101.1.140"]


def get_target_app(db: Session, app_slug: str = None) -> Application:
    if app_slug:
        app = db.query(Application).filter(Application.slug == app_slug).first()
        if app:
            return app
    app = db.query(Application).first()
    if not app:
        print("[!] No applications found in database. Run seed_comprehensive_soc first.")
        sys.exit(1)
    return app


def inject_event(db: Session, event: SecurityEvent, evaluate: bool = True) -> SecurityEvent:
    db.add(event)
    db.commit()
    db.refresh(event)
    if evaluate:
        try:
            DetectionService.evaluate_event(db, event)
            CorrelationService.evaluate_event(db, event)
        except Exception as e:
            print(f"  [warn] Evaluation note: {e}")
    return event


def run_brute_force_scenario(db: Session, app: Application):
    print(f"\n[*] [LIVE ATTACK] Launching Brute Force scenario against: {app.name}")
    attacker_ip = f"198.51.100.{random.randint(10, 99)}"
    target_user = "admin_sec_ops"
    
    print(f"  -> Attacker IP: {attacker_ip}")
    print(f"  -> Target User: {target_user}")

    for i in range(8):
        evt = SecurityEvent(
            application_id=app.id,
            event_type="LOGIN_FAILED",
            severity=EventSeverity.MEDIUM.value,
            source_ip=attacker_ip,
            username=target_user,
            http_method="POST",
            request_path="/api/v1/auth/login",
            user_agent="Hydra/9.5 (Kali-Linux automated probe)",
            message=f"Failed login attempt {i+1}/8 (invalid password)",
            timestamp=datetime.now(timezone.utc),
            metadata_={"attempt": i+1, "status": "FAIL", "reason": "bad_credentials"}
        )
        inject_event(db, evt, evaluate=True)
        print(f"     [+] Event {i+1}/8 sent: LOGIN_FAILED")
        time.sleep(0.3)

    print("[SUCCESS] Brute Force scenario completed! Alert generated. Refresh your Alerts tab in browser.")


def run_sqli_scenario(db: Session, app: Application):
    print(f"\n[*] [LIVE ATTACK] Launching SQL Injection Probe against: {app.name}")
    attacker_ip = f"185.220.101.{random.randint(20, 90)}"
    sqli_vectors = [
        "/api/v1/products?id=1' OR '1'='1",
        "/api/v1/users?search=admin' UNION SELECT null,password,email FROM users--",
        "/api/v1/invoices/99; DROP TABLE temp_audit;--"
    ]

    for i, vector in enumerate(sqli_vectors):
        evt = SecurityEvent(
            application_id=app.id,
            event_type="API_REQUEST",
            severity=EventSeverity.HIGH.value,
            source_ip=attacker_ip,
            http_method="GET",
            request_path=vector,
            user_agent="sqlmap/1.8.2#stable (automated vulnerability scanner)",
            message=f"Critical SQL syntax injection attempt: {vector}",
            timestamp=datetime.now(timezone.utc),
            metadata_={"matched_pattern": "SQL_UNION_INJECTION", "response_code": 403}
        )
        inject_event(db, evt, evaluate=True)
        print(f"     [+] Event {i+1}/3 sent: SQLi vector on {vector[:35]}...")
        time.sleep(0.4)

    print("[SUCCESS] SQL Injection probes completed! Alert generated. Refresh your Alerts tab in browser.")


def run_dos_scenario(db: Session, app: Application):
    print(f"\n[*] [LIVE ATTACK] Launching API Flood / DoS scenario against: {app.name}")
    attacker_ip = f"203.0.113.{random.randint(50, 99)}"

    for i in range(25):
        evt = SecurityEvent(
            application_id=app.id,
            event_type="API_ERROR",
            severity=EventSeverity.MEDIUM.value,
            source_ip=attacker_ip,
            http_method="POST",
            request_path="/api/v1/transactions/charge",
            user_agent="Go-http-client/1.1 (load generator)",
            message="HTTP 429: Too Many Requests / Resource limits breached",
            timestamp=datetime.now(timezone.utc),
            metadata_={"rate_limit_breached": True, "http_status": 429}
        )
        inject_event(db, evt, evaluate=True)
        if (i + 1) % 5 == 0:
            print(f"     [+] Sent {i+1}/25 volumetric rate limit breach events...")
        time.sleep(0.05)

    print("[SUCCESS] API DoS flood completed! Refresh your Events and Alerts tabs.")


def run_full_chain_scenario(db: Session, app: Application):
    print(f"\n[*] [LIVE ATTACK CHAIN] Launching Full Kill-Chain Simulation against: {app.name}")
    attacker_ip = f"198.51.100.{random.randint(100, 150)}"
    user = "finance_lead"

    # Step 1: Brute force
    print("  [Stage 1/3] Brute force password guessing...")
    for i in range(6):
        evt = SecurityEvent(
            application_id=app.id,
            event_type="LOGIN_FAILED",
            severity=EventSeverity.MEDIUM.value,
            source_ip=attacker_ip,
            username=user,
            http_method="POST",
            request_path="/api/v1/auth/login",
            message=f"Brute force attempt {i+1}",
            timestamp=datetime.now(timezone.utc)
        )
        inject_event(db, evt, evaluate=True)
        time.sleep(0.2)

    # Step 2: Privilege elevation
    print("  [Stage 2/3] Admin session takeover & elevation...")
    admin_evt = SecurityEvent(
        application_id=app.id,
        event_type="ADMIN_LOGIN",
        severity=EventSeverity.HIGH.value,
        source_ip=attacker_ip,
        username=user,
        http_method="POST",
        request_path="/api/v1/admin/auth",
        message="Unauthorized administrative pivot achieved",
        timestamp=datetime.now(timezone.utc),
        metadata_={"escalated_role": "SYSTEM_ADMIN"}
    )
    inject_event(db, admin_evt, evaluate=True)
    time.sleep(0.5)

    # Step 3: Massive exfiltration
    print("  [Stage 3/3] Outbound archive data exfiltration...")
    exfil_evt = SecurityEvent(
        application_id=app.id,
        event_type="SUSPICIOUS_REQUEST",
        severity=EventSeverity.CRITICAL.value,
        source_ip=attacker_ip,
        username=user,
        http_method="POST",
        request_path="/api/v1/export/financial-records.enc",
        message="Data exfiltration: 48.2 MB compressed payload transferred",
        timestamp=datetime.now(timezone.utc),
        metadata_={"bytes_out": 50541312, "destination": "c2.external-vault.org"}
    )
    inject_event(db, exfil_evt, evaluate=True)
    print("[SUCCESS] Full Attack Chain deployed! Refresh Dashboard, Alerts, and Correlations.")


def generate_single_random_event(db: Session, app: Application) -> SecurityEvent:
    path, method = random.choice(BENIGN_PATHS)
    user = random.choice(BENIGN_USERS)
    ip = random.choice(BENIGN_IPS)
    
    event_type = random.choices(
        ["API_REQUEST", "LOGIN_SUCCESS", "API_ERROR"],
        weights=[75, 20, 5],
        k=1
    )[0]
    
    severity = EventSeverity.INFO.value if event_type != "API_ERROR" else EventSeverity.LOW.value

    evt = SecurityEvent(
        application_id=app.id,
        event_type=event_type,
        severity=severity,
        source_ip=ip,
        username=user,
        http_method=method,
        request_path=path,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
        message=f"Standard telemetry: {method} {path}",
        timestamp=datetime.now(timezone.utc)
    )
    return inject_event(db, evt, evaluate=False)


def run_batch(db: Session, app: Application, count: int):
    print(f"\n[*] Generating batch of {count} events for {app.name}...")
    for i in range(count):
        generate_single_random_event(db, app)
    print(f"[+] Successfully injected {count} events! Check Events and Dashboard tabs.")


def run_continuous(db: Session, app: Application, interval: float):
    print(f"\n[*] [STREAMING LIVE TRAFFIC] Sending live events every {interval}s to: {app.name}")
    print("[*] Keep this running during your presentation. Press Ctrl+C anytime to stop.\n")
    
    count = 0
    try:
        while True:
            evt = generate_single_random_event(db, app)
            count += 1
            now_str = datetime.now().strftime("%H:%M:%S")
            print(f"  [{now_str}] Event #{count}: {evt.event_type:<14} {evt.username:<15} {evt.source_ip:<15} {evt.request_path}")
            time.sleep(interval)
    except KeyboardInterrupt:
        print(f"\n[+] Stream stopped. Total events generated: {count}")


def main():
    parser = argparse.ArgumentParser(description="Live traffic and attack generator for SentinelSOC presentations.")
    parser.add_argument("--attack", choices=["brute-force", "sqli", "dos", "full-chain"], help="Trigger a live attack scenario.")
    parser.add_argument("--batch", type=int, help="Inject N random live events immediately.")
    parser.add_argument("--continuous", action="store_true", help="Stream continuous live events in real-time.")
    parser.add_argument("--interval", type=float, default=2.0, help="Seconds between events in continuous mode (default: 2.0).")
    parser.add_argument("--app", type=str, help="Target application slug (default: first application).")
    args = parser.parse_args()

    db: Session = SessionLocal()
    try:
        app = get_target_app(db, args.app)

        if args.attack == "brute-force":
            run_brute_force_scenario(db, app)
        elif args.attack == "sqli":
            run_sqli_scenario(db, app)
        elif args.attack == "dos":
            run_dos_scenario(db, app)
        elif args.attack == "full-chain":
            run_full_chain_scenario(db, app)
        elif args.batch:
            run_batch(db, app, args.batch)
        elif args.continuous:
            run_continuous(db, app, args.interval)
        else:
            print("SentinelSOC Live Traffic Simulator")
            print("-----------------------------------")
            print("Please specify an action:")
            print("  --attack brute-force   (simulate live brute force attack)")
            print("  --attack sqli          (simulate live SQL injection probe)")
            print("  --attack dos           (simulate live API rate limit flood)")
            print("  --attack full-chain    (simulate complete attack kill-chain)")
            print("  --batch 20             (inject 20 random events immediately)")
            print("  --continuous           (stream events continuously every 2s)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
