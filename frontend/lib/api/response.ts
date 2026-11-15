import { api } from '../api';
import { 
  ResponseAction, 
  ResponseActionCreate, 
  ResponseActionListResponse,
  ApplicationResponseCapability,
  ResponsePolicy,
  ResponsePolicyListResponse
} from "../types/response";

function buildQueryString(params?: Record<string, any>) {
  if (!params) return '';
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.append(key, String(value));
    }
  });
  const query = searchParams.toString();
  return query ? `?${query}` : '';
}

// --- Actions ---

export const getResponseActions = async (params?: Record<string, any>): Promise<ResponseActionListResponse> => {
  return api.get(`/api/v1/response-actions${buildQueryString(params)}`);
};

export const createResponseAction = async (data: ResponseActionCreate): Promise<ResponseAction> => {
  return api.post("/api/v1/response-actions", data);
};

export const approveResponseAction = async (id: string): Promise<ResponseAction> => {
  return api.post(`/api/v1/response-actions/${id}/approve`);
};

export const rejectResponseAction = async (id: string, reason: string): Promise<ResponseAction> => {
  return api.post(`/api/v1/response-actions/${id}/reject`, { reason });
};

export const cancelResponseAction = async (id: string): Promise<ResponseAction> => {
  return api.post(`/api/v1/response-actions/${id}/cancel`);
};

export const executeResponseAction = async (id: string): Promise<ResponseAction> => {
  return api.post(`/api/v1/response-actions/${id}/execute`);
};

// --- Capabilities ---

export const getApplicationCapabilities = async (applicationId: string): Promise<ApplicationResponseCapability[]> => {
  return api.get(`/api/v1/response-capabilities${buildQueryString({ application_id: applicationId })}`);
};

export const updateApplicationCapability = async (id: string, data: Partial<ApplicationResponseCapability>): Promise<ApplicationResponseCapability> => {
  return api.patch(`/api/v1/response-capabilities/${id}`, data);
};

export const createApplicationCapability = async (data: any): Promise<ApplicationResponseCapability> => {
  return api.post("/api/v1/response-capabilities", data);
};

// --- Policies ---

export const getResponsePolicies = async (params?: Record<string, any>): Promise<ResponsePolicyListResponse> => {
  return api.get(`/api/v1/response-policies${buildQueryString(params)}`);
};

export const createResponsePolicy = async (data: any): Promise<ResponsePolicy> => {
  return api.post("/api/v1/response-policies", data);
};

export const updateResponsePolicy = async (id: string, data: any): Promise<ResponsePolicy> => {
  return api.patch(`/api/v1/response-policies/${id}`, data);
};
