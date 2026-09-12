from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.api import deps
from app.models.user import User
from app.schemas.ml import MLModelResponse, MLTrainRequest
from app.services.ml_training_service import MLTrainingService
from app.models.ml_model import MLModel

router = APIRouter()

@router.get("/models", response_model=List[MLModelResponse])
def list_models(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("ML_READ")),
    application_id: Optional[UUID] = None
):
    """
    List all ML models, optionally filtered by application.
    """
    query = db.query(MLModel)
    if application_id:
        query = query.filter(MLModel.application_id == application_id)
        
    models = query.order_by(MLModel.created_at.desc()).all()
    return models

@router.get("/models/{model_id}", response_model=MLModelResponse)
def get_model(
    model_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("ML_READ"))
):
    """
    Get detailed information about a specific ML model.
    """
    model = db.query(MLModel).filter(MLModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model

@router.post("/models/train", status_code=status.HTTP_202_ACCEPTED)
def train_model(
    request: MLTrainRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("ML_MANAGE"))
):
    """
    Triggers background training of an ML model for a specific application.
    """
    if request.training_days < 1 or request.training_days > 90:
        raise HTTPException(status_code=400, detail="Training days must be between 1 and 90")
        
    # Schedule the training job in the background to avoid blocking
    background_tasks.add_task(
        MLTrainingService.train_model,
        db=db,
        application_id=request.application_id,
        training_days=request.training_days,
        user_id=current_user.id
    )
    
    return {"message": "Model training triggered in background"}
