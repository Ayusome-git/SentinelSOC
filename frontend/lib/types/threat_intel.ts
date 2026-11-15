export interface ThreatIntelIndicator {
  id: string;
  indicator: string;
  indicator_type: string;
  source: string;
  malicious: boolean;
  confidence: number;
  reputation?: string;
  categories?: string[];
  first_seen_at?: string;
  last_seen_at?: string;
  reference?: string;
  created_at: string;
  updated_at: string;
}

export interface ThreatIntelListResponse {
  items: ThreatIntelIndicator[];
  total: number;
  page: number;
  page_size: number;
}

export interface ThreatIntelLookupRequest {
  indicator: string;
  indicator_type: string;
}

export interface ThreatIntelLookupResponse {
  found: boolean;
  indicator: string;
  indicator_type: string;
  malicious: boolean;
  confidence: number;
  reputation?: string;
  categories?: string[];
  source: string;
  first_seen_at?: string;
  last_seen_at?: string;
  reference?: string;
}
