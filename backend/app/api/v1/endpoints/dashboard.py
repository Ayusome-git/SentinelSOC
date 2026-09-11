from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta, timezone

from app.api import deps
from app.schemas.dashboard import DashboardOverviewResponse
from app.services.dashboard_service import get_dashboard_overview
from app.models.user import User

router = APIRouter()

@router.get("/overview", response_model=DashboardOverviewResponse)
def get_dashboard_overview_endpoint(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("EVENTS_READ")),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """
    Get SOC Command Center overview metrics.
    Requires EVENTS_READ permission.
    """
    if not end_date:
        end_date = datetime.now(timezone.utc)
    if not start_date:
        start_date = end_date - timedelta(hours=24)
        
    # Prevent enormous queries
    if (end_date - start_date).days > 90:
        raise HTTPException(status_code=400, detail="Time range cannot exceed 90 days")

    return get_dashboard_overview(db=db, start_date=start_date, end_date=end_date)
