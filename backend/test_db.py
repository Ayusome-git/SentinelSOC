import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("DATABASE_URL")
print(f"Testing connection to: {db_url}")

try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        print("SUCCESS! Successfully connected to the database.")
except Exception as e:
    print(f"FAILED to connect to the database. Error: {e}")
