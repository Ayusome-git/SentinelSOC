import { api } from '../api'
import type { 
  Application, 
  ApplicationCreate, 
  ApplicationListResponse, 
  ApplicationStatusUpdate, 
  ApplicationUpdate,
  AppEnvironment,
  AppStatus
} from '../types/application'
import type { ApiKey, ApiKeyCreateResponse } from '../types/api_key'

export const applicationsApi = {
  list: async (
    params?: { 
      page?: number
      page_size?: number
      environment?: AppEnvironment
      status?: AppStatus
    }
  ): Promise<ApplicationListResponse> => {
    const searchParams = new URLSearchParams()
    if (params?.page) searchParams.append('page', params.page.toString())
    if (params?.page_size) searchParams.append('page_size', params.page_size.toString())
    if (params?.environment) searchParams.append('environment', params.environment)
    if (params?.status) searchParams.append('status', params.status)
    
    const query = searchParams.toString() ? `?${searchParams.toString()}` : ''
    return api.get<ApplicationListResponse>(`/api/v1/applications${query}`)
  },

  get: async (id: string): Promise<Application> => {
    return api.get<Application>(`/api/v1/applications/${id}`)
  },

  create: async (data: ApplicationCreate): Promise<Application> => {
    return api.post<Application>('/api/v1/applications', data)
  },

  update: async (id: string, data: ApplicationUpdate): Promise<Application> => {
    return api.patch<Application>(`/api/v1/applications/${id}`, data)
  },

  changeStatus: async (id: string, data: ApplicationStatusUpdate): Promise<Application> => {
    return api.patch<Application>(`/api/v1/applications/${id}/status`, data)
  },

  createApiKey: async (applicationId: string, data: { name: string; expires_at?: string | null }): Promise<ApiKeyCreateResponse> => {
    return api.post<ApiKeyCreateResponse>(`/api/v1/applications/${applicationId}/api-keys`, data)
  },

  listApiKeys: async (applicationId: string): Promise<ApiKey[]> => {
    return api.get<ApiKey[]>(`/api/v1/applications/${applicationId}/api-keys`)
  },

  revokeApiKey: async (applicationId: string, keyId: string, is_active: boolean): Promise<ApiKey> => {
    return api.patch<ApiKey>(`/api/v1/applications/${applicationId}/api-keys/${keyId}/status`, { is_active })
  }
}
