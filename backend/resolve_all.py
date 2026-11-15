import sys

sys.path.insert(0, r"c:\Users\ayush\OneDrive\Desktop\CyberSOC\backend")

from app.db.session import SessionLocal
from app.models.alert import Alert, AlertStatus

db = SessionLocal()

open_alerts = db.query(Alert).filter(Alert.status.in_([AlertStatus.OPEN.value, AlertStatus.ACKNOWLEDGED.value])).all()
count = 0
for a in open_alerts:
    a.status = AlertStatus.RESOLVED.value
    count += 1

db.commit()
print(f"Resolved {count} alerts.")
db.close()
