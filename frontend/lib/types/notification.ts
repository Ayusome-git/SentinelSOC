export type NotificationType =
  | 'CRITICAL_ALERT'
  | 'HIGH_RISK_ALERT'
  | 'INCIDENT_ASSIGNED'
  | 'INCIDENT_CREATED'
  | 'INCIDENT_ESCALATED'
  | 'RESPONSE_ACTION_FAILED'
  | 'ML_ANOMALY_DETECTED'
  | 'THREAT_INTELLIGENCE_MATCH';

export type NotificationStatus = 'PENDING' | 'SENT' | 'FAILED';

export interface Notification {
  id: string;
  user_id: string;
  notification_type: NotificationType;
  title: string;
  message: string;
  severity: string | null;
  risk_score: number | null;
  link_path: string | null;
  is_read: boolean;
  status: NotificationStatus;
  created_at: string;
  read_at: string | null;
  sent_at: string | null;
  failure_reason: string | null;
  alert_id: string | null;
  incident_id: string | null;
  response_action_id: string | null;
  application_id: string | null;
}

export interface NotificationListResponse {
  items: Notification[];
  total: number;
  unread_count: number;
  page: number;
  size: number;
}

export interface NotificationPreference {
  id: string;
  user_id: string;
  notify_on_critical_alerts: boolean;
  notify_on_high_risk: boolean;
  notify_on_incident_assigned: boolean;
  notify_on_incident_created: boolean;
  notify_on_incident_escalated: boolean;
  notify_on_response_failure: boolean;
  notify_on_ml_anomaly: boolean;
  notify_on_ti_match: boolean;
  receive_emails: boolean;
  updated_at: string;
}

export interface NotificationPreferenceUpdate {
  notify_on_critical_alerts?: boolean;
  notify_on_high_risk?: boolean;
  notify_on_incident_assigned?: boolean;
  notify_on_incident_created?: boolean;
  notify_on_incident_escalated?: boolean;
  notify_on_response_failure?: boolean;
  notify_on_ml_anomaly?: boolean;
  notify_on_ti_match?: boolean;
  receive_emails?: boolean;
}
