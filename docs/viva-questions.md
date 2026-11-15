# Viva Questions & Answers

**Q: What is a SOC?**
A: A Security Operations Center (SOC) is a centralized function or platform within an organization employing people, processes, and technology to continuously monitor and improve an organization's security posture while preventing, detecting, analyzing, and responding to cybersecurity incidents.

**Q: Why did you build SentinelSOC?**
A: To solve the problem of fragmented application logging. Most applications write logs to flat files or basic databases without security context. SentinelSOC provides a unified, intelligent layer that actively evaluates those logs for threats.

**Q: Why is it application-agnostic?**
A: Hardcoding a SOC to a specific application prevents scalability. By exposing a standardized API, SentinelSOC can protect an entire ecosystem of completely different applications (e.g., a React frontend, a mobile app, and a backend microservice) simultaneously.

**Q: How does an application send events?**
A: The external application formats a JSON payload conforming to our schema and POSTs it to the `/api/v1/events` endpoint, authenticating with a scoped API key in the `Authorization` header.

**Q: Why use API keys?**
A: API keys provide a deterministic, easily revocable authentication method designed for machine-to-machine communication, unlike JWTs which are better suited for human user sessions.

**Q: Why not expose the API key in React?**
A: Exposing an API key in client-side code (like React) allows any user to extract it. Attackers could then flood SentinelSOC with fake events. The key must stay on the external application's secure backend.

**Q: How does RBAC work?**
A: Role-Based Access Control assigns permissions based on user roles (VIEWER, ANALYST, ADMIN). SentinelSOC enforces this via JWT claims in the backend, rejecting unauthorized API requests regardless of frontend UI state.

**Q: How does brute-force detection work?**
A: The deterministic detection engine groups `LOGIN_FAILED` events by `source_ip`. If the count of events within a specific sliding time window (e.g., 5 minutes) exceeds a configured threshold, an Alert is generated.

**Q: What is event correlation?**
A: Event correlation is the process of linking distinct, related security alerts and events over time (e.g., a brute-force alert followed immediately by a successful login from the same IP) to identify a broader attack chain.

**Q: Why is correlation different from detection?**
A: Detection looks for immediate, isolated threshold breaches. Correlation happens asynchronously, analyzing the *results* of detections to find relationships across different vectors and timeframes.

**Q: How is risk calculated?**
A: Risk is calculated deterministically from 0 to 100 by aggregating base severity, event frequency, attack category, correlation context, and enrichment modifiers (like TI matches or ML anomalies).

**Q: Why use Isolation Forest?**
A: Isolation Forest is highly effective at identifying outliers (anomalies) in high-dimensional data without requiring labeled training datasets. It perfectly fits SOC use cases where "normal" behavior is common, and "attacks" are rare and distinctly different.

**Q: What is Threat Intelligence?**
A: Threat Intelligence involves querying external datasets (like AlienVault or VirusTotal) to determine if extracted indicators (like IP addresses) are known malicious actors.

**Q: How do you prevent SSRF?**
A: Server-Side Request Forgery is prevented by abstracting Threat Intelligence and Response APIs. The system only connects to explicitly hardcoded, trusted provider domains and does not accept arbitrary URLs from user input.

**Q: Why is human approval required for response?**
A: Automated response actions (like blocking IPs or locking users) carry a high risk of causing unintentional Denial of Service (DoS) if the detection engine misfires. Human-in-the-loop ensures safe execution.

**Q: How do you prevent IDOR/BOLA?**
A: Insecure Direct Object Reference is prevented by enforcing tenant isolation. When fetching data (like an application's events), the backend strictly validates that the requesting user has explicit permission for that specific Application ID.

**Q: Why PostgreSQL / FastAPI / Next.js?**
- **PostgreSQL**: Provides robust ACID compliance and relational integrity, crucial for audit trails.
- **FastAPI**: Offers high concurrency for event ingestion and native data validation via Pydantic.
- **Next.js**: Provides a responsive, component-driven UI capable of static optimization and fast dashboard rendering.
