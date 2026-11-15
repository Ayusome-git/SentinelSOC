export interface Incident {
  id: string;
  incident_number: string;
  title: string;
  description: string | null;
  severity: string;
  status: string;
  risk_score: number | null;
  application_id: string;
  correlation_id: string | null;
  assigned_to: string | null;
  detected_at: string;
  contained_at: string | null;
  resolved_at: string | null;
  closed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface IncidentListResponse {
  items: Incident[];
  total: number;
  page: number;
  size: number;
}

export interface IncidentSummary {
  total: number;
  open: number;
  investigating: number;
  contained: number;
  resolved: number;
  closed: number;
  critical: number;
  high: number;
  unassigned: number;
  average_risk_score: number;
}

export interface IncidentComment {
  id: string;
  incident_id: string;
  user_id: string;
  comment: string;
  created_at: string;
  updated_at: string;
}

export interface IncidentTimelineEvent {
  id: string;
  entry_type: string;
  occurred_at: string;
  title: string;
  description: string | null;
  severity: string | null;
  risk_score: number | null;
  security_event_id: string | null;
  alert_id: string | null;
  correlation_id: string | null;
  source_ip: string | null;
  username: string | null;
  metadata_fields: any | null;
}

export interface EntityCount {
  value: string;
  event_count: number;
}

export interface IncidentEntity {
  source_ips: EntityCount[];
  users: EntityCount[];
  request_paths: EntityCount[];
  sessions: EntityCount[];
}

export interface RelatedSecurityEvent {
  id: string;
  event_type: string;
  timestamp: string;
  source_ip?: string;
  username?: string;
  risk_score?: number;
}

export interface EntitiesResponse {
  source_ips: EntityCount[];
  users: EntityCount[];
  request_paths: EntityCount[];
  sessions: EntityCount[];
}
