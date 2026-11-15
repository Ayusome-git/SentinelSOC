export type TimelineEntryType = "SECURITY_EVENT" | "ALERT" | "CORRELATION" | "INCIDENT_ACTIVITY" | "COMMENT"

export interface TimelineEntry {
  id: string
  entry_type: TimelineEntryType
  occurred_at: string
  title: string
  description?: string
  severity?: string
  risk_score?: number
  security_event_id?: string
  alert_id?: string
  correlation_id?: string
  source_ip?: string
  username?: string
  metadata_fields?: Record<string, any>
}

export interface EntityCount {
  value: string
  event_count: number
}

export interface EntitiesResponse {
  source_ips: EntityCount[]
  users: EntityCount[]
  request_paths: EntityCount[]
  sessions: EntityCount[]
}

export interface IncidentEvidenceResponse {
  id: string
  incident_id: string
  evidence_type: string
  evidence_id: string
  added_by?: string
  created_at: string
}
