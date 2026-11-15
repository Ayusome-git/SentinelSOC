import requests

payload = {
    "event_type": "API_REQUEST",
    "severity": "HIGH",
    "message": "API request payload matching XSS pattern",
    "username": "anonymous",
    "request_path": "/api/comments?body=<script>alert(1)</script>",
    "http_method": "POST"
}
try:
    response = requests.post("http://localhost:8080/api/telemetry", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
