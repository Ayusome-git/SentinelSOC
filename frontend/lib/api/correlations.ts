import { api } from '../api'
import { Correlation, CorrelationListResponse } from '../types/correlation'

export const correlationsApi = {
  async getCorrelations(params?: {
    page?: number
    page_size?: number
    status?: string
    severity?: string
    risk_level?: string
    min_risk_score?: number
    max_risk_score?: number
    application_id?: string
  }): Promise<CorrelationListResponse> {
    const searchParams = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, String(value))
        }
      })
    }

    return api.get<CorrelationListResponse>(`/api/v1/correlations?${searchParams.toString()}`)
  },

  async getCorrelation(id: string): Promise<Correlation> {
    return api.get<Correlation>(`/api/v1/correlations/${id}`)
  },

  async updateStatus(id: string, status: string): Promise<Correlation> {
    return api.patch<Correlation>(`/api/v1/correlations/${id}/status`, { status })
  },

  async createIncident(id: string): Promise<{ message: string, incident_id: string, incident_number: string }> {
    return api.post<{ message: string, incident_id: string, incident_number: string }>(`/api/v1/correlations/${id}/create-incident`)
  }
}

