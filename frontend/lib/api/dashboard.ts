import { api } from '../api'
import { DashboardOverviewResponse } from '../types/dashboard'

export const dashboardApi = {
  getOverview: async (params?: { start_date?: string; end_date?: string }): Promise<DashboardOverviewResponse> => {
    const searchParams = new URLSearchParams()
    if (params?.start_date) searchParams.append('start_date', params.start_date)
    if (params?.end_date) searchParams.append('end_date', params.end_date)

    return api.get<DashboardOverviewResponse>(`/api/v1/dashboard/overview?${searchParams.toString()}`)
  }
}
