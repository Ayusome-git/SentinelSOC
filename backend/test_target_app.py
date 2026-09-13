from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import uvicorn
import asyncio

app = FastAPI(title="Sample Target Application for Response Testing")

SHARED_SECRET = "super_secret_response_key"

class Target(BaseModel):
    type: str
    value: str

class SecurityActionRequest(BaseModel):
    action: str
    target: Target
    request_id: str

# In-memory idempotency cache
processed_requests = set()

@app.post("/api/security-actions")
async def handle_security_action(request: SecurityActionRequest, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = authorization.split(" ")[1]
    if token != SHARED_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")
        
    if request.request_id in processed_requests:
        return {"status": "success", "message": f"Action {request.action} already executed for {request.target.value} (Idempotent)"}
        
    # Simulate work
    await asyncio.sleep(0.5)
    
    # Process the action
    processed_requests.add(request.request_id)
    
    return {
        "status": "success",
        "message": f"Successfully executed {request.action} on {request.target.type} '{request.target.value}'"
    }

if __name__ == "__main__":
    print("Starting Sample Target Application on port 8001...")
    print(f"Configure ApplicationResponseCapability with webhook_url='http://localhost:8001/api/security-actions' and secret='{SHARED_SECRET}'")
    uvicorn.run(app, host="127.0.0.1", port=8001)
