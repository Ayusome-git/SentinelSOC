import { api } from '../api'
import type { EventListResponse, EventAnalyticsResponse } from '../types/event'

export interface EventQueryParams {
  page?: number
  page_size?: number
  application_id?: string
  event_type?: string
  severity?: string
  source_ip?: string
  username?: string
  request_path?: string
  request_id?: string
  session_id?: string
  search?: string
  start_date?: string
  end_date?: string
  sort_dir?: 'newest' | 'oldest'
}

export const eventsApi = {
  list: async (params?: EventQueryParams): Promise<EventListResponse> => {
    const searchParams = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          searchParams.append(key, String(value))
        }
      })
    }
    const query = searchParams.toString() ? `?${searchParams.toString()}` : ''
    return api.get<EventListResponse>(`/api/v1/events${query}`)
  },

  getAnalytics: async (params?: Omit<EventQueryParams, 'page' | 'page_size' | 'sort_dir'>): Promise<EventAnalyticsResponse> => {
    const searchParams = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          searchParams.append(key, String(value))
        }
      })
    }
    const query = searchParams.toString() ? `?${searchParams.toString()}` : ''
    return api.get<EventAnalyticsResponse>(`/api/v1/events/analytics${query}`)
  }
}
