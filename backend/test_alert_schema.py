import requests
import json

try:
    # Get a user access token for a superadmin (e.g. from tests)
    # Actually, let's bypass auth and test the schema validation directly
    import sys
    sys.path.insert(0, r"c:\Users\ayush\OneDrive\Desktop\CyberSOC\backend")
    from app.db.session import SessionLocal
    from app.models.alert import Alert
    from app.schemas.alert import AlertResponse

    db = SessionLocal()
    alerts = db.query(Alert).all()
    for a in alerts:
        try:
            AlertResponse.model_validate(a)
        except Exception as e:
            print(f"Failed on alert {a.id}: {e}")
            sys.exit(1)
    print("All alerts validated successfully against AlertResponse schema.")

except Exception as e:
    print(f"Error: {e}")
