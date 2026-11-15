import { api } from '../api'
import { Alert, AlertListResponse, AlertComment, AlertSummary } from '../types/alert'

export const alertsApi = {
  async getAlerts(params?: {
    page?: number
    page_size?: number
    status?: string
    severity?: string
    risk_level?: string
    min_risk_score?: number
    max_risk_score?: number
    application_id?: string
    rule_id?: string
    assigned_to?: string
    unassigned?: boolean
    start_time?: string
    end_time?: string
    search?: string
    sort_by?: string
    sort_dir?: string
  }): Promise<AlertListResponse> {
    const searchParams = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, String(value))
        }
      })
    }

    return api.get<AlertListResponse>(`/api/v1/alerts?${searchParams.toString()}`)
  },

  async getAlert(id: string): Promise<Alert> {
    return api.get<Alert>(`/api/v1/alerts/${id}`)
  },

  async getSummary(): Promise<AlertSummary> {
    return api.get<AlertSummary>(`/api/v1/alerts/summary`)
  },

  async acknowledge(id: string): Promise<Alert> {
    return api.post<Alert>(`/api/v1/alerts/${id}/acknowledge`)
  },

  async resolve(id: string): Promise<Alert> {
    return api.post<Alert>(`/api/v1/alerts/${id}/resolve`)
  },

  async markFalsePositive(id: string): Promise<Alert> {
    return api.post<Alert>(`/api/v1/alerts/${id}/false-positive`)
  },

  async assign(id: string, assigned_to: string | null): Promise<Alert> {
    return api.patch<Alert>(`/api/v1/alerts/${id}/assignee`, { assigned_to })
  },

  async getComments(id: string): Promise<AlertComment[]> {
    return api.get<AlertComment[]>(`/api/v1/alerts/${id}/comments`)
  },

  async addComment(id: string, comment: string): Promise<AlertComment> {
    return api.post<AlertComment>(`/api/v1/alerts/${id}/comments`, { comment })
  },

  async bulkAction(alert_ids: string[], action: 'ACKNOWLEDGE' | 'ASSIGN' | 'RESOLVE' | 'FALSE_POSITIVE', assigned_to?: string | null): Promise<void> {
    return api.post<void>(`/api/v1/alerts/bulk-action`, { alert_ids, action, assigned_to })
  },

  async createIncident(id: string): Promise<{ message: string, incident_id: string, incident_number: string }> {
    return api.post<{ message: string, incident_id: string, incident_number: string }>(`/api/v1/alerts/${id}/create-incident`)
  }
}

