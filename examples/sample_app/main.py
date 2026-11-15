from fastapi import FastAPI, Request, Depends, HTTPException, Header, BackgroundTasks
import os
import sys
import time
import random

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

@app.post("/webhook")
async def handle_webhook(request: Request, authorization: str = Header(None)):
    if not authorization or authorization != "Bearer secret-123":
        raise HTTPException(status_code=401, detail="Unauthorized webhook call")
        
    data = await request.json()
    action = data.get("action")
    target = data.get("target", {})
    
    soc_logger.log(
        event_type="RESPONSE_ACTION_EXECUTED",
        severity="INFO",
        source_ip="127.0.0.1",
        message=f"Executed {action} on {target.get('type')}: {target.get('value')}",
        request_path="/webhook"
    )
    
    return {"message": f"Successfully blocked {target.get('value')}!"}

# --- DEMONSTRATION ENDPOINTS ---

def run_attack_simulation(attack_type: str, base_ip: str):
    print(f"Starting simulation for: {attack_type}")
    
    if attack_type == "brute_force":
        for i in range(6):
            soc_logger.log(
                event_type="LOGIN_FAILED", severity="MEDIUM", source_ip=base_ip,
                message=f"Failed login attempt {i+1}", username="admin", request_path="/login"
            )
            time.sleep(0.5)
            
    elif attack_type == "credential_stuffing":
        usernames = ["john", "jane", "admin", "test", "root", "guest"]
        for u in usernames:
            soc_logger.log(
                event_type="LOGIN_FAILED", severity="MEDIUM", source_ip=base_ip,
                message=f"Failed login attempt for {u}", username=u, request_path="/login"
            )
            time.sleep(0.5)
            
    elif attack_type == "password_spray":
        for i in range(6):
            spoofed_ip = f"10.0.0.{100+i}"
            soc_logger.log(
                event_type="LOGIN_FAILED", severity="MEDIUM", source_ip=spoofed_ip,
                message="Failed login attempt for admin", username="admin", request_path="/login"
            )
            time.sleep(0.5)
            
    elif attack_type == "privilege_escalation":
        # 1. Permission Denied
        soc_logger.log(
            event_type="PERMISSION_DENIED", severity="HIGH", source_ip=base_ip,
            message="Unauthorized access to admin settings", username="hacker1", request_path="/admin/settings"
        )
        time.sleep(2)
        # 2. Admin Action (escalation)
        soc_logger.log(
            event_type="ADMIN_ACTION", severity="CRITICAL", source_ip=base_ip,
            message="Admin updated global settings", username="hacker1", request_path="/admin/settings"
        )
        
    elif attack_type == "sql_injection":
        soc_logger.log(
            event_type="API_REQUEST", severity="HIGH", source_ip=base_ip,
            message="Database query executed", request_path="/api/products?search=' OR 1=1 --", http_method="GET"
        )
        
    elif attack_type == "xss_attack":
        soc_logger.log(
            event_type="API_REQUEST", severity="HIGH", source_ip=base_ip,
            message="Comment submitted", request_path="/api/comments?body=<script>alert(1)</script>", http_method="POST"
        )
        
    elif attack_type == "path_traversal":
        soc_logger.log(
            event_type="API_REQUEST", severity="HIGH", source_ip=base_ip,
            message="File download requested", request_path="/api/download?file=../../../../etc/passwd", http_method="GET"
        )
        
    elif attack_type == "api_abuse":
        for i in range(110):
            soc_logger.log(
                event_type="API_REQUEST", severity="INFO", source_ip=base_ip,
                message=f"Bulk request {i}", request_path="/api/data"
            )
            
    print(f"Finished simulation for: {attack_type}")


@app.post("/simulate_attack/{attack_type}")
def simulate_attack(attack_type: str, request: Request, background_tasks: BackgroundTasks):
    valid_attacks = [
        "brute_force", "credential_stuffing", "password_spray", 
        "privilege_escalation", "sql_injection", "xss_attack", 
        "path_traversal", "api_abuse"
    ]
    if attack_type not in valid_attacks:
        raise HTTPException(status_code=400, detail=f"Invalid attack type. Choose from: {valid_attacks}")
        
    background_tasks.add_task(run_attack_simulation, attack_type, get_client_ip(request))
    return {"status": "simulation_started", "attack_type": attack_type, "note": "Check your SentinelSOC dashboard."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
