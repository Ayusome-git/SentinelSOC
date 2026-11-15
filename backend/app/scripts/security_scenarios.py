import argparse
import requests
import time
import sys
import uuid
import json

DEMO_APP_URL = "http://localhost:8080/api/telemetry"

def send_event(event_type, severity, message, username="anonymous", request_path="/", http_method="GET", ip="127.0.0.1", user_id=None, extra_metadata=None):
    payload = {
        "event_type": event_type,
        "severity": severity,
        "message": message,
        "username": username,
        "request_path": request_path,
        "http_method": http_method
    }
    if user_id:
        payload["user_id"] = user_id
    if extra_metadata:
        payload["metadata"] = extra_metadata

    headers = {
        "Content-Type": "application/json",
        "X-Forwarded-For": ip
    }

    try:
        response = requests.post(DEMO_APP_URL, json=payload, headers=headers)
        if response.status_code == 200:
            return True
        else:
            print(f"[!] Failed to send event: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"[!] Failed to connect to demo app at {DEMO_APP_URL}. Is it running?")
        sys.exit(1)

def run_brute_force():
    print("[*] Running Scenario 1: Brute Force Login")
    for i in range(1, 21):
        print(f"  -> Attempt {i}/20")
        send_event("LOGIN_FAILED", "MEDIUM", f"Failed login attempt {i}", username="admin", request_path="/api/login", http_method="POST", ip="10.0.0.1")
        time.sleep(0.1)
    print("[+] Done.")

def run_brute_force_success():
    print("[*] Running Scenario 2: Brute Force -> Success")
    for i in range(1, 15):
        print(f"  -> Failed Attempt {i}/14")
        send_event("LOGIN_FAILED", "MEDIUM", f"Failed login attempt {i}", username="testuser", request_path="/api/login", http_method="POST", ip="10.0.0.2")
        time.sleep(0.1)
    print("  -> Successful Login")
    send_event("LOGIN_SUCCESS", "INFO", "Successful login after brute force", username="testuser", request_path="/api/login", http_method="POST", ip="10.0.0.2")
    print("[+] Done.")

def run_credential_stuffing():
    print("[*] Running Scenario 3: Credential Stuffing")
    users = ["admin", "root", "user1", "guest", "test", "sales", "info", "system", "ayush", "demo"]
    for idx, u in enumerate(users):
        print(f"  -> Attempt {idx+1}/{len(users)} for {u}")
        send_event("LOGIN_FAILED", "MEDIUM", f"Failed login attempt for {u}", username=u, request_path="/api/login", http_method="POST", ip="10.0.0.3")
        time.sleep(0.1)
    print("[+] Done.")

def run_password_spray():
    print("[*] Running Scenario 4: Password Spray")
    for i in range(1, 15):
        ip = f"192.168.1.{i}"
        print(f"  -> Attempt {i}/14 from {ip}")
        send_event("LOGIN_FAILED", "MEDIUM", f"Failed login attempt from {ip}", username="administrator", request_path="/api/login", http_method="POST", ip=ip)
        time.sleep(0.1)
    print("[+] Done.")

def run_privilege_abuse():
    print("[*] Running Scenario 5: Privilege Abuse")
    for i in range(1, 7):
        print(f"  -> Permission Denied {i}/6")
        send_event("PERMISSION_DENIED", "MEDIUM", "Unauthorized access attempt", username="normal_user", user_id="usr_123", request_path="/admin/settings", ip="10.0.0.4")
        time.sleep(0.1)
    print("  -> Admin Action")
    send_event("ADMIN_ACTION", "HIGH", "Executed admin action", username="normal_user", user_id="usr_123", request_path="/admin/settings/update", http_method="POST", ip="10.0.0.4")
    print("[+] Done.")

def run_suspicious_path():
    print("[*] Running Scenario 6: Suspicious Request Path")
    send_event("API_REQUEST", "INFO", "API Request to suspicious path", request_path="/../../etc/passwd", ip="10.0.0.5")
    print("[+] Done.")

def run_sqli():
    print("[*] Running Scenario 7: SQLi Indicator")
    send_event("API_REQUEST", "INFO", "API Request with SQLi payload", request_path="/api/users?id=1' OR '1'='1", ip="10.0.0.6")
    print("[+] Done.")

def run_xss():
    print("[*] Running Scenario 8: XSS Indicator")
    send_event("API_REQUEST", "INFO", "API Request with XSS payload", request_path="/api/search?q=<script>alert(1)</script>", ip="10.0.0.7")
    print("[+] Done.")

def run_api_error_spike():
    print("[*] Running Scenario 9: API Error Spike")
    for i in range(1, 25):
        print(f"  -> API Error {i}/24")
        send_event("API_ERROR", "LOW", "Internal Server Error", request_path="/api/data", ip="10.0.0.8")
        time.sleep(0.1)
    print("[+] Done.")

def run_api_activity_spike():
    print("[*] Running Scenario 10: API Activity Spike")
    for i in range(1, 110):
        if i % 10 == 0:
            print(f"  -> API Request {i}/109")
        send_event("API_REQUEST", "INFO", "Normal API Request", request_path="/api/data", ip="10.0.0.9")
    print("[+] Done.")

def run_full_chain():
    print("[*] Running Scenario 11: Full Attack Chain")
    ip = "10.0.0.10"
    user = "hacker123"
    print("  -> Phase A: Reconnaissance / Activity Spike")
    for i in range(110):
        send_event("API_REQUEST", "INFO", "Recon Request", request_path="/api/scan", ip=ip)
    
    print("  -> Phase B: Repeated failed logins")
    for i in range(6):
        send_event("LOGIN_FAILED", "MEDIUM", "Failed login", username=user, request_path="/api/login", http_method="POST", ip=ip)
        time.sleep(0.1)
        
    print("  -> Phase C: Successful Login")
    send_event("LOGIN_SUCCESS", "INFO", "Successful login", username=user, request_path="/api/login", http_method="POST", ip=ip)
    
    print("  -> Phase D: Admin Login")
    send_event("ADMIN_LOGIN", "HIGH", "Admin Login", username=user, request_path="/api/admin/login", http_method="POST", ip=ip)
    
    print("  -> Phase E: Suspicious Requests")
    send_event("API_REQUEST", "INFO", "LFI attempt", request_path="/api/download?file=../../../etc/passwd", ip=ip)
    send_event("API_REQUEST", "INFO", "SQLi attempt", request_path="/api/users?id=1' OR '1'='1", ip=ip)
    
    print("[+] Done.")

def run_all():
    run_brute_force()
    run_brute_force_success()
    run_credential_stuffing()
    run_password_spray()
    run_privilege_abuse()
    run_suspicious_path()
    run_sqli()
    run_xss()
    run_api_error_spike()
    run_api_activity_spike()
    run_full_chain()

def reset_data():
    print("[!] Warning: You are about to wipe SOC test data generated by the harness.")
    from sqlalchemy.orm import Session
    from app.db.session import SessionLocal
    from app.models.security_event import SecurityEvent
    from app.models.alert import Alert
    from app.models.incident import Incident
    from app.models.correlation import Correlation

    db: Session = SessionLocal()
    # In a safe environment, we would use a tag like is_test=true, 
    # but here we'll clear everything because it's a dev environment and user wants to reset.
    print("[*] Clearing database...")
    db.query(Incident).delete()
    db.query(Correlation).delete()
    db.query(Alert).delete()
    db.query(SecurityEvent).delete()
    db.commit()
    print("[+] Test data reset successful.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SentinelSOC Security Test Harness")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run a security scenario")
    run_parser.add_argument("scenario", choices=["brute-force", "brute-force-success", "credential-stuffing", "password-spray", "privilege-abuse", "suspicious-path", "sqli", "xss", "api-error-spike", "api-activity-spike", "full-chain", "all"], help="Scenario to run")

    reset_parser = subparsers.add_parser("reset", help="Reset test data")

    args = parser.parse_args()

    if args.command == "run":
        if args.scenario == "brute-force":
            run_brute_force()
        elif args.scenario == "brute-force-success":
            run_brute_force_success()
        elif args.scenario == "credential-stuffing":
            run_credential_stuffing()
        elif args.scenario == "password-spray":
            run_password_spray()
        elif args.scenario == "privilege-abuse":
            run_privilege_abuse()
        elif args.scenario == "suspicious-path":
            run_suspicious_path()
        elif args.scenario == "sqli":
            run_sqli()
        elif args.scenario == "xss":
            run_xss()
        elif args.scenario == "api-error-spike":
            run_api_error_spike()
        elif args.scenario == "api-activity-spike":
            run_api_activity_spike()
        elif args.scenario == "full-chain":
            run_full_chain()
        elif args.scenario == "all":
            run_all()
    elif args.command == "reset":
        reset_data()
    else:
        parser.print_help()
