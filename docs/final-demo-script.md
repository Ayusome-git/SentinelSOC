# SentinelSOC Final Demo Script

This script provides a step-by-step walkthrough for demonstrating the end-to-end capabilities of the SentinelSOC platform, proving its readiness for production security monitoring and academic evaluation.

## Prerequisites
1. Ensure the PostgreSQL database is running and seeded.
2. Start the SentinelSOC backend API: `cd backend && uvicorn app.main:app --reload`
3. Start the SentinelSOC frontend: `cd frontend && npm run dev`
4. Start the MANIT Marketplace Demo target app: `cd manit-marketplace-demo && node server.js`

## Demo Steps

### Part 1: The SOC Dashboard (The Defender's View)
1. **Login**: Navigate to `http://localhost:3000` and log in as an administrator.
2. **Dashboard Overview**: Explain the layout—High Severity Alerts, Recent Incidents, and the Threat Map. Point out the live telemetry stream if configured.
3. **Detection Rules**: Navigate to Settings > Detection Rules. Show the diverse pre-configured rules (Brute Force, Credential Stuffing, SQLi, XSS, Path Traversal, Privilege Escalation).

### Part 2: Attacking the Target (The Attacker's View)
1. Open a terminal and navigate to the backend directory (`cd backend`).
2. **Run Scenario 1 (Brute Force)**:
   ```bash
   python -m app.scripts.security_scenarios run brute-force
   ```
   *Explanation*: "An attacker is attempting to guess the admin password from IP 10.0.0.1 by sending 20 rapid failed login requests."
3. **Run Scenario 3 (Credential Stuffing)**:
   ```bash
   python -m app.scripts.security_scenarios run credential-stuffing
   ```
   *Explanation*: "An attacker has a leaked password database and is trying the same password across 10 different user accounts."
4. **Run Scenario 5 (Privilege Escalation)**:
   ```bash
   python -m app.scripts.security_scenarios run privilege-abuse
   ```
   *Explanation*: "A compromised normal user repeatedly tries to access admin settings, and suddenly succeeds, indicating a privilege escalation exploit."

### Part 3: Detection and Response (Closing the Loop)
1. **Return to the SOC Dashboard**.
2. **View Alerts**: Navigate to the Alerts page. Show the newly generated alerts matching the attacks just executed:
   - `Brute Force Login Attempt` (Score ~67)
   - `Credential Stuffing Detected` (Score ~70)
   - `Privilege Escalation Indicator` (Score 95 - Critical)
3. **Analyze Incident Details**: Click on the `Privilege Escalation Indicator`. Show how the SentinelSOC Risk Engine dynamically scored the event at 95 (CRITICAL) because it detected a sequence of "Permission Denied" followed by an "Admin Action".
4. **Demonstrate Extensibility**: Briefly mention the ML Anomaly Detection engine (`IsolationForest`) and Threat Intelligence pipelines that run in the background.

## Cleanup
To reset the demonstration environment to a clean state for the next presentation:
```bash
python -m app.scripts.security_scenarios reset
```
