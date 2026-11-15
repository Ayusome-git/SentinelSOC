export interface DetectionRule {
  id: string;
  name: string;
  description: string | null;
  rule_type: string;
  enabled: boolean;
  severity: string;
  event_type: string;
  threshold: number | null;
  window_seconds: number | null;
  group_by: string | null;
  category: string | null;
  mitre_technique: string | null;
  pattern: string | null;
  distinct_field: string | null;
  application_id: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface DetectionRuleCreate {
  name: string;
  description?: string;
  rule_type?: string;
  enabled?: boolean;
  severity: string;
  event_type: string;
  threshold?: number | null;
  window_seconds?: number | null;
  group_by?: string | null;
  category?: string | null;
  mitre_technique?: string | null;
  pattern?: string | null;
  distinct_field?: string | null;
  application_id?: string;
}

export interface DetectionRuleUpdate {
  name?: string;
  description?: string;
  enabled?: boolean;
  severity?: string;
  threshold?: number | null;
  window_seconds?: number | null;
  group_by?: string | null;
  category?: string | null;
  mitre_technique?: string | null;
  pattern?: string | null;
  distinct_field?: string | null;
}

export interface DetectionRuleListResponse {
  items: DetectionRule[];
  total: number;
  page: number;
  size: number;
}
