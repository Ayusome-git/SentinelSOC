import sys
sys.path.insert(0, r"c:\Users\ayush\OneDrive\Desktop\CyberSOC\backend")

from app.db.session import engine
from sqlalchemy import MetaData

metadata = MetaData()
metadata.reflect(bind=engine)

tables = list(metadata.tables.keys())
print(f"Total tables: {len(tables)}")
for t in sorted(tables):
    print(f"- {t}")
