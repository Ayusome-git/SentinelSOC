import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.db.session import SessionLocal
from app.services.ml_training_service import MLTrainingService

async def main():
    db = SessionLocal()
    try:
        print("Starting ML Model Training...")
        # Train a global model (no application_id) for the last 7 days
        MLTrainingService.train_model(db=db, application_id=None, training_days=7, user_id=None)
        print("Model training completed successfully.")
    except Exception as e:
        print(f"Error during training: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
