from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.core.security import hash_password, create_access_token
from app.models.detection_rule import DetectionRule
from app.models.alert import Alert
from app.models.application import Application, AppStatus
from app.models.application_api_key import ApplicationApiKey
from app.core.api_key import generate_api_key
import datetime

client = TestClient(app)

def run_simulation():
    db = SessionLocal()
    
    # 1. Ensure admin user exists
    admin = db.query(User).filter(User.email == "sim_admin@soc.com").first()
    if not admin:
        admin = User(
            email="sim_admin@soc.com",
            password_hash=hash_password("admin"),
            full_name="Sim Admin",
            role=UserRole.ADMIN.value,
            is_active=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

    # 2. Ensure application and API key exist
    app_db = db.query(Application).filter(Application.name == "Sim App").first()
    if not app_db:
        app_db = Application(name="Sim App", slug="sim-app", status=AppStatus.ACTIVE.value, environment="dev", owner_id=admin.id)
        db.add(app_db)
        db.commit()
        db.refresh(app_db)
        
    api_key_db = db.query(ApplicationApiKey).filter(ApplicationApiKey.application_id == app_db.id).first()
    if not api_key_db:
        raw_key, key_prefix, key_hash = generate_api_key("dev")
        api_key_db = ApplicationApiKey(
            application_id=app_db.id,
            name="Sim Key",
            key_prefix=key_prefix,
            key_hash=key_hash,
            is_active=True,
            created_by=admin.id
        )
        db.add(api_key_db)
        db.commit()
        db.refresh(api_key_db)
    else:
        # We don't have the raw key, so we need to recreate one
        db.delete(api_key_db)
        raw_key, key_prefix, key_hash = generate_api_key("dev")
        api_key_db = ApplicationApiKey(
            application_id=app_db.id,
            name="Sim Key",
            key_prefix=key_prefix,
            key_hash=key_hash,
            is_active=True,
            created_by=admin.id
        )
        db.add(api_key_db)
        db.commit()

    token = create_access_token(admin.id)
    auth_headers = {"Authorization": f"Bearer {token}"}
    api_headers = {"X-API-Key": raw_key}
    
    # 2. Clear old alerts and rules
    db.query(Alert).delete()
    db.query(DetectionRule).filter(DetectionRule.name == "Sim Rule").delete()
    db.commit()

    # 3. Seed Rule
    rule = DetectionRule(
        name="Sim Rule",
        description="Simulate Failed Logins",
        rule_type="THRESHOLD",
        enabled=True,
        severity="HIGH",
        event_type="LOGIN_FAILED",
        threshold=5,
        window_seconds=300,
        group_by="source_ip",
        application_id=app_db.id
    )
    db.add(rule)
    db.commit()

    print(f"Created rule: {rule.name}")

    # 4. Ingest failed logins (5 from 10.0.0.1)
    print("Ingesting 5 failed logins for 10.0.0.1...")
    for _ in range(5):
        resp = client.post(
            "/api/v1/events/",
            headers=api_headers,
            json={
                "event_type": "LOGIN_FAILED",
                "severity": "LOW",
                "message": "Failed login",
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                "source_ip": "10.0.0.1",
                "details": {"user": "admin"}
            }
        )
        assert resp.status_code == 201, f"Failed to ingest: {resp.text}"
    
    # 5. Check alerts via DB
    alerts = db.query(Alert).filter(Alert.application_id == app_db.id).all()
    print(f"Total alerts: {len(alerts)}")
    for a in alerts:
        print(f" - {a.title}")

    # 6. Duplicate suppression: Ingest 3 more from 10.0.0.1
    print("Ingesting 3 more failed logins for 10.0.0.1...")
    for _ in range(3):
        resp = client.post(
            "/api/v1/events/",
            headers=api_headers,
            json={
                "event_type": "LOGIN_FAILED",
                "severity": "LOW",
                "message": "Failed login",
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                "source_ip": "10.0.0.1",
                "details": {"user": "admin"}
            }
        )
        assert resp.status_code == 201

    alerts2 = db.query(Alert).filter(Alert.application_id == app_db.id).all()
    print(f"Total alerts after 3 more events: {len(alerts2)}")
    
    # Clean up
    db.query(Alert).delete()
    db.query(DetectionRule).filter(DetectionRule.name == "Sim Rule").delete()
    db.delete(admin)
    db.commit()

if __name__ == "__main__":
    run_simulation()
