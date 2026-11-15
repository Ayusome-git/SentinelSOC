export type AppEnvironment = 'DEVELOPMENT' | 'STAGING' | 'PRODUCTION'
export type AppStatus = 'ACTIVE' | 'INACTIVE' | 'SUSPENDED'

export interface Application {
  id: string
  name: string
  slug: string
  description: string | null
  environment: AppEnvironment
  status: AppStatus
  owner_id: string
  owner_name: string
  created_at: string
  updated_at: string
}

export interface ApplicationListResponse {
  items: Application[]
  page: number
  page_size: number
  total: number
}

export interface ApplicationCreate {
  name: string
  slug: string
  description?: string
  environment: AppEnvironment
  owner_id: string
}

export interface ApplicationUpdate {
  name?: string
  description?: string
  environment?: AppEnvironment
  owner_id?: string
}

export interface ApplicationStatusUpdate {
  status: AppStatus
}
