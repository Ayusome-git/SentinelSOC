from pptx import Presentation
from pptx.util import Inches, Pt

def create_presentation(filename="SentinelSOC_Presentation.pptx"):
    prs = Presentation()

    # Define slide layouts
    title_slide_layout = prs.slide_layouts[0]
    bullet_slide_layout = prs.slide_layouts[1]

    # Slide 1: Title Slide
    slide = prs.slides.add_slide(title_slide_layout)
    title = slide.shapes.title
    subtitle = slide.placeholders[1]
    title.text = "SentinelSOC: Advanced Security Operations Center"
    subtitle.text = "Centralized Logging, Threat Detection & Investigation Workspace\n\nPrepared for Presentation"
    
    # Speaker notes for Slide 1
    notes_slide = slide.notes_slide
    text_frame = notes_slide.notes_text_frame
    text_frame.text = "Hello everyone. Today I'll be presenting SentinelSOC, a centralized Security Operations Center designed to normalize event logging, automate threat detection, and provide a unified workspace for security analysts."

    # Function to add bullet slides
    def add_bullet_slide(title_text, bullet_points, speaker_notes):
        slide = prs.slides.add_slide(bullet_slide_layout)
        shapes = slide.shapes
        title_shape = shapes.title
        body_shape = shapes.placeholders[1]
        
        title_shape.text = title_text
        
        tf = body_shape.text_frame
        tf.clear()
        for point in bullet_points:
            p = tf.add_paragraph()
            p.text = point
            p.font.size = Pt(22)
            p.space_after = Pt(14)
            p.level = 0
            
        notes = slide.notes_slide
        notes.notes_text_frame.text = speaker_notes

    # Slide 2: The Security Challenge
    add_bullet_slide(
        "The Security Challenge",
        [
            "Disconnected security events across disparate applications.",
            "Inability to detect complex, multi-stage attack chains manually.",
            "Overwhelming alert fatigue and slow incident response times.",
            "Need for a unified, application-agnostic monitoring solution."
        ],
        "Organizations today face major challenges: security events are scattered across different apps, alert fatigue overwhelms analysts, and detecting multi-stage attacks is nearly impossible manually. We built SentinelSOC to solve these specific problems."
    )

    # Slide 3: What is SentinelSOC?
    add_bullet_slide(
        "What is SentinelSOC?",
        [
            "A high-performance, centralized Security Operations Center.",
            "Standardizes event ingestion from multiple tenant applications.",
            "Strict Multi-Tenant isolation using scoped API Keys and RBAC.",
            "Provides a unified workspace for investigating and mitigating threats."
        ],
        "SentinelSOC acts as the central hub. It ingests events from any application, ensures strict multi-tenant isolation, and provides analysts with a single pane of glass to investigate threats."
    )

    # Slide 4: Key Capabilities
    add_bullet_slide(
        "Key Capabilities",
        [
            "Rule-Based Detection: Deterministic evaluation of events (e.g., Brute Force).",
            "Automated Correlation: Asynchronously stitches events into cohesive attack chains.",
            "ML Anomaly Detection: Detects statistical deviations using Unsupervised Learning.",
            "Threat Intelligence: Out-of-the-box IP enrichment via AlienVault and VirusTotal.",
            "Controlled Response Actions: Human-in-the-loop approval workflows."
        ],
        "The core engine runs on deterministic rules, automated correlation, and Machine Learning. It automatically enriches IP indicators via Threat Intel and allows analysts to take controlled response actions back onto the originating application."
    )

    # Slide 5: System Architecture
    add_bullet_slide(
        "Modern Technology Stack",
        [
            "Frontend: Next.js 14, React 18, Tailwind CSS, TypeScript.",
            "Backend: Python 3.13, FastAPI, SQLAlchemy, scikit-learn.",
            "Database: PostgreSQL 15 for relational source-of-truth.",
            "Infrastructure: Containerized via Docker and NGINX.",
            "Clean separation of concerns with asynchronous background workers."
        ],
        "Our stack is built for scale and performance. We use FastAPI and asyncio for a high-concurrency ingestion engine, Next.js for a responsive dashboard, and PostgreSQL for our source of truth. Everything is containerized with Docker."
    )

    # Slide 6: Machine Learning Integration
    add_bullet_slide(
        "Machine Learning Anomaly Detection",
        [
            "Algorithm: Unsupervised Isolation Forest models.",
            "Purpose: Detects statistical deviations from established normal baselines.",
            "Process: Dynamically extracts features over rolling time windows.",
            "Output: Deterministic, explainable anomaly scores and high-fidelity alerts."
        ],
        "To detect unknown threats, we use Isolation Forests. Instead of relying purely on static rules, this unsupervised model learns the baseline of normal behavior and isolates anomalies, providing explainable scores when deviations occur."
    )

    # Slide 7: Threat Detection & Correlation
    add_bullet_slide(
        "Detecting Attack Chains",
        [
            "Rule Engine: Threshold-based triggers (Impossible Travel, API Spikes).",
            "Correlation Engine: Background workers group distinct events into unified incidents.",
            "Risk Scoring: Deterministic 0-100 scoring prioritizes critical threats.",
            "Result: Drastically reduces alert fatigue by highlighting real incidents."
        ],
        "Individual events often don't tell the whole story. Our correlation engine stitches disparate events together into attack chains. We then apply a deterministic 0-100 risk score so analysts know exactly what to focus on first."
    )

    # Slide 8: Investigation & Response
    add_bullet_slide(
        "Incident Response & Mitigation",
        [
            "Unified Dashboard: Comprehensive view of alerts, events, and incidents.",
            "Containment Actions: Execute IP Blocks and User Lockouts instantly.",
            "Approval Workflows: Human-in-the-loop validation for critical automated actions.",
            "Reporting: Automated PDF/CSV security posture reporting."
        ],
        "Once an incident is identified, analysts can take action directly from the dashboard. They can trigger IP blocks or user lockouts, requiring human approval for critical actions to prevent operational disruption."
    )

    # Slide 9: Security Best Practices
    add_bullet_slide(
        "Built-In Security Protections",
        [
            "Authentication: Argon2id Password Hashing, short-lived JWT authentication.",
            "Tenant Isolation: Strict IDOR/BOLA protection per tenant.",
            "Traffic Protection: Internal rate-limiting and payload size caps.",
            "Network Security: Strict SSRF protections on Threat Intelligence integrations."
        ],
        "Security is built-in by design. We use Argon2id for hashing, enforce strict tenant isolation to prevent data leakage, and implement internal rate-limiting and SSRF protections."
    )

    # Slide 10: Conclusion & Next Steps
    add_bullet_slide(
        "Summary & Next Steps",
        [
            "SentinelSOC provides a scalable, secure foundation for threat monitoring.",
            "Combines deterministic rules with advanced ML for robust detection.",
            "Empowers analysts with actionable intelligence and automated responses.",
            "Next Steps: Live Demonstration & Q&A."
        ],
        "In conclusion, SentinelSOC provides a modern, scalable foundation for threat detection. It empowers analysts to detect, investigate, and respond to threats effectively. I will now open the floor for questions and a live demonstration."
    )

    prs.save(filename)
    print(f"Presentation saved successfully to {filename}")

if __name__ == "__main__":
    create_presentation()
