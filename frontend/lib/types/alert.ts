import { ThreatIntelIndicator } from './threat_intel';

export interface Alert {
    id: string;
    application_id: string;
    security_event_id?: string;
    title: string;
    description?: string;
    severity: string;
    status: string;
    risk_score?: number;
    risk_level?: string;
    risk_factors?: Record<string, number>;
    rule_id?: string;
    correlation_id?: string;
    detection_source?: string;
    detected_at: string;
    acknowledged_at?: string;
    resolved_at?: string;
    assigned_to?: string;
    created_at: string;
    updated_at: string;
    threat_intel_indicators?: ThreatIntelIndicator[];
}

export interface AlertListResponse {
    items: Alert[];
    total: number;
    page: number;
    page_size: number;
}

export interface AlertComment {
    id: string;
    alert_id: string;
    user_id: string;
    comment: string;
    created_at: string;
    updated_at: string;
}

export interface AlertSummary {
    total: number;
    open: number;
    acknowledged: number;
    resolved: number;
    false_positive: number;
    critical: number;
    high: number;
    unassigned: number;
    average_risk_score: number;
}
