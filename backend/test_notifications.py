import asyncio
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import create_access_token
import httpx

async def test_endpoint():
    db = SessionLocal()
    user = db.query(User).first()
    if not user:
        print("No user found.")
        return
    
    token = create_access_token(subject=str(user.id))
    db.close()
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v1/notifications?page=1&size=5&is_read=false",
            headers={"Authorization": f"Bearer {token}"}
        )
        print("STATUS:", response.status_code)
        print("BODY:", response.text)

if __name__ == "__main__":
    asyncio.run(test_endpoint())
