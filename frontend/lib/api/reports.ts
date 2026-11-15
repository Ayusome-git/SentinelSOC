import { api } from '../api';
import { 
  SecurityOverviewReport, AlertSummaryReport, IncidentSummaryReport, 
  AttackActivityReport, ApplicationSecurityReport, RiskAnalysisReport, 
  ResponseActionReport, EventActivityReport 
} from '../types/report';

export interface ReportParams {
  start_date: string;
  end_date: string;
  application_id?: string;
  severity?: string;
}

const buildQuery = (params: ReportParams) => {
  const query = new URLSearchParams({
    start_date: params.start_date,
    end_date: params.end_date,
  });
  
  if (params.application_id) {
    query.append('application_id', params.application_id);
  }
  if (params.severity) {
    query.append('severity', params.severity);
  }
  
  return query.toString();
};

export const getSecurityOverview = async (params: ReportParams): Promise<SecurityOverviewReport> => {
  return api.get(`/api/v1/reports/security-overview?${buildQuery(params)}`);
};

export const getAlertSummary = async (params: ReportParams): Promise<AlertSummaryReport> => {
  return api.get(`/api/v1/reports/alerts?${buildQuery(params)}`);
};

export const getIncidentSummary = async (params: ReportParams): Promise<IncidentSummaryReport> => {
  return api.get(`/api/v1/reports/incidents?${buildQuery(params)}`);
};

export const getAttackActivity = async (params: ReportParams): Promise<AttackActivityReport> => {
  return api.get(`/api/v1/reports/attacks?${buildQuery(params)}`);
};

export const getApplicationSecurity = async (params: ReportParams): Promise<ApplicationSecurityReport> => {
  return api.get(`/api/v1/reports/applications?${buildQuery(params)}`);
};

export const getRiskAnalysis = async (params: ReportParams): Promise<RiskAnalysisReport> => {
  return api.get(`/api/v1/reports/risk?${buildQuery(params)}`);
};

export const getResponseActions = async (params: ReportParams): Promise<ResponseActionReport> => {
  return api.get(`/api/v1/reports/response-actions?${buildQuery(params)}`);
};

export const getEventActivity = async (params: ReportParams): Promise<EventActivityReport> => {
  return api.get(`/api/v1/reports/events?${buildQuery(params)}`);
};

export const exportSecurityOverview = async (params: ReportParams, format: 'pdf' | 'csv' = 'pdf') => {
  const token = localStorage.getItem('sentinel_token');
  const headers: Record<string, string> = {
    'Accept': format === 'pdf' ? 'application/pdf' : 'text/csv'
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/reports/security-overview/export?format=${format}&${buildQuery(params)}`, {
    headers,
  });
  
  if (!res.ok) throw new Error('Export failed');
  return res.blob();
};
