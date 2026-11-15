export interface ApiKey {
  id: string
  name: string
  key_prefix: string
  last_used_at: string | null
  expires_at: string | null
  is_active: boolean
  created_at: string
  created_by: string
}

export interface ApiKeyCreateResponse extends ApiKey {
  api_key: string
}
