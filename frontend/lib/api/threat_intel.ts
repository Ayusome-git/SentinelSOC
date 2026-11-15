import { api } from '../api';
import { ThreatIntelListResponse, ThreatIntelIndicator, ThreatIntelLookupRequest, ThreatIntelLookupResponse } from "../types/threat_intel";

export const getIndicators = async (params?: Record<string, any>): Promise<ThreatIntelListResponse> => {
  const searchParams = new URLSearchParams()
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.append(key, String(value))
      }
    })
  }
  const query = searchParams.toString() ? `?${searchParams.toString()}` : ''
  return api.get(`/api/v1/threat-intelligence/indicators${query}`);
};

export const getIndicator = async (id: string): Promise<ThreatIntelIndicator> => {
  return api.get(`/api/v1/threat-intelligence/indicators/${id}`);
};

export const lookupIndicator = async (data: ThreatIntelLookupRequest): Promise<ThreatIntelLookupResponse> => {
  return api.post("/api/v1/threat-intelligence/lookup", data);
};
