# SentinelSOC Risk Scoring Engine

The Risk Scoring Engine provides a deterministic, mathematically transparent score (from `0` to `100`) for every Alert and Incident. This score strictly dictates the priority in the analyst queue.

## Risk Levels
- **LOW**: 0 - 24
- **MODERATE**: 25 - 49
- **HIGH**: 50 - 74
- **CRITICAL**: 75 - 100

## How the Score is Calculated

The calculation is deterministic. The engine starts at a baseline of `0` and adds points across several distinct risk factors up to a maximum ceiling of `100`.

### 1. Base Severity (Max 40 points)
The raw severity of the underlying events defines the starting baseline.
- `INFO`: +0
- `LOW`: +10
- `MEDIUM`: +20
- `HIGH`: +30
- `CRITICAL`: +40

### 2. Frequency / Volume (Max 15 points)
Higher volumes of events indicate aggressive or automated tooling.
- > 10 events: +5
- > 50 events: +10
- > 100 events: +15

### 3. Attack Type / Category (Max 15 points)
Certain categories inherently pose higher risks than others.
- `Authentication` / `Privilege`: +15 (Highest risk to confidentiality and integrity)
- `Web Attack` / `Injection`: +10
- `Abuse` / `Rate Limit`: +5

### 4. Correlation Context (Max 20 points)
If the engine identifies that this alert belongs to a verified correlation chain (e.g., Brute Force → Successful Login), a massive context multiplier is applied.
- Exists in Correlation Chain: +20

### 5. Enrichment Multipliers (Max 10 points)
Third-party or ML integrations add final confidence weights.
- **Threat Intelligence Match**: +10 (IP is a known malicious actor in AlienVault/VirusTotal).
- **ML Anomaly Detected**: +5 (Behavior strongly deviates from the historical baseline).

## Transparency
The risk score is completely explainable. When viewing an alert, the user interface explicitly breaks down which risk factors contributed to the final score, preventing "black-box" confusion often found in purely ML-driven SOC products.
