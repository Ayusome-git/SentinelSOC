import { api } from '../api'
import { Incident, IncidentListResponse, IncidentComment, IncidentSummary, IncidentEntity, IncidentTimelineEvent, RelatedSecurityEvent } from '../types/incident'

export const incidentsApi = {
  async getIncidents(params?: {
    page?: number
    page_size?: number
    status?: string
    severity?: string
    application_id?: string
    assigned_to?: string
    unassigned?: boolean
    start_time?: string
    end_time?: string
    search?: string
    sort_by?: string
    sort_dir?: string
  }): Promise<IncidentListResponse> {
    const searchParams = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, String(value))
        }
      })
    }

    return api.get<IncidentListResponse>(`/api/v1/incidents?${searchParams.toString()}`)
  },

  async getIncident(id: string): Promise<Incident> {
    return api.get<Incident>(`/api/v1/incidents/${id}`)
  },

  async getSummary(): Promise<IncidentSummary> {
    return api.get<IncidentSummary>('/api/v1/incidents/summary')
  },

  async updateStatus(id: string, status: string, resolution_notes?: string): Promise<Incident> {
    return api.patch<Incident>(`/api/v1/incidents/${id}/status`, { status, resolution_notes })
  },

  async assign(id: string, assigned_to: string | null): Promise<Incident> {
    return api.patch<Incident>(`/api/v1/incidents/${id}/assignee`, { assigned_to })
  },

  async addComment(id: string, comment: string): Promise<IncidentComment> {
    return api.post<IncidentComment>(`/api/v1/incidents/${id}/comments`, { comment })
  },

  async getComments(id: string): Promise<IncidentComment[]> {
    return api.get<IncidentComment[]>(`/api/v1/incidents/${id}/comments`)
  },

  async getTimeline(id: string, params?: { 
    event_type?: string; 
    start_time?: string; 
    end_time?: string;
    types?: string;
    search?: string;
  }): Promise<{ items: IncidentTimelineEvent[], total: number }> {
    const searchParams = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) searchParams.append(key, String(value))
      })
    }
    return api.get<{ items: IncidentTimelineEvent[], total: number }>(`/api/v1/incidents/${id}/timeline?${searchParams.toString()}`)
  },

  async getEntities(id: string): Promise<IncidentEntity[]> {
    return api.get<IncidentEntity[]>(`/api/v1/incidents/${id}/entities`)
  },

  async getRelatedEvents(id: string, params?: {
    page?: number;
    page_size?: number;
  }): Promise<{ items: RelatedSecurityEvent[], total: number }> {
    const searchParams = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) searchParams.append(key, String(value))
      })
    }
    return api.get<{ items: RelatedSecurityEvent[], total: number }>(`/api/v1/incidents/${id}/related-events?${searchParams.toString()}`)
  },

  async addEvidence(id: string, data: {
    evidence_type: 'ALERT' | 'CORRELATION' | 'EVENT' | 'USER' | 'IP' | 'FILE';
    evidence_id: string;
    notes?: string;
  }): Promise<any> {
    return api.post<any>(`/api/v1/incidents/${id}/evidence`, data)
  },

  async removeEvidence(id: string, evidenceType: string, evidenceId: string): Promise<void> {
    return api.delete<void>(`/api/v1/incidents/${id}/evidence/${evidenceType}/${evidenceId}`)
  }
}
