# SentinelSOC Demo Runbook

This guide dictates a deterministic, repeatable demonstration of the SentinelSOC pipeline using synthetic data.

## Environment Preparation

### 1. Start the Environment
Ensure the local development environment is running cleanly:
```bash
docker compose up -d
```

### 2. Login
Open your browser to `http://localhost:3000`. Login using your Administrator credentials.

## Demonstration Flow

### STEP 1: Introduction (Applications)
1. Navigate to the **Applications** view.
2. Point out the `SentinelSOC Demo Application` (or register one if it's a completely fresh instance).
3. Explain that SentinelSOC is application-agnostic and relies on Applications generating API Keys to securely ingest events.

### STEP 2: The Attack (Synthetic Scenario)
1. Open a terminal to your backend container:
   ```bash
   docker exec -it sentinelsoc_backend_dev bash
   ```
2. Execute the safe demo seeding script:
   ```bash
   python -m app.scripts.seed_demo_scenario --scenario brute-force-to-admin
   ```
3. *Narrative*: "An attacker is currently targeting our Demo Application. They are attempting to brute force a user account, and if successful, they will attempt to pivot to administrative functions."

### STEP 3: Event Explorer
1. Navigate to **Events** on the sidebar.
2. Show the influx of new events.
3. Highlight the ~15 `LOGIN_FAILED` events originating from a single IP.
4. *Narrative*: "SentinelSOC has ingested these raw events and normalized them. Individually, they are just noisy failed logins."

### STEP 4: Detection & Alerts
1. Navigate to **Alerts**.
2. Show the newly generated `Brute Force Login` alert.
3. *Narrative*: "Our deterministic detection engine identified the threshold breach (5 failures in 5 minutes) and automatically generated an Alert."

### STEP 5: The Pivot
1. Return to **Events**.
2. Point out the `LOGIN_SUCCESS` event, followed shortly by an `ADMIN_ACTION`.
3. *Narrative*: "The attacker succeeded in guessing the password and has now begun attempting administrative actions."

### STEP 6: Correlation & Risk
1. Return to **Alerts** and open the specific Brute Force alert detail page.
2. *Narrative*: "Because the Correlation Engine runs asynchronously, it recognized the successful login and admin activity originating from the same IP that caused the Brute Force."
3. Highlight the Risk Score.
4. *Narrative*: "The Risk Scoring Engine evaluated this correlated chain. Because it involves Authentication and Privilege escalation, the risk is calculated deterministically as a **CRITICAL** (e.g., 90/100) score."

### STEP 7: Incident Investigation
1. Navigate to **Incidents**.
2. Open the newly escalated Incident.
3. Show the chronological **Timeline**.
4. *Narrative*: "The critical risk caused the system to automatically escalate the alert into an Incident. Analysts can use this workspace to view the entire attack chain chronologically."

### STEP 8: Enrichment
1. Show the **Threat Intelligence** module (if configured with keys).
2. *Narrative*: "The system queried the Source IP against AlienVault. We can see it matched a known botnet list, adding context to the incident."
3. Explain the **Machine Learning** module. 
4. *Narrative*: "While this attack was caught deterministically, our ML Isolation Forest continually evaluates baselines to catch unknown 'Zero Day' anomalies."

### STEP 9: Controlled Response
1. Within the Incident, click **Request Response**.
2. Request a `BLOCK_SOURCE_IP` action.
3. Show that the status is `PENDING APPROVAL`.
4. *Narrative*: "To prevent accidental Denial of Service, response actions require human approval."
5. As an Administrator, click **Approve**.
6. Show the status change to `EXECUTING`, then `SUCCEEDED`.

### STEP 10: Reporting
1. Navigate to **Reports**.
2. Generate a new report for the current week.
3. *Narrative*: "Finally, managers can generate PDF or CSV reports detailing the volume of events, severe incidents, and response times over the period."
