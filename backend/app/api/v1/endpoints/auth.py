from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.api import deps
from app.core.rate_limit import check_rate_limit
from app.core.security import verify_password, create_access_token
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserResponse

router = APIRouter()

@router.post("/login", response_model=TokenResponse, dependencies=[Depends(check_rate_limit)])
def login_access_token(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(deps.get_db)
) -> TokenResponse:
    """OAuth2 compatible token login, get an access token for future requests."""
    email = login_data.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    if not user or not verify_password(login_data.password, user.password_hash):
        # Create failed login audit
        audit = AuditLog(
            user_id=user.id if user else None,
            action="USER_LOGIN_FAILED",
            ip_address=client_ip,
            user_agent=user_agent,
            details={"email_attempted": email}
        )
        if user:
            db.add(audit)
            db.commit()
        raise HTTPException(status_code=400, detail="Invalid email or password")
        
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)
    
    # Audit log
    audit = AuditLog(
        user_id=user.id,
        action="USER_LOGIN",
        ip_address=client_ip,
        user_agent=user_agent,
        details={"email": email}
    )
    db.add(audit)
    db.commit()

    return TokenResponse(
        access_token=create_access_token(user.id),
        token_type="bearer"
    )

@router.post("/logout")
def logout(
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> dict:
    """Log out a user (stateless, just creates audit log)."""
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    audit = AuditLog(
        user_id=current_user.id,
        action="USER_LOGOUT",
        ip_address=client_ip,
        user_agent=user_agent
    )
    db.add(audit)
    db.commit()
    
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(deps.get_current_user)
) -> UserResponse:
    """Get current user."""
    return current_user
