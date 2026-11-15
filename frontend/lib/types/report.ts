export interface ReportFilters {
  start_date: string;
  end_date: string;
  application_id?: string;
  severity?: string;
}

export interface TrendPoint {
  timestamp: string;
  count: number;
}

export interface BaseReportResponse {
  from_date: string;
  to_date: string;
  generated_at: string;
  filters: Record<string, any>;
}

// Security Overview
export interface SecurityOverviewSummary {
  total_events: number;
  critical_events: number;
  high_events: number;
  medium_events: number;
  low_events: number;
  total_alerts: number;
  open_alerts: number;
  critical_alerts: number;
  high_risk_alerts: number;
  total_incidents: number;
  open_incidents: number;
  critical_incidents: number;
  resolved_incidents: number;
  average_alert_risk: number | null;
  max_alert_risk: number | null;
  total_response_actions: number;
  successful_response_actions: number;
  failed_response_actions: number;
}

export interface SecurityOverviewTrend {
  events: TrendPoint[];
  alerts: TrendPoint[];
  incidents: TrendPoint[];
}

export interface SecurityOverviewReport extends BaseReportResponse {
  summary: SecurityOverviewSummary;
  trends: SecurityOverviewTrend;
  comparison?: any;
}

// Alert Summary
export interface AlertSummaryMetrics {
  total: number;
  open: number;
  acknowledged: number;
  resolved: number;
  false_positives: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  avg_risk: number | null;
  max_risk: number | null;
  unassigned: number;
  assigned: number;
}

export interface AlertSummaryReport extends BaseReportResponse {
  summary: AlertSummaryMetrics;
  breakdowns: {
    by_severity: Record<string, number>;
    by_rule: Record<string, number>;
    by_application: Record<string, number>;
    by_status: Record<string, number>;
  };
}

// Incident Summary
export interface IncidentSummaryReport extends BaseReportResponse {
  summary: {
    total: number;
    open: number;
    investigating: number;
    contained: number;
    resolved: number;
    closed: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
    avg_risk: number | null;
    max_risk: number | null;
  };
  breakdowns: {
    by_severity: Record<string, number>;
    by_status: Record<string, number>;
    by_application: Record<string, number>;
  };
  trends: TrendPoint[];
}

// Attack Activity
export interface AttackCategory {
  category: string;
  detection_count: number;
  alert_count: number;
  critical_count: number;
  high_risk_count: number;
  incident_count: number;
  avg_risk: number | null;
}

export interface AttackActivityReport extends BaseReportResponse {
  categories: AttackCategory[];
  top_rules: { rule_name: string; alert_count: number }[];
}

// Application Security
export interface ApplicationSecurityMetrics {
  application_id: string;
  name: string;
  environment: string;
  status: string;
  events: number;
  alerts: number;
  critical_alerts: number;
  incidents: number;
  critical_incidents: number;
  avg_risk: number | null;
  max_risk: number | null;
  last_event_at: string | null;
  last_alert_at: string | null;
  last_incident_at: string | null;
}

export interface ApplicationSecurityReport extends BaseReportResponse {
  applications: ApplicationSecurityMetrics[];
}

// Risk Analysis
export interface RiskAnalysisReport extends BaseReportResponse {
  metrics: {
    avg_alert_risk: number | null;
    avg_incident_risk: number | null;
    max_alert_risk: number | null;
    max_incident_risk: number | null;
  };
  distribution: {
    low: number;
    moderate: number;
    high: number;
    critical: number;
  };
  risk_by_application: Record<string, number>;
  risk_by_rule: Record<string, number>;
  top_high_risk_alerts: any[];
  top_high_risk_incidents: any[];
  trends: TrendPoint[];
}

// Response Actions
export interface ResponseActionReport extends BaseReportResponse {
  summary: {
    total: number;
    pending: number;
    approved: number;
    executing: number;
    succeeded: number;
    failed: number;
    cancelled: number;
    rejected: number;
    success_rate: number | null;
    failure_rate: number | null;
  };
  breakdowns: {
    by_type: Record<string, number>;
    by_application: Record<string, number>;
    by_status: Record<string, number>;
  };
}

// Event Activity
export interface EventActivityReport extends BaseReportResponse {
  summary: {
    total: number;
    login_failures: number;
    login_successes: number;
    permission_denied: number;
    api_errors: number;
    suspicious_requests: number;
    admin_actions: number;
  };
  breakdowns: {
    by_severity: Record<string, number>;
    by_type: Record<string, number>;
    by_application: Record<string, number>;
  };
  trends: TrendPoint[];
}
