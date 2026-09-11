from fastapi import FastAPI, Request, Depends, HTTPException, Header
import os
import sys

# Ensure sdk is in path for the sample app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../sdk/python')))

from sentinelsoc import SentinelLogger

app = FastAPI(title="Sample App integrated with SentinelSOC")

# Initialize Logger. In production, API key should come from env variables
# Run backend first and generate a key, then run sample app with API_KEY=ssk_...
API_KEY = os.environ.get("API_KEY", "ssk_dev_dummy")
SOC_URL = os.environ.get("SOC_URL", "http://localhost:8000")

soc_logger = SentinelLogger(api_key=API_KEY, endpoint=SOC_URL)

def get_client_ip(request: Request) -> str:
    return request.client.host if request.client else "127.0.0.1"

@app.post("/login")
def login(request: Request, username: str = Header(None)):
    if username == "admin":
        soc_logger.log(
            event_type="LOGIN_SUCCESS",
            severity="INFO",
            source_ip=get_client_ip(request),
            message="User logged in successfully",
            username=username,
            request_path="/login",
            http_method="POST",
            metadata={"browser": request.headers.get("user-agent")}
        )
        return {"status": "success"}
    else:
        soc_logger.log(
            event_type="LOGIN_FAILED",
            severity="MEDIUM",
            source_ip=get_client_ip(request),
            message="Failed login attempt",
            username=username,
            request_path="/login",
            http_method="POST",
            metadata={"reason": "Invalid credentials"}
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/logout")
def logout(request: Request, username: str = Header(None)):
    soc_logger.log(
        event_type="LOGOUT",
        severity="INFO",
        source_ip=get_client_ip(request),
        message="User logged out",
        username=username,
        request_path="/logout"
    )
    return {"status": "success"}

@app.post("/admin/settings")
def update_settings(request: Request, username: str = Header(None)):
    if username != "admin":
        soc_logger.log(
            event_type="PERMISSION_DENIED",
            severity="HIGH",
            source_ip=get_client_ip(request),
            message="Unauthorized access to admin settings",
            username=username,
            request_path="/admin/settings",
            http_method="POST"
        )
        raise HTTPException(status_code=403, detail="Forbidden")
        
    soc_logger.log(
        event_type="ADMIN_ACTION",
        severity="MEDIUM",
        source_ip=get_client_ip(request),
        message="Admin updated global settings",
        username=username,
        request_path="/admin/settings"
    )
    return {"status": "settings updated"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
