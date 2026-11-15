import { api } from '../api';
import { DetectionRule, DetectionRuleCreate, DetectionRuleUpdate, DetectionRuleListResponse } from '../types/rule';

export const rulesApi = {
  list: async (params?: { page?: number; page_size?: number; search?: string; category?: string; severity?: string; enabled?: boolean; rule_type?: string }): Promise<DetectionRuleListResponse> => {
    const searchParams = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, String(value))
        }
      })
    }
    return api.get<DetectionRuleListResponse>(`/api/v1/rules?${searchParams.toString()}`)
  },
  
  get: async (id: string): Promise<DetectionRule> => {
    return api.get<DetectionRule>(`/api/v1/rules/${id}`)
  },
    
  create: async (data: DetectionRuleCreate): Promise<DetectionRule> => {
    return api.post<DetectionRule>('/api/v1/rules', data)
  },
    
  update: async (id: string, data: DetectionRuleUpdate): Promise<DetectionRule> => {
    return api.patch<DetectionRule>(`/api/v1/rules/${id}`, data)
  },
    
  updateStatus: async (id: string, enabled: boolean): Promise<DetectionRule> => {
    return api.patch<DetectionRule>(`/api/v1/rules/${id}/status`, { enabled })
  }
};
