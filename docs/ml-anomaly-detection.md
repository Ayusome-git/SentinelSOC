# Machine Learning Anomaly Detection

SentinelSOC incorporates an unsupervised Machine Learning subsystem designed to detect deviations from established baselines that deterministic rules might miss.

> [!IMPORTANT]
> Machine Learning in SentinelSOC acts strictly as an **additional detection layer**. It does not replace the deterministic, threshold-based detection rules. It solely serves to enrich investigations and marginally adjust risk scores.

## Algorithm: Isolation Forest
SentinelSOC utilizes the `Isolation Forest` algorithm provided by `scikit-learn`. 

Isolation Forest is explicitly designed for anomaly detection. Unlike algorithms that try to map out the shape of "normal" data, Isolation Forest attempts to isolate anomalies by randomly partitioning data. Since anomalies are "few and different," they require fewer partitions to be isolated (resulting in shorter path lengths).

## Feature Extraction & Windowing
The model does not train on raw textual logs. Instead, it extracts aggregated, time-windowed numeric features:
- Event count per window (e.g., 5-minute buckets)
- Count of unique Source IPs
- Count of unique User IDs
- Distribution of Severity levels (Low, Medium, High, Critical)
- Count of distinct Event Types

## Model Lifecycle
1. **Cold Start**: Initially, the model requires historical data (e.g., 7 days or 1000 minimum samples). It remains in a `COLD_START` state until this threshold is met.
2. **Training**: A background task (configurable via `ML_TRAINING_DAYS` in `.env`) periodically queries the PostgreSQL database, extracts the features, and trains the model.
3. **Persistence**: The model is serialized (`.pkl`) and stored in the localized `ml_models` volume to survive container restarts.
4. **Inference**: During ingestion, if the ML system is active, events are passed through the model. 

## Anomaly Scoring
The Isolation Forest outputs an anomaly score ranging from -1 to 1. SentinelSOC normalizes this internally into a standard `0-100` Anomaly Score. 
If the score crosses `ML_ANOMALY_THRESHOLD` (default 75), the event is flagged as anomalous. This flag is surfaced in the Event Explorer and increases the deterministic Risk Score of any associated alerts by +5 points.

## Limitations
- **Data Dependency**: The model is highly dependent on sufficient "normal" historical data. If the application is brand new, the model cannot function immediately.
- **Concept Drift**: Application patterns change (e.g., legitimate marketing campaigns causing traffic spikes). The model must be continuously retrained to incorporate new baselines.
