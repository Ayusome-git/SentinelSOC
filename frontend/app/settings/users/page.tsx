/* eslint-disable @typescript-eslint/no-explicit-any */
"use client"

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { PageHeader } from "@/components/layout/PageHeader"
import { usePermissions } from "@/lib/permissions"
import { api } from "@/lib/api"
import {
  Search,
  Plus,
  MoreHorizontal,
  ChevronLeft,
  ChevronRight,
  X,
  UserCog,
  Shield,
  Eye,
  Loader2,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react"

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface UserItem {
  id: string
  email: string
  full_name: string | null
  role: 'ADMIN' | 'ANALYST' | 'VIEWER'
  is_active: boolean
  last_login_at: string | null
  created_at: string
  updated_at: string
}

interface PaginatedUsers {
  items: UserItem[]
  total: number
  page: number
  page_size: number
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------
const ROLE_BADGE_STYLES: Record<string, string> = {
  ADMIN: 'bg-indigo-500/15 text-indigo-400 border border-indigo-500/30',
  ANALYST: 'bg-amber-500/15 text-amber-400 border border-amber-500/30',
  VIEWER: 'bg-zinc-500/15 text-zinc-400 border border-zinc-500/30',
}

const ROLE_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  ADMIN: Shield,
  ANALYST: UserCog,
  VIEWER: Eye,
}

const STATUS_BADGE_STYLES: Record<string, string> = {
  active: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30',
  inactive: 'bg-red-500/15 text-red-400 border border-red-500/30',
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  })
}

function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return 'Never'
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function RoleBadge({ role }: { role: string }) {
  const Icon = ROLE_ICONS[role] ?? Eye
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${ROLE_BADGE_STYLES[role] ?? ROLE_BADGE_STYLES.VIEWER}`}>
      <Icon className="h-3 w-3" />
      {role}
    </span>
  )
}

function StatusBadge({ active }: { active: boolean }) {
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${active ? STATUS_BADGE_STYLES.active : STATUS_BADGE_STYLES.inactive}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${active ? 'bg-emerald-400' : 'bg-red-400'}`} />
      {active ? 'Active' : 'Inactive'}
    </span>
  )
}

// ---------------------------------------------------------------------------
// Modal wrapper
// ---------------------------------------------------------------------------
function Modal({ open, onClose, title, children }: {
  open: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
}) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div className="w-full max-w-lg rounded-xl border border-zinc-800 bg-[#0c0c0c] shadow-2xl" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between border-b border-zinc-800 px-6 py-4">
          <h2 className="text-lg font-semibold text-white">{title}</h2>
          <button onClick={onClose} className="text-zinc-500 hover:text-zinc-300 transition-colors">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="px-6 py-5">{children}</div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Confirm Dialog
// ---------------------------------------------------------------------------
function ConfirmDialog({ open, onClose, onConfirm, title, message, confirmLabel, loading, destructive }: {
  open: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  message: string
  confirmLabel: string
  loading?: boolean
  destructive?: boolean
}) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div className="w-full max-w-md rounded-xl border border-zinc-800 bg-[#0c0c0c] shadow-2xl" onClick={e => e.stopPropagation()}>
        <div className="px-6 py-5">
          <div className="flex items-start gap-3">
            <div className={`mt-0.5 flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full ${destructive ? 'bg-red-500/10' : 'bg-amber-500/10'}`}>
              <AlertTriangle className={`h-5 w-5 ${destructive ? 'text-red-400' : 'text-amber-400'}`} />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white">{title}</h3>
              <p className="mt-1 text-sm text-zinc-400">{message}</p>
            </div>
          </div>
        </div>
        <div className="flex justify-end gap-3 border-t border-zinc-800 px-6 py-4">
          <button onClick={onClose} disabled={loading} className="rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm font-medium text-zinc-300 hover:bg-zinc-800 transition-colors disabled:opacity-50">
            Cancel
          </button>
          <button onClick={onConfirm} disabled={loading} className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50 ${destructive ? 'bg-red-600 text-white hover:bg-red-700' : 'bg-indigo-600 text-white hover:bg-indigo-700'}`}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Toast
// ---------------------------------------------------------------------------
function Toast({ message, type, onClose }: { message: string; type: 'success' | 'error'; onClose: () => void }) {
  useEffect(() => {
    const t = setTimeout(onClose, 4000)
    return () => clearTimeout(t)
  }, [onClose])

  return (
    <div className={`fixed bottom-6 right-6 z-[60] flex items-center gap-2 rounded-lg border px-4 py-3 shadow-xl backdrop-blur-sm transition-all ${
      type === 'success' ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400' : 'border-red-500/30 bg-red-500/10 text-red-400'
    }`}>
      {type === 'success' ? <CheckCircle2 className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
      <span className="text-sm font-medium">{message}</span>
      <button onClick={onClose} className="ml-2 text-zinc-500 hover:text-zinc-300">
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  )
}


// ===========================================================================
// Main Page Component
// ===========================================================================
export default function UserManagementPage() {
  const router = useRouter()
  const { isAdmin } = usePermissions()

  // State
  const [users, setUsers] = useState<UserItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Modals
  const [createOpen, setCreateOpen] = useState(false)
  const [editUser, setEditUser] = useState<UserItem | null>(null)
  const [roleUser, setRoleUser] = useState<UserItem | null>(null)
  const [statusConfirm, setStatusConfirm] = useState<UserItem | null>(null)
  const [actionsOpen, setActionsOpen] = useState<string | null>(null)

  // Toast
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null)

  // -----------------------------------------------------------------------
  // Data fetching
  // -----------------------------------------------------------------------
  const fetchUsers = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      let path = `/api/v1/users?page=${page}&page_size=${pageSize}`
      if (search) path += `&search=${encodeURIComponent(search)}`
      const data = await api.get<PaginatedUsers>(path)
      setUsers(data.items)
      setTotal(data.total)
    } catch (e: any) {
      setError(e.message || 'Failed to load users')
    } finally {
      setLoading(false)
    }
  }, [page, pageSize, search])

  useEffect(() => {
    if (!isAdmin) {
      router.push('/dashboard')
      return
    }
    fetchUsers()
  }, [isAdmin, fetchUsers, router])

  const totalPages = Math.ceil(total / pageSize)

  // -----------------------------------------------------------------------
  // Create User
  // -----------------------------------------------------------------------
  function CreateUserForm({ onClose }: { onClose: () => void }) {
    const [form, setForm] = useState({ full_name: '', email: '', password: '', role: 'ANALYST' as string })
    const [submitting, setSubmitting] = useState(false)
    const [formError, setFormError] = useState('')

    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault()
      setFormError('')
      if (!form.full_name.trim()) { setFormError('Full name is required'); return }
      if (!form.email.trim()) { setFormError('Email is required'); return }
      if (form.password.length < 8) { setFormError('Password must be at least 8 characters'); return }

      setSubmitting(true)
      try {
        await api.post('/api/v1/users', form)
        setToast({ message: 'User created successfully', type: 'success' })
        onClose()
        fetchUsers()
      } catch (e: any) {
        setFormError(e.message || 'Failed to create user')
      } finally {
        setSubmitting(false)
      }
    }

    return (
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-1">Full Name</label>
          <input
            type="text"
            value={form.full_name}
            onChange={e => setForm(f => ({ ...f, full_name: e.target.value }))}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            placeholder="Jane Smith"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-1">Email</label>
          <input
            type="email"
            value={form.email}
            onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            placeholder="jane@company.com"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-1">Password</label>
          <input
            type="password"
            value={form.password}
            onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            placeholder="••••••••"
          />
          <p className="mt-1 text-xs text-zinc-500">Minimum 8 characters</p>
        </div>
        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-1">Role</label>
          <select
            value={form.role}
            onChange={e => setForm(f => ({ ...f, role: e.target.value }))}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="ADMIN">Admin</option>
            <option value="ANALYST">Analyst</option>
            <option value="VIEWER">Viewer</option>
          </select>
        </div>

        {formError && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-400">
            {formError}
          </div>
        )}

        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={onClose} className="rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm font-medium text-zinc-300 hover:bg-zinc-800 transition-colors">
            Cancel
          </button>
          <button type="submit" disabled={submitting} className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 transition-colors disabled:opacity-50">
            {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Create User'}
          </button>
        </div>
      </form>
    )
  }

  // -----------------------------------------------------------------------
  // Edit User
  // -----------------------------------------------------------------------
  function EditUserForm({ user, onClose }: { user: UserItem; onClose: () => void }) {
    const [form, setForm] = useState({ full_name: user.full_name || '', email: user.email })
    const [submitting, setSubmitting] = useState(false)
    const [formError, setFormError] = useState('')

    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault()
      setFormError('')
      setSubmitting(true)
      try {
        await api.patch(`/api/v1/users/${user.id}`, form)
        setToast({ message: 'User updated successfully', type: 'success' })
        onClose()
        fetchUsers()
      } catch (e: any) {
        setFormError(e.message || 'Failed to update user')
      } finally {
        setSubmitting(false)
      }
    }

    return (
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-1">Full Name</label>
          <input
            type="text"
            value={form.full_name}
            onChange={e => setForm(f => ({ ...f, full_name: e.target.value }))}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-1">Email</label>
          <input
            type="email"
            value={form.email}
            onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>

        {formError && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-400">
            {formError}
          </div>
        )}

        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={onClose} className="rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm font-medium text-zinc-300 hover:bg-zinc-800 transition-colors">
            Cancel
          </button>
          <button type="submit" disabled={submitting} className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 transition-colors disabled:opacity-50">
            {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Save Changes'}
          </button>
        </div>
      </form>
    )
  }

  // -----------------------------------------------------------------------
  // Change Role
  // -----------------------------------------------------------------------
  function ChangeRoleForm({ user, onClose }: { user: UserItem; onClose: () => void }) {
    const [role, setRole] = useState(user.role)
    const [submitting, setSubmitting] = useState(false)
    const [formError, setFormError] = useState('')

    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault()
      if (role === user.role) { onClose(); return }
      setFormError('')
      setSubmitting(true)
      try {
        await api.patch(`/api/v1/users/${user.id}/role`, { role })
        setToast({ message: `Role changed to ${role}`, type: 'success' })
        onClose()
        fetchUsers()
      } catch (e: any) {
        setFormError(e.message || 'Failed to change role')
      } finally {
        setSubmitting(false)
      }
    }

    return (
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <p className="text-sm text-zinc-400 mb-3">
            Changing role for <span className="font-medium text-zinc-200">{user.full_name || user.email}</span>
          </p>
          <div className="space-y-2">
            {(['ADMIN', 'ANALYST', 'VIEWER'] as const).map(r => (
              <label key={r} className={`flex items-center gap-3 rounded-lg border px-4 py-3 cursor-pointer transition-colors ${role === r ? 'border-indigo-500/50 bg-indigo-500/5' : 'border-zinc-800 hover:border-zinc-700'}`}>
                <input type="radio" name="role" value={r} checked={role === r} onChange={() => setRole(r)} className="sr-only" />
                <RoleBadge role={r} />
                <span className="text-sm text-zinc-400">
                  {r === 'ADMIN' && 'Full administrative access'}
                  {r === 'ANALYST' && 'SOC investigation & operational access'}
                  {r === 'VIEWER' && 'Read-only SOC access'}
                </span>
              </label>
            ))}
          </div>
        </div>

        {formError && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-400">
            {formError}
          </div>
        )}

        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={onClose} className="rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm font-medium text-zinc-300 hover:bg-zinc-800 transition-colors">
            Cancel
          </button>
          <button type="submit" disabled={submitting} className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 transition-colors disabled:opacity-50">
            {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Update Role'}
          </button>
        </div>
      </form>
    )
  }

  // -----------------------------------------------------------------------
  // Status toggle handler
  // -----------------------------------------------------------------------
  const [statusLoading, setStatusLoading] = useState(false)

  const handleStatusChange = async () => {
    if (!statusConfirm) return
    setStatusLoading(true)
    try {
      await api.patch(`/api/v1/users/${statusConfirm.id}/status`, { is_active: !statusConfirm.is_active })
      setToast({ message: statusConfirm.is_active ? 'User deactivated' : 'User activated', type: 'success' })
      setStatusConfirm(null)
      fetchUsers()
    } catch (e: any) {
      setToast({ message: e.message || 'Failed to update status', type: 'error' })
      setStatusConfirm(null)
    } finally {
      setStatusLoading(false)
    }
  }

  // -----------------------------------------------------------------------
  // Render
  // -----------------------------------------------------------------------
  if (!isAdmin) return null

  return (
    <div className="space-y-6 max-w-7xl">
      <PageHeader
        title="User Management"
        description="Manage SOC user accounts, roles, and access."
      />

      {/* Toolbar */}
      <div className="flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
          <input
            type="text"
            placeholder="Search users..."
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1) }}
            className="w-full rounded-lg border border-zinc-800 bg-zinc-900 py-2 pl-10 pr-3 text-sm text-zinc-300 placeholder:text-zinc-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>
        <button
          onClick={() => setCreateOpen(true)}
          className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          Create User
        </button>
      </div>

      {/* Error state */}
      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4" />
          {error}
          <button onClick={fetchUsers} className="ml-auto text-red-300 hover:text-white underline text-xs">Retry</button>
        </div>
      )}

      {/* Table */}
      <div className="rounded-xl border border-zinc-800 bg-[#0a0a0a] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-zinc-800 text-left">
                <th className="px-5 py-3 text-xs font-medium uppercase tracking-wider text-zinc-500">User</th>
                <th className="px-5 py-3 text-xs font-medium uppercase tracking-wider text-zinc-500">Role</th>
                <th className="px-5 py-3 text-xs font-medium uppercase tracking-wider text-zinc-500">Status</th>
                <th className="px-5 py-3 text-xs font-medium uppercase tracking-wider text-zinc-500">Last Login</th>
                <th className="px-5 py-3 text-xs font-medium uppercase tracking-wider text-zinc-500">Created</th>
                <th className="px-5 py-3 text-xs font-medium uppercase tracking-wider text-zinc-500 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/50">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-5 py-12 text-center">
                    <Loader2 className="h-6 w-6 animate-spin text-zinc-500 mx-auto" />
                    <p className="mt-2 text-sm text-zinc-500">Loading users…</p>
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-5 py-12 text-center">
                    <p className="text-sm text-zinc-500">{search ? 'No users match your search.' : 'No users found.'}</p>
                  </td>
                </tr>
              ) : (
                users.map(u => (
                  <tr key={u.id} className="group hover:bg-zinc-900/50 transition-colors">
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-3">
                        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-zinc-800 border border-zinc-700 text-xs font-semibold text-zinc-300">
                          {(u.full_name || u.email).charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <p className="text-sm font-medium text-zinc-200">{u.full_name || '—'}</p>
                          <p className="text-xs text-zinc-500">{u.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-3">
                      <RoleBadge role={u.role} />
                    </td>
                    <td className="px-5 py-3">
                      <StatusBadge active={u.is_active} />
                    </td>
                    <td className="px-5 py-3 text-sm text-zinc-400">
                      {formatDateTime(u.last_login_at)}
                    </td>
                    <td className="px-5 py-3 text-sm text-zinc-400">
                      {formatDate(u.created_at)}
                    </td>
                    <td className="px-5 py-3 text-right">
                      <div className="relative inline-block">
                        <button
                          onClick={() => setActionsOpen(actionsOpen === u.id ? null : u.id)}
                          className="rounded-lg p-1.5 text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300 transition-colors"
                        >
                          <MoreHorizontal className="h-4 w-4" />
                        </button>
                        {actionsOpen === u.id && (
                          <>
                            <div className="fixed inset-0 z-30" onClick={() => setActionsOpen(null)} />
                            <div className="absolute right-0 z-40 mt-1 w-44 rounded-lg border border-zinc-800 bg-[#111] shadow-xl py-1">
                              <button
                                onClick={() => { setActionsOpen(null); setEditUser(u) }}
                                className="flex w-full items-center gap-2 px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-800 transition-colors"
                              >
                                Edit Profile
                              </button>
                              <button
                                onClick={() => { setActionsOpen(null); setRoleUser(u) }}
                                className="flex w-full items-center gap-2 px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-800 transition-colors"
                              >
                                Change Role
                              </button>
                              <div className="my-1 border-t border-zinc-800" />
                              <button
                                onClick={() => { setActionsOpen(null); setStatusConfirm(u) }}
                                className={`flex w-full items-center gap-2 px-3 py-2 text-sm transition-colors ${u.is_active ? 'text-red-400 hover:bg-red-500/10' : 'text-emerald-400 hover:bg-emerald-500/10'}`}
                              >
                                {u.is_active ? 'Deactivate' : 'Activate'}
                              </button>
                            </div>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between border-t border-zinc-800 px-5 py-3">
            <p className="text-sm text-zinc-500">
              Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)} of {total} users
            </p>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="rounded-lg p-1.5 text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <span className="px-3 text-sm text-zinc-400">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="rounded-lg p-1.5 text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Create User Modal */}
      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="Create New User">
        <CreateUserForm onClose={() => setCreateOpen(false)} />
      </Modal>

      {/* Edit User Modal */}
      <Modal open={!!editUser} onClose={() => setEditUser(null)} title="Edit User">
        {editUser && <EditUserForm user={editUser} onClose={() => setEditUser(null)} />}
      </Modal>

      {/* Change Role Modal */}
      <Modal open={!!roleUser} onClose={() => setRoleUser(null)} title="Change User Role">
        {roleUser && <ChangeRoleForm user={roleUser} onClose={() => setRoleUser(null)} />}
      </Modal>

      {/* Status Confirm Dialog */}
      <ConfirmDialog
        open={!!statusConfirm}
        onClose={() => setStatusConfirm(null)}
        onConfirm={handleStatusChange}
        loading={statusLoading}
        destructive={statusConfirm?.is_active ?? false}
        title={statusConfirm?.is_active ? 'Deactivate User' : 'Activate User'}
        message={
          statusConfirm?.is_active
            ? `Deactivate ${statusConfirm?.full_name || statusConfirm?.email}? They will immediately lose access to SentinelSOC.`
            : `Activate ${statusConfirm?.full_name || statusConfirm?.email}? They will regain access to SentinelSOC.`
        }
        confirmLabel={statusConfirm?.is_active ? 'Deactivate' : 'Activate'}
      />

      {/* Toast notifications */}
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  )
}
