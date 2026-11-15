/**
 * SentinelSOC Permission System (Frontend)
 *
 * Client-side mirror of the backend ROLE_PERMISSIONS matrix.
 * Used for UX purposes ONLY — the backend is always authoritative.
 */

import { useAuth } from './auth'

export type Permission =
  | 'USERS_READ'
  | 'USERS_MANAGE'
  | 'APPLICATIONS_READ'
  | 'APPLICATIONS_MANAGE'
  | 'EVENTS_READ'
  | 'ALERTS_READ'
  | 'ALERTS_MANAGE'
  | 'INCIDENTS_READ'
  | 'INCIDENTS_MANAGE'
  | 'SETTINGS_READ'
  | 'SETTINGS_MANAGE'
  | 'RULES_READ'
  | 'RULES_MANAGE'

export type UserRole = 'ADMIN' | 'ANALYST' | 'VIEWER'

const ROLE_PERMISSIONS: Record<UserRole, Set<Permission>> = {
  ADMIN: new Set<Permission>([
    'USERS_READ',
    'USERS_MANAGE',
    'APPLICATIONS_READ',
    'APPLICATIONS_MANAGE',
    'EVENTS_READ',
    'ALERTS_READ',
    'ALERTS_MANAGE',
    'INCIDENTS_READ',
    'INCIDENTS_MANAGE',
    'SETTINGS_READ',
    'SETTINGS_MANAGE',
    'RULES_READ',
    'RULES_MANAGE',
  ]),
  ANALYST: new Set<Permission>([
    'APPLICATIONS_READ',
    'EVENTS_READ',
    'ALERTS_READ',
    'ALERTS_MANAGE',
    'INCIDENTS_READ',
    'INCIDENTS_MANAGE',
    'SETTINGS_READ',
    'RULES_READ',
    'RULES_MANAGE',
  ]),
  VIEWER: new Set<Permission>([
    'APPLICATIONS_READ',
    'EVENTS_READ',
    'ALERTS_READ',
    'INCIDENTS_READ',
    'SETTINGS_READ',
    'RULES_READ',
  ]),
}

export function usePermissions() {
  const { user } = useAuth()
  const role = (user?.role as UserRole) ?? null

  const hasPermission = (permission: Permission): boolean => {
    if (!role) return false
    return ROLE_PERMISSIONS[role]?.has(permission) ?? false
  }

  const hasRole = (r: UserRole): boolean => role === r

  return {
    role,
    hasPermission,
    hasRole,
    isAdmin: role === 'ADMIN',
    isAnalyst: role === 'ANALYST',
    isViewer: role === 'VIEWER',
    permissions: role ? ROLE_PERMISSIONS[role] : new Set<Permission>(),
    isLoading: useAuth().loading,
  }
}
