import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.db.session import SessionLocal
from app.services.ml_anomaly_service import MLAnomalyDetectionService

async def main():
    db = SessionLocal()
    try:
        print("Testing ML Anomaly Detection...")
        MLAnomalyDetectionService.trigger_detection_for_latest_window(db=db, application_id=None)
        print("Detection completed successfully.")
    except Exception as e:
        print(f"Error during detection: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
