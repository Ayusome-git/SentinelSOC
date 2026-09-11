import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import SessionLocal

db: Session = SessionLocal()
db.execute(text("UPDATE applications SET environment='DEVELOPMENT' WHERE environment='dev'"))
db.execute(text("UPDATE applications SET environment='STAGING' WHERE environment='staging'"))
db.execute(text("UPDATE applications SET environment='PRODUCTION' WHERE environment='prod'"))
db.commit()
print("Fixed application environments.")
