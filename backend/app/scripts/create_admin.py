import argparse
import getpass
import re
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.core.security import hash_password

def validate_email(email: str) -> bool:
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None

def main():
    print("=== SentinelSOC Initial Administrator Creation ===")
    
    email = input("Email: ").strip().lower()
    if not validate_email(email):
        print("Error: Invalid email format.")
        return
        
    full_name = input("Full Name: ").strip()
    
    password = getpass.getpass("Password: ")
    if len(password) < 8:
        print("Error: Password must be at least 8 characters long.")
        return
        
    confirm_password = getpass.getpass("Confirm Password: ")
    if password != confirm_password:
        print("Error: Passwords do not match.")
        return

    db: Session = SessionLocal()
    try:
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"Error: A user with email {email} already exists.")
            return

        hashed_password = hash_password(password)
        
        admin_user = User(
            email=email,
            password_hash=hashed_password,
            full_name=full_name,
            role=UserRole.ADMIN.value,
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        print(f"Success: Administrator {email} created successfully.")
        
    except Exception as e:
        db.rollback()
        print(f"Error: Failed to create administrator. Details: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
