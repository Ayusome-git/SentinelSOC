from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.incident_sequence import IncidentSequence

class IncidentSequenceService:
    @staticmethod
    def generate_incident_number(db: Session) -> str:
        """
        Safely generates a sequential incident number like INC-000001
        """
        # Try to use RETURNING clause for atomic update (Postgres/SQLite > 3.35)
        # We will use raw SQL to ensure it increments safely.
        result = db.execute(
            text("""
                UPDATE incident_sequences 
                SET last_value = last_value + 1 
                WHERE id = 'INCIDENT' 
                RETURNING last_value
            """)
        )
        row = result.fetchone()
        
        # If the row doesn't exist, create it (first time setup)
        if not row:
            db.execute(text("INSERT INTO incident_sequences (id, last_value) VALUES ('INCIDENT', 1)"))
            val = 1
        else:
            val = row[0]
            
        # Do not commit here, allow the caller's transaction to handle it
        # This keeps the increment tied to the incident creation transaction
        return f"INC-{val:06d}"
