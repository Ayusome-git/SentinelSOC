export type EventSeverity = 'INFO' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export type EventType = 
  | 'LOGIN_SUCCESS' 
  | 'LOGIN_FAILED' 
  | 'LOGOUT' 
  | 'PASSWORD_CHANGED' 
  | 'ACCOUNT_CREATED' 
  | 'ACCOUNT_LOCKED' 
  | 'ADMIN_LOGIN' 
  | 'ADMIN_ACTION' 
  | 'API_REQUEST' 
  | 'API_ERROR' 
  | 'FILE_UPLOAD' 
  | 'FILE_DOWNLOAD' 
  | 'PERMISSION_DENIED' 
  | 'SUSPICIOUS_REQUEST'

export interface SecurityEvent {
  id: string
  application_id: string
  application_name: string
  event_type: EventType | string
  severity: EventSeverity | string
  timestamp: string
  
  source_ip?: string | null
  user_id?: string | null
  username?: string | null
  session_id?: string | null
  request_id?: string | null
  
  http_method?: string | null
  request_path?: string | null
  user_agent?: string | null
  
  message?: string | null
  metadata?: Record<string, any> | null
  
  created_at: string
}

export interface EventListResponse {
  total: number
  items: SecurityEvent[]
  page: number
  page_size: number
}

export interface EventTimelinePoint {
  timestamp: string
  count: number
}

export interface EventAnalyticsResponse {
  total: number
  severity_counts: Record<string, number>
  event_type_counts: Record<string, number>
  application_counts: Record<string, number>
  source_ip_counts: Record<string, number>
  timeline: EventTimelinePoint[]
}
