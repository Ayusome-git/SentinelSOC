"""
Comprehensive SentinelSOC Demonstration Data Seeder.

Populates all database tables with realistic, coherent security operations data:
- Applications (Payment Gateway, Customer Portal, Auth Service)
- Application API Keys
- Detection Rules (Threshold, Pattern, Sequence)
- Security Events across 24h timeline (Login, API, Admin, Database)
- Security Alerts with MITRE techniques, risk scores, and statuses
- Correlated Attack Chains (Brute Force -> Admin Pivot -> Exfiltration)
- Incidents with timeline comments and evidence
- Threat Intelligence indicators (Tor nodes, scanner IPs, C2 domains)
- Machine Learning Anomaly Detection model & baseline stats
- Response capabilities and pending/approved actions
- In-App Notifications for SOC analysts

Usage:
    python -m app.scripts.seed_comprehensive_soc [--reset]
"""

import sys
import os
import uuid
import random
import hashlib
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session
from app.db.session import SessionLocal

from app.models.user import User, UserRole
from app.models.application import Application, AppEnvironment, AppStatus
from app.models.application_api_key import ApplicationApiKey
from app.models.detection_rule import DetectionRule
from app.models.correlation_rule import CorrelationRule
from app.models.security_event import SecurityEvent, EventSeverity, incident_events
from app.models.alert import Alert, AlertStatus, DetectionSource, incident_alerts
from app.models.correlation import Correlation, CorrelationStatus, correlation_alerts, correlation_events
from app.models.incident import Incident, IncidentStatus
from app.models.incident_comment import IncidentComment
from app.models.threat_intel import ThreatIntelIndicator, AlertThreatIntel
from app.models.ml_model import MLModel, MLModelStatus
from app.models.response import ApplicationResponseCapability, ResponseAction, ResponseActionStatus
from app.models.notification import Notification, NotificationType, NotificationChannel, NotificationStatus


def generate_time(minutes_ago: float) -> datetime:
    return datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)


def seed():
    print("=" * 60)
    print("  SentinelSOC Comprehensive Data Seeder")
    print("=" * 60)

    db: Session = SessionLocal()
    try:
        # 1. Fetch or create Admin user
        admin = db.query(User).filter(User.role == UserRole.ADMIN.value).first()
        if not admin:
            admin = User(
                email="admin@sentinelsoc.com",
                password_hash="$argon2id$v=19$m=65536,t=3,p=4$q6qZ6qZ6qZ6qZ6qZ6qZ6qw$dummyhashforexample",
                full_name="SOC Administrator",
                role=UserRole.ADMIN.value,
                is_active=True
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            print(f"[+] Created Administrator: {admin.email}")
        else:
            if not admin.full_name:
                admin.full_name = "SOC Administrator"
                db.commit()
            print(f"[*] Using existing Administrator: {admin.email} ({admin.full_name})")

        # 2. Applications
        print("\n[*] Seeding Monitored Applications...")
        app_specs = [
            ("Payment Gateway Service", "payment-gateway", "Core transaction processing and settlement service", AppEnvironment.PRODUCTION.value),
            ("Customer Web Portal", "customer-portal", "Public-facing account management and billing dashboard", AppEnvironment.PRODUCTION.value),
            ("Identity & Auth Provider", "identity-auth", "Centralized OAuth2 / OIDC authentication service", AppEnvironment.PRODUCTION.value),
            ("Data Analytics Pipeline", "analytics-pipeline", "Internal telemetry and metrics aggregation worker", AppEnvironment.STAGING.value),
        ]

        apps = {}
        for name, slug, desc, env in app_specs:
            app_obj = db.query(Application).filter(Application.slug == slug).first()
            if not app_obj:
                app_obj = Application(
                    name=name,
                    slug=slug,
                    description=desc,
                    environment=env,
                    status=AppStatus.ACTIVE.value,
                    owner_id=admin.id
                )
                db.add(app_obj)
                db.commit()
                db.refresh(app_obj)
                print(f"  -> Created app: {name} ({env})")
            else:
                # Normalize environment if it was old/legacy
                if app_obj.environment != env:
                    app_obj.environment = env
                    db.commit()
                print(f"  -> App exists: {name}")
            apps[slug] = app_obj

        # 3. API Keys for each application
        print("\n[*] Generating Application API Keys...")
        for slug, app_obj in apps.items():
            existing_key = db.query(ApplicationApiKey).filter(ApplicationApiKey.application_id == app_obj.id).first()
            if not existing_key:
                raw_prefix = f"soc_{slug[:6]}"
                dummy_hash = hashlib.sha256(f"{raw_prefix}_{uuid.uuid4()}".encode()).hexdigest()
                key = ApplicationApiKey(
                    application_id=app_obj.id,
                    name=f"Production Agent Key - {app_obj.name}",
                    key_prefix=raw_prefix,
                    key_hash=dummy_hash,
                    is_active=True,
                    created_by=admin.id,
                    last_used_at=datetime.now(timezone.utc) - timedelta(minutes=random.randint(1, 30))
                )
                db.add(key)
        db.commit()

        # 4. Detection Rules
        print("\n[*] Seeding Detection Rules...")
        rules_specs = [
            {
                "name": "SSH & API Brute Force Detection",
                "description": "Flags 5 or more failed authentication attempts from a single IP within 5 minutes.",
                "rule_type": "THRESHOLD",
                "severity": "HIGH",
                "event_type": "LOGIN_FAILED",
                "threshold": 5,
                "window_seconds": 300,
                "group_by": "source_ip",
                "category": "AUTHENTICATION",
                "mitre_technique": "T1110"
            },
            {
                "name": "SQL Injection Attack Vector Probe",
                "description": "Detects SQL syntax injection patterns in HTTP request query and body parameters.",
                "rule_type": "PATTERN",
                "severity": "CRITICAL",
                "event_type": "API_REQUEST",
                "pattern": "(UNION|SELECT|--|OR 1=1|DROP TABLE)",
                "category": "INJECTION",
                "mitre_technique": "T1190"
            },
            {
                "name": "Abnormal Data Exfiltration Transfer",
                "description": "Alerts when an unauthenticated or privileged endpoint exports an unusually large byte payload.",
                "rule_type": "THRESHOLD",
                "severity": "CRITICAL",
                "event_type": "SUSPICIOUS_REQUEST",
                "threshold": 1,
                "window_seconds": 60,
                "category": "EXFILTRATION",
                "mitre_technique": "T1567"
            },
            {
                "name": "Privileged Admin Escalation & Session Pivot",
                "description": "Detects sudden elevation from standard user privileges to administrative roles.",
                "rule_type": "THRESHOLD",
                "severity": "HIGH",
                "event_type": "ADMIN_LOGIN",
                "threshold": 2,
                "window_seconds": 120,
                "category": "PRIVILEGE_ESCALATION",
                "mitre_technique": "T1078"
            },
            {
                "name": "API Rate Limit & Resource Exhaustion (DoS)",
                "description": "Alerts on 20+ error responses from single client IP within 1 minute.",
                "rule_type": "THRESHOLD",
                "severity": "MEDIUM",
                "event_type": "API_ERROR",
                "threshold": 20,
                "window_seconds": 60,
                "group_by": "source_ip",
                "category": "DENIAL_OF_SERVICE",
                "mitre_technique": "T1499"
            },
            {
                "name": "Cross-Site Scripting (XSS) Filter Breach",
                "description": "Matches script tags and DOM manipulation keywords in API payloads.",
                "rule_type": "PATTERN",
                "severity": "MEDIUM",
                "event_type": "API_REQUEST",
                "pattern": "(<script|javascript:|onerror=)",
                "category": "INJECTION",
                "mitre_technique": "T1059"
            }
        ]

        rules = []
        for r_spec in rules_specs:
            rule_obj = db.query(DetectionRule).filter(DetectionRule.name == r_spec["name"]).first()
            if not rule_obj:
                rule_obj = DetectionRule(
                    name=r_spec["name"],
                    description=r_spec["description"],
                    rule_type=r_spec["rule_type"],
                    severity=r_spec["severity"],
                    event_type=r_spec["event_type"],
                    threshold=r_spec.get("threshold"),
                    window_seconds=r_spec.get("window_seconds"),
                    group_by=r_spec.get("group_by"),
                    pattern=r_spec.get("pattern"),
                    category=r_spec.get("category"),
                    mitre_technique=r_spec.get("mitre_technique"),
                    enabled=True,
                    created_by=admin.id
                )
                db.add(rule_obj)
                db.commit()
                db.refresh(rule_obj)
                print(f"  -> Created rule: {rule_obj.name}")
            rules.append(rule_obj)

        # 5. Correlation Rules
        print("\n[*] Seeding Correlation Attack Rules...")
        corr_rule = db.query(CorrelationRule).filter(CorrelationRule.name == "Account Takeover to Exfiltration Chain").first()
        if not corr_rule:
            corr_rule = CorrelationRule(
                name="Account Takeover to Exfiltration Chain",
                description="Correlates Brute Force failures followed by Admin Login and Suspicious Exfiltration from the same IP.",
                rule_type="SEQUENCE",
                severity="CRITICAL",
                time_window_seconds=900,
                sequence=[
                    {"type": "event", "event_type": "LOGIN_FAILED"},
                    {"type": "event", "event_type": "ADMIN_LOGIN"},
                    {"type": "event", "event_type": "SUSPICIOUS_REQUEST"}
                ],
                relationships=["SAME_SOURCE_IP"],
                enabled=True,
                created_by=admin.id
            )
            db.add(corr_rule)
            db.commit()
            db.refresh(corr_rule)
            print(f"  -> Created correlation rule: {corr_rule.name}")

        # 6. Security Events
        print("\n[*] Ingesting Realistic Security Events...")
        attacker_ip_1 = "198.51.100.23"  # Known Botnet
        attacker_ip_2 = "185.220.101.5"   # Tor Exit Node
        attacker_ip_3 = "203.0.113.88"   # Script Scanner
        internal_ip = "10.0.1.45"
        regular_ip = "72.14.201.12"

        events = []
        payment_app = apps["payment-gateway"]
        auth_app = apps["identity-auth"]
        portal_app = apps["customer-portal"]

        # A. Brute force sequence on Auth app (20 failures)
        for i in range(20):
            events.append(SecurityEvent(
                application_id=auth_app.id,
                event_type="LOGIN_FAILED",
                severity=EventSeverity.MEDIUM.value,
                source_ip=attacker_ip_1,
                username="administrator",
                user_id="user_admin",
                http_method="POST",
                request_path="/api/v1/auth/login",
                user_agent="Mozilla/5.0 (Hydra/9.5 Kali-Linux)",
                message=f"Failed password authentication attempt {i+1}",
                timestamp=generate_time(120 - (i * 0.4)),
                metadata_={"attempt": i+1, "auth_provider": "local"}
            ))

        # Successful credential breach
        breach_event = SecurityEvent(
            application_id=auth_app.id,
            event_type="LOGIN_SUCCESS",
            severity=EventSeverity.INFO.value,
            source_ip=attacker_ip_1,
            username="administrator",
            user_id="user_admin",
            http_method="POST",
            request_path="/api/v1/auth/login",
            user_agent="Mozilla/5.0 (Hydra/9.5 Kali-Linux)",
            message="Successful authentication after multiple failed attempts",
            timestamp=generate_time(111),
            metadata_={"auth_provider": "local", "mfa_bypassed": True}
        )
        events.append(breach_event)

        # Admin login & elevation
        admin_login_event = SecurityEvent(
            application_id=auth_app.id,
            event_type="ADMIN_LOGIN",
            severity=EventSeverity.HIGH.value,
            source_ip=attacker_ip_1,
            username="administrator",
            user_id="user_admin",
            http_method="POST",
            request_path="/api/v1/admin/session",
            user_agent="Mozilla/5.0 (Hydra/9.5 Kali-Linux)",
            message="Administrative console session initiated from anomalous external IP",
            timestamp=generate_time(110),
            metadata_={"role": "SUPERADMIN", "session_id": "sess_89af32d"}
        )
        events.append(admin_login_event)

        # Admin actions
        for i, table in enumerate(["credit_cards", "users_vault", "api_credentials"]):
            events.append(SecurityEvent(
                application_id=payment_app.id,
                event_type="ADMIN_ACTION",
                severity=EventSeverity.HIGH.value,
                source_ip=attacker_ip_1,
                username="administrator",
                user_id="user_admin",
                http_method="POST",
                request_path=f"/api/v1/admin/tables/{table}/dump",
                message=f"Direct database extraction query executed against {table}",
                timestamp=generate_time(108 - (i * 2)),
                metadata_={"table": table, "row_count": 45000}
            ))

        # Suspicious massive exfiltration
        exfil_event = SecurityEvent(
            application_id=payment_app.id,
            event_type="SUSPICIOUS_REQUEST",
            severity=EventSeverity.CRITICAL.value,
            source_ip=attacker_ip_1,
            username="administrator",
            user_id="user_admin",
            http_method="POST",
            request_path="/api/v1/export/bulk-download",
            message="Anomalous outbound transfer of 68.4 MB encrypted archive",
            timestamp=generate_time(102),
            metadata_={"bytes_sent": 71722880, "destination_domain": "data-drop-collector.org"}
        )
        events.append(exfil_event)

        # B. SQL Injection probes on Customer Portal
        sqli_payloads = [
            "/api/v1/customers?search=' OR '1'='1",
            "/api/v1/invoices/1029; DROP TABLE audit_temp;--",
            "/api/v1/products?cat=1 UNION SELECT null,username,password FROM users--",
            "/api/v1/profile?id=admin' AND 1=1--"
        ]
        for i, payload in enumerate(sqli_payloads):
            events.append(SecurityEvent(
                application_id=portal_app.id,
                event_type="API_REQUEST",
                severity=EventSeverity.HIGH.value,
                source_ip=attacker_ip_2,
                http_method="GET",
                request_path=payload,
                user_agent="sqlmap/1.8.2#stable (https://sqlmap.org)",
                message=f"SQL injection heuristic triggered on query parameter: {payload}",
                timestamp=generate_time(85 - (i * 5)),
                metadata_={"matched_filter": "SQL_SYNTAX", "waf_action": "LOGGED"}
            ))

        # C. Denial of Service API error flood
        for i in range(25):
            events.append(SecurityEvent(
                application_id=payment_app.id,
                event_type="API_ERROR",
                severity=EventSeverity.MEDIUM.value,
                source_ip=attacker_ip_3,
                http_method="POST",
                request_path="/api/v1/transactions/process",
                message="HTTP 429 Too Many Requests / 503 Service Unavailable",
                timestamp=generate_time(40 - (i * 0.5)),
                metadata_={"status_code": 429, "retry_after": 60}
            ))

        # D. Normal operational baseline events across past 24h
        users_list = ["sarah.miller", "alex.chen", "david.kim", "olivia.martinez", "jordan.lee"]
        for i in range(50):
            u = random.choice(users_list)
            events.append(SecurityEvent(
                application_id=random.choice([payment_app.id, portal_app.id, auth_app.id]),
                event_type=random.choice(["API_REQUEST", "LOGIN_SUCCESS", "API_REQUEST"]),
                severity=EventSeverity.INFO.value,
                source_ip=regular_ip if random.random() > 0.3 else internal_ip,
                username=u,
                user_id=f"user_{hashlib.md5(u.encode()).hexdigest()[:8]}",
                http_method=random.choice(["GET", "POST", "GET"]),
                request_path=random.choice(["/api/v1/account", "/api/v1/dashboard/stats", "/api/v1/billing/history", "/api/v1/status"]),
                timestamp=generate_time(random.uniform(5, 1400)),
                message="Routine authenticated user action"
            ))

        db.add_all(events)
        db.commit()
        print(f"  -> Ingested {len(events)} security events.")

        # 7. Threat Intelligence Indicators
        print("\n[*] Populating Threat Intelligence Indicators...")
        ti_specs = [
            ("198.51.100.23", "IP", "AbuseIPDB", True, 92, "Known credential brute-force botnet participant", ["brute_force", "botnet"]),
            ("185.220.101.5", "IP", "AlienVault OTX", True, 98, "Active Tor Exit Node used in vulnerability scans", ["tor", "scanner"]),
            ("data-drop-collector.org", "DOMAIN", "VirusTotal", True, 88, "Suspected Command & Control data drop server", ["c2", "exfiltration"]),
            ("203.0.113.88", "IP", "Spamhaus", True, 75, "Automated denial of service scanner", ["dos", "scanner"]),
        ]

        ti_indicators = []
        for ind, ind_type, src, mal, conf, rep, cats in ti_specs:
            ti_obj = db.query(ThreatIntelIndicator).filter(ThreatIntelIndicator.indicator == ind).first()
            if not ti_obj:
                ti_obj = ThreatIntelIndicator(
                    indicator=ind,
                    indicator_type=ind_type,
                    source=src,
                    malicious=mal,
                    confidence=conf,
                    reputation=rep,
                    categories=cats,
                    first_seen_at=generate_time(3000),
                    last_seen_at=generate_time(10),
                    reference="https://threatintel.sentinelsoc.local/intel"
                )
                db.add(ti_obj)
                db.commit()
                db.refresh(ti_obj)
            ti_indicators.append(ti_obj)

        # 8. Alerts
        print("\n[*] Generating Security Alerts...")
        alerts_data = [
            {
                "title": "Brute Force Attack Detected against Identity Provider",
                "description": f"Over 20 failed login attempts detected in 5 minutes originating from suspicious IP {attacker_ip_1}.",
                "severity": "CRITICAL",
                "status": AlertStatus.OPEN.value,
                "detection_source": DetectionSource.RULE.value,
                "risk_score": 92,
                "risk_level": "CRITICAL",
                "app": auth_app,
                "detected_at": generate_time(112),
                "ti_indicator": ti_indicators[0]
            },
            {
                "title": "SQL Injection Pattern Detected on Public Search API",
                "description": f"Classic SQL injection string 'UNION SELECT' detected from IP {attacker_ip_2}.",
                "severity": "CRITICAL",
                "status": AlertStatus.OPEN.value,
                "detection_source": DetectionSource.RULE.value,
                "risk_score": 88,
                "risk_level": "CRITICAL",
                "app": portal_app,
                "detected_at": generate_time(84),
                "ti_indicator": ti_indicators[1]
            },
            {
                "title": "Anomalous Outbound Data Transfer (Exfiltration)",
                "description": f"68.4 MB of encrypted archive data transmitted to unknown destination {attacker_ip_1}.",
                "severity": "CRITICAL",
                "status": AlertStatus.OPEN.value,
                "detection_source": DetectionSource.RULE.value,
                "risk_score": 96,
                "risk_level": "CRITICAL",
                "app": payment_app,
                "detected_at": generate_time(101),
                "ti_indicator": ti_indicators[2]
            },
            {
                "title": "Privilege Escalation to Superadmin Detected",
                "description": f"Administrative session initiated after anomalous authentication sequence from {attacker_ip_1}.",
                "severity": "HIGH",
                "status": AlertStatus.ACKNOWLEDGED.value,
                "detection_source": DetectionSource.RULE.value,
                "risk_score": 78,
                "risk_level": "HIGH",
                "app": auth_app,
                "detected_at": generate_time(109),
                "ti_indicator": ti_indicators[0]
            },
            {
                "title": "High Volume API Error Rate Spike (HTTP 429/503)",
                "description": f"Client IP {attacker_ip_3} generated 25+ failed rate-limited requests within 60 seconds.",
                "severity": "MEDIUM",
                "status": AlertStatus.RESOLVED.value,
                "detection_source": DetectionSource.RULE.value,
                "risk_score": 52,
                "risk_level": "MODERATE",
                "app": payment_app,
                "detected_at": generate_time(38),
                "ti_indicator": ti_indicators[3]
            },
            {
                "title": "Suspicious User Agent Scraper Probing Endpoints",
                "description": "Known security scanner user-agent header detected on public billing routes.",
                "severity": "LOW",
                "status": AlertStatus.RESOLVED.value,
                "detection_source": DetectionSource.RULE.value,
                "risk_score": 28,
                "risk_level": "LOW",
                "app": portal_app,
                "detected_at": generate_time(350),
                "ti_indicator": None
            }
        ]

        created_alerts = []
        for ad in alerts_data:
            existing_alert = db.query(Alert).filter(Alert.title == ad["title"]).first()
            if not existing_alert:
                alert_obj = Alert(
                    title=ad["title"],
                    description=ad["description"],
                    severity=ad["severity"],
                    status=ad["status"],
                    detection_source=ad["detection_source"],
                    risk_score=ad["risk_score"],
                    risk_level=ad["risk_level"],
                    application_id=ad["app"].id,
                    detected_at=ad["detected_at"],
                    acknowledged_at=ad["detected_at"] + timedelta(minutes=5) if ad["status"] in ["ACKNOWLEDGED", "RESOLVED"] else None,
                    resolved_at=ad["detected_at"] + timedelta(minutes=25) if ad["status"] == "RESOLVED" else None,
                    assigned_to=admin.id if ad["status"] in ["ACKNOWLEDGED", "RESOLVED"] else None
                )
                db.add(alert_obj)
                db.commit()
                db.refresh(alert_obj)

                # Link TI indicator if present
                if ad["ti_indicator"]:
                    link = AlertThreatIntel(
                        alert_id=alert_obj.id,
                        threat_intel_indicator_id=ad["ti_indicator"].id
                    )
                    db.add(link)
                    db.commit()
                created_alerts.append(alert_obj)
                print(f"  -> Created alert: {alert_obj.title} ({alert_obj.severity})")
            else:
                created_alerts.append(existing_alert)

        # 9. Correlation & Attack Chain
        print("\n[*] Correlating Alerts into Multi-Stage Attack Chains...")
        corr_hash = hashlib.sha256(f"{attacker_ip_1}_{payment_app.id}_exfil_chain".encode()).hexdigest()
        existing_corr = db.query(Correlation).filter(Correlation.unique_hash == corr_hash).first()
        if not existing_corr:
            corr_obj = Correlation(
                name="Distributed Brute Force & Data Exfiltration Attack Chain",
                description=f"Multi-phase kill chain originating from {attacker_ip_1}: Initial credential brute force -> Privilege elevation -> Mass archive export.",
                severity="CRITICAL",
                status=CorrelationStatus.DETECTED.value,
                risk_score=95,
                risk_level="CRITICAL",
                application_id=payment_app.id,
                rule_id=corr_rule.id if corr_rule else None,
                first_event_at=generate_time(120),
                last_event_at=generate_time(101),
                unique_hash=corr_hash
            )
            db.add(corr_obj)
            db.commit()
            db.refresh(corr_obj)

            # Link correlated alerts
            for pos, alert in enumerate(created_alerts[:3]):
                db.execute(correlation_alerts.insert().values(
                    correlation_id=corr_obj.id,
                    alert_id=alert.id,
                    sequence_position=pos + 1
                ))
            db.commit()
            print(f"  -> Created correlation: {corr_obj.name}")

        # 10. Incidents
        print("\n[*] Generating Security Incidents...")
        incidents_specs = [
            {
                "incident_number": "INC-2026-001",
                "title": "CRITICAL - Active Account Takeover & Database Exfiltration",
                "description": f"An attacker successfully compromised administrative credentials from IP {attacker_ip_1} and initiated large database export operations.",
                "severity": "CRITICAL",
                "status": IncidentStatus.INVESTIGATING.value,
                "risk_score": 96,
                "app": payment_app,
                "detected_at": generate_time(110),
                "assigned_to": admin.id,
                "comments": [
                    "SOC Analyst: Identified rapid credential stuffing breach from known botnet IP 198.51.100.23.",
                    "SOC Lead: Requested emergency token revocation and egress blocking on payment gateway."
                ]
            },
            {
                "incident_number": "INC-2026-002",
                "title": "HIGH - Multi-Vector SQL Injection Probe on Customer Portal",
                "description": f"Targeted SQLMap scanning detected against customer and invoice query APIs originating from Tor exit node {attacker_ip_2}.",
                "severity": "HIGH",
                "status": IncidentStatus.CONTAINED.value,
                "risk_score": 82,
                "app": portal_app,
                "detected_at": generate_time(85),
                "assigned_to": admin.id,
                "comments": [
                    "WAF rule updated to immediately drop all traffic matching Tor exit node ASN.",
                    "No database leakage confirmed via read replica audit logs."
                ]
            },
            {
                "incident_number": "INC-2026-003",
                "title": "MEDIUM - Volumetric API Denial of Service Precursor",
                "description": f"Automated scanner attempting resource exhaustion on payment transaction endpoint from {attacker_ip_3}.",
                "severity": "MEDIUM",
                "status": IncidentStatus.RESOLVED.value,
                "risk_score": 55,
                "app": payment_app,
                "detected_at": generate_time(42),
                "assigned_to": admin.id,
                "comments": [
                    "Distributed Redis sliding-window rate limiting automatically throttled source IP to 0 req/sec."
                ]
            }
        ]

        for inc_spec in incidents_specs:
            existing_inc = db.query(Incident).filter(Incident.incident_number == inc_spec["incident_number"]).first()
            if not existing_inc:
                inc_obj = Incident(
                    incident_number=inc_spec["incident_number"],
                    title=inc_spec["title"],
                    description=inc_spec["description"],
                    severity=inc_spec["severity"],
                    status=inc_spec["status"],
                    risk_score=inc_spec["risk_score"],
                    application_id=inc_spec["app"].id,
                    assigned_to=inc_spec["assigned_to"],
                    detected_at=inc_spec["detected_at"],
                    contained_at=inc_spec["detected_at"] + timedelta(minutes=15) if inc_spec["status"] in ["CONTAINED", "RESOLVED"] else None,
                    resolved_at=inc_spec["detected_at"] + timedelta(minutes=30) if inc_spec["status"] == "RESOLVED" else None,
                )
                db.add(inc_obj)
                db.commit()
                db.refresh(inc_obj)

                # Link alerts to incident
                for al in created_alerts[:2]:
                    db.execute(incident_alerts.insert().values(
                        incident_id=inc_obj.id,
                        alert_id=al.id
                    ))

                # Add comments
                for comment_text in inc_spec["comments"]:
                    c_obj = IncidentComment(
                        incident_id=inc_obj.id,
                        user_id=admin.id,
                        comment=comment_text
                    )
                    db.add(c_obj)
                db.commit()
                print(f"  -> Created incident: {inc_obj.incident_number} - {inc_obj.title}")

        # 11. Machine Learning Anomaly Detection Model
        print("\n[*] Initializing Machine Learning Anomaly Detection Model...")
        existing_model = db.query(MLModel).filter(MLModel.name == "Payment Gateway Transaction IsolationForest").first()
        if not existing_model:
            ml_obj = MLModel(
                name="Payment Gateway Transaction IsolationForest",
                model_type="ISOLATION_FOREST",
                feature_version="v2.1",
                application_id=payment_app.id,
                status=MLModelStatus.ACTIVE.value,
                trained_at=generate_time(180),
                training_window_start=generate_time(10080),  # 7 days
                training_window_end=generate_time(180),
                training_sample_count=18450,
                parameters={
                    "n_estimators": 100,
                    "contamination": 0.02,
                    "max_features": 8,
                    "random_state": 42
                },
                baseline_statistics={
                    "request_rate_mean": 24.5,
                    "request_rate_std": 6.2,
                    "payload_size_mean_bytes": 1420,
                    "anomaly_threshold_score": -0.62
                },
                model_path="/app/ml_models/payment_gateway_isoforest_v2.joblib"
            )
            db.add(ml_obj)
            db.commit()
            print(f"  -> Created active ML model: {ml_obj.name}")

        # 12. Automated Response Capability & Actions
        print("\n[*] Provisioning Active Response Actions...")
        resp_cap = db.query(ApplicationResponseCapability).filter(ApplicationResponseCapability.application_id == payment_app.id).first()
        if not resp_cap:
            resp_cap = ApplicationResponseCapability(
                application_id=payment_app.id,
                action_type="BLOCK_IP",
                enabled=True,
                configuration={"firewall_type": "iptables_and_waf", "default_duration_hours": 24}
            )
            db.add(resp_cap)
            db.commit()
            db.refresh(resp_cap)

        first_inc = db.query(Incident).filter(Incident.incident_number == "INC-2026-001").first()
        existing_action = db.query(ResponseAction).filter(ResponseAction.target_value == attacker_ip_1).first()
        if not existing_action:
            action_obj = ResponseAction(
                incident_id=first_inc.id if first_inc else None,
                application_id=payment_app.id,
                action_type="BLOCK_IP",
                target_type="IP_ADDRESS",
                target_value=attacker_ip_1,
                status=ResponseActionStatus.APPROVED.value,
                requested_by=admin.id,
                approved_by=admin.id,
                requested_at=generate_time(100),
                approved_at=generate_time(95),
                result_summary="Firewall rule active: Drop all inbound packets from 198.51.100.23",
                metadata_={"duration_hours": 24, "waf_rule_id": "waf_block_981"}
            )
            db.add(action_obj)
            db.commit()
            print(f"  -> Created response action: BLOCK_IP on {attacker_ip_1}")

        # 13. In-App Notifications
        print("\n[*] Emitting Real-Time Analyst Notifications...")
        notif_specs = [
            (NotificationType.CRITICAL_ALERT.value, "CRITICAL Security Alert Triggered", f"Brute Force Account Takeover sequence detected from IP {attacker_ip_1}", "CRITICAL", 95),
            (NotificationType.INCIDENT_CREATED.value, "New Incident Escalated: INC-2026-001", "CRITICAL - Active Account Takeover & Database Exfiltration requires analyst response.", "CRITICAL", 96),
            (NotificationType.THREAT_INTELLIGENCE_MATCH.value, "Known Threat Intel Match", f"Source IP {attacker_ip_2} identified as active Tor Exit Node / Scanner in AlienVault OTX feed.", "HIGH", 85),
        ]

        for n_type, title, msg, sev, r_score in notif_specs:
            notif = Notification(
                user_id=admin.id,
                application_id=payment_app.id,
                notification_type=n_type,
                channel=NotificationChannel.IN_APP.value,
                title=title,
                message=msg,
                severity=sev,
                risk_score=r_score,
                status=NotificationStatus.SENT.value
            )
            db.add(notif)
        db.commit()
        print(f"  -> Dispatched {len(notif_specs)} notifications to {admin.email}.")

        print("\n" + "=" * 60)
        print("  Comprehensive Demo Seeding Completed Successfully!")
        print("  All SentinelSOC tabs are now populated with rich security data.")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"\n[!] Critical Seeding Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
