export type ResponseActionStatus = 
  | "PENDING_APPROVAL"
  | "APPROVED"
  | "EXECUTING"
  | "SUCCEEDED"
  | "FAILED"
  | "CANCELLED"
  | "REJECTED";

export interface ResponseAction {
  id: string;
  incident_id?: string;
  alert_id?: string;
  application_id: string;
  action_type: string;
  target_type: string;
  target_value: string;
  status: ResponseActionStatus;
  requested_by: string;
  approved_by?: string;
  requested_at: string;
  approved_at?: string;
  executed_at?: string;
  completed_at?: string;
  failure_reason?: string;
  result_summary?: string;
}

export interface ResponseActionCreate {
  incident_id?: string;
  alert_id?: string;
  application_id: string;
  action_type: string;
  target_type: string;
  target_value: string;
}

export interface ResponseActionListResponse {
  items: ResponseAction[];
  total: number;
  page: number;
  page_size: number;
}

export interface ApplicationResponseCapability {
  id: string;
  application_id: string;
  action_type: string;
  enabled: boolean;
  configuration?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ResponsePolicy {
  id: string;
  name: string;
  enabled: boolean;
  application_id: string;
  action_type: string;
  minimum_severity?: string;
  minimum_risk_score?: number;
  require_approval: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface ResponsePolicyListResponse {
  items: ResponsePolicy[];
  total: number;
  page: number;
  page_size: number;
}
