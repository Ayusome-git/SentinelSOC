export interface DashboardTimeRange {
  start: string
  end: string
}

export interface ApplicationActivity {
  application_id: string
  application_name: string
  event_count: number
}

export interface RecentEvent {
  id: string
  timestamp: string
  severity: string
  event_type: string
  application_name: string
  username?: string | null
  source_ip?: string | null
}

export interface EventTimelinePoint {
  timestamp: string
  count: number
}

export interface DashboardOverviewResponse {
  time_range: DashboardTimeRange
  total_events: number
  critical_events: number
  high_events: number
  active_applications: number
  events_per_hour: number
  severity_distribution: Record<string, number>
  event_type_distribution: Record<string, number>
  application_activity: ApplicationActivity[]
  application_status: Record<string, number>
  environment_distribution: Record<string, number>
  production_events: number
  event_timeline: EventTimelinePoint[]
  latest_event_timestamp?: string | null
  recent_events: RecentEvent[]
  risk_summary?: Record<string, number>
}
