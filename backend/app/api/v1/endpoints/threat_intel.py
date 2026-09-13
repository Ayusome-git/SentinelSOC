from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from uuid import UUID

from app.api import deps
from app.models.user import User
from app.models.threat_intel import ThreatIntelIndicator
from app.schemas.threat_intel import ThreatIntelListResponse, ThreatIntelIndicatorResponse, ThreatIntelLookupRequest, ThreatIntelLookupResponse
from app.threat_intel.service import ThreatIntelEnrichmentService

router = APIRouter()

@router.get("/indicators", response_model=ThreatIntelListResponse)
def list_indicators(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("THREAT_INTEL_READ")),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    indicator_type: Optional[str] = None,
    malicious: Optional[bool] = None,
    search: Optional[str] = None
):
    query = db.query(ThreatIntelIndicator)
    
    if indicator_type:
        query = query.filter(ThreatIntelIndicator.indicator_type == indicator_type)
    if malicious is not None:
        query = query.filter(ThreatIntelIndicator.malicious == malicious)
    if search:
        query = query.filter(ThreatIntelIndicator.indicator.ilike(f"%{search}%"))
        
    total = query.count()
    items = query.order_by(desc(ThreatIntelIndicator.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/indicators/{id}", response_model=ThreatIntelIndicatorResponse)
def get_indicator(
    *,
    db: Session = Depends(deps.get_db),
    id: UUID,
    current_user: User = Depends(deps.require_permission("THREAT_INTEL_READ"))
):
    indicator = db.query(ThreatIntelIndicator).filter(ThreatIntelIndicator.id == id).first()
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    return indicator

@router.post("/lookup", response_model=ThreatIntelLookupResponse)
async def manual_lookup(
    *,
    db: Session = Depends(deps.get_db),
    request: ThreatIntelLookupRequest,
    current_user: User = Depends(deps.require_permission("THREAT_INTEL_MANAGE"))
):
    """
    Perform a real-time manual lookup of an indicator against configured providers.
    Uses cache if available and not expired.
    """
    result = await ThreatIntelEnrichmentService.manual_lookup(
        db=db,
        indicator=request.indicator,
        indicator_type=request.indicator_type
    )
    
    return ThreatIntelLookupResponse(
        found=result.found,
        indicator=result.indicator,
        indicator_type=result.indicator_type,
        malicious=result.malicious,
        confidence=result.confidence,
        reputation=result.reputation,
        categories=result.categories,
        source=result.source,
        first_seen_at=result.first_seen_at,
        last_seen_at=result.last_seen_at,
        reference=result.reference
    )
