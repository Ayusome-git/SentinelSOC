import requests
import json
import sys
sys.path.insert(0, r"c:\Users\ayush\OneDrive\Desktop\CyberSOC\backend")
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import create_access_token

db = SessionLocal()
user = db.query(User).first()
token = create_access_token(user.id)
db.close()

headers = {"Authorization": f"Bearer {token}"}
response = requests.get("http://localhost:8000/api/v1/dashboard/overview", headers=headers)
if response.status_code == 200:
    data = response.json()
    print(f"Total Events: {data['total_events']}")
    print(f"Critical Events: {data['critical_events']}")
    print(f"High Events: {data['high_events']}")
    print(f"Recent Events (Top 3):")
    for i, e in enumerate(data['recent_events'][:3]):
        print(f"  - {e['event_type']} | {e['severity']} | {e['timestamp']}")
    print(f"Risk Summary: {data['risk_summary']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
