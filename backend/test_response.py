import asyncio
import os
import sys

# Add the parent directory to sys.path to allow imports from app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.response.validation import validate_action_and_target
from app.models.user import User, UserRole
from app.models.application import Application, AppStatus, AppEnvironment
from app.models.response import ApplicationResponseCapability, ResponseAction, ResponseActionStatus
from app.response.workflow import ResponseWorkflowService
from app.response.execution import ResponseExecutionService
from app.core.config import settings
import uuid

async def main():
    print("--- Testing Validation ---")
    print(f"IP valid? {validate_action_and_target('BLOCK_SOURCE_IP', 'IP_ADDRESS', '192.168.1.10')}")
    print(f"IP invalid? {validate_action_and_target('BLOCK_SOURCE_IP', 'IP_ADDRESS', 'invalid_ip')}")
    print(f"Action mismatch? {validate_action_and_target('REVOKE_SESSION', 'IP_ADDRESS', '192.168.1.10')}")
    print(f"Session valid? {validate_action_and_target('REVOKE_SESSION', 'SESSION_ID', 'sess-1234567890abcdef')}")

    db = SessionLocal()
    try:
        # Get admin user
        admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if not admin:
            admin = User(email="admin_response@test.com", password_hash="dummy", role=UserRole.ADMIN, is_active=True)
            db.add(admin)
            db.commit()
            db.refresh(admin)
            
        # Create test app
        app_id = uuid.uuid4()
        app = Application(
            id=app_id,
            name="Test Response App",
            slug=f"test-resp-{str(app_id)[:8]}",
            owner_id=admin.id,
            environment=AppEnvironment.DEVELOPMENT,
            status=AppStatus.ACTIVE
        )
        db.add(app)
        db.commit()
        
        # Add capability
        cap = ApplicationResponseCapability(
            application_id=app.id,
            action_type="REVOKE_SESSION",
            enabled=True,
            configuration={
                "webhook_url": "http://127.0.0.1:8001/api/security-actions",
                "secret": "super_secret_response_key"
            }
        )
        db.add(cap)
        db.commit()
        
        # 1. Create Action
        from datetime import datetime, timezone
        action = ResponseAction(
            application_id=app.id,
            action_type="REVOKE_SESSION",
            target_type="SESSION_ID",
            target_value="sess-12345678",
            status=ResponseActionStatus.PENDING_APPROVAL,
            requested_by=admin.id,
            requested_at=datetime.now(timezone.utc)
        )
        db.add(action)
        db.commit()
        
        print(f"\nAction created in state: {action.status}")
        
        # 2. Approve Action
        action = ResponseWorkflowService.approve_action(db, action.id, admin.id)
        print(f"Action approved in state: {action.status}")
        
        # 3. Execute Action
        print("\nEnsure test_target_app.py is running on port 8001 to test actual execution.")
        print("Executing action...")
        action = await ResponseExecutionService.execute_action(db, action.id, admin.id)
        print(f"Execution complete. Status: {action.status}")
        print(f"Result summary: {action.result_summary}")
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
