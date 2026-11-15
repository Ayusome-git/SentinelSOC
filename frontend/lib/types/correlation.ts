import { SecurityEvent } from "./event";

export interface CorrelationEvidence {
    id: string;
    type: "EVENT" | "ALERT";
    timestamp: string;
    data: any; // Event or Alert
    sequence_position: number;
}

export interface Correlation {
    id: string;
    name: string;
    description?: string;
    severity: string;
    status: string;
    risk_score?: number;
    risk_level?: string;
    risk_factors?: Record<string, number>;
    rule_id?: string;
    application_id: string;
    first_event_at: string;
    last_event_at: string;
    created_at: string;
    generated_alert_id?: string;
    evidence?: CorrelationEvidence[];
}

export interface CorrelationListResponse {
    items: Correlation[];
    total: number;
    page: number;
    page_size: number;
}
