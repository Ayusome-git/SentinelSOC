/* eslint-disable @typescript-eslint/no-explicit-any */
"use client"

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { PageHeader } from "@/components/layout/PageHeader"
import { usePermissions } from "@/lib/permissions"
import { applicationsApi } from "@/lib/api/applications"
import { api } from "@/lib/api"
import type { Application, AppEnvironment, AppStatus } from "@/lib/types/application"
import {
  Search,
  Plus,
  MoreHorizontal,
  ChevronLeft,
  ChevronRight,
  X,
  Loader2,
  AlertTriangle,
  CheckCircle2,
  Activity,
  Box,
  PauseCircle,
  Database
} from "lucide-react"

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------
const ENV_BADGE_STYLES: Record<string, string> = {
  DEVELOPMENT: 'bg-zinc-500/15 text-zinc-400 border border-zinc-500/30',
  STAGING: 'bg-amber-500/15 text-amber-400 border border-amber-500/30',
  PRODUCTION: 'bg-indigo-500/15 text-indigo-400 border border-indigo-500/30',
}

const STATUS_BADGE_STYLES: Record<string, string> = {
  ACTIVE: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30',
  INACTIVE: 'bg-zinc-500/15 text-zinc-400 border border-zinc-500/30',
  SUSPENDED: 'bg-red-500/15 text-red-400 border border-red-500/30',
}

const STATUS_ICONS: Record<string, any> = {
  ACTIVE: Activity,
  INACTIVE: Box,
  SUSPENDED: PauseCircle,
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

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------
function EnvBadge({ env }: { env: AppEnvironment }) {
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${ENV_BADGE_STYLES[env] || ENV_BADGE_STYLES.DEVELOPMENT}`}>
      {env}
    </span>
  )
}

function StatusBadge({ status }: { status: AppStatus }) {
  const Icon = STATUS_ICONS[status] || Activity
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${STATUS_BADGE_STYLES[status] || STATUS_BADGE_STYLES.INACTIVE}`}>
      <Icon className="h-3 w-3" />
      {status}
    </span>
  )
}

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

// ---------------------------------------------------------------------------
// Main Page Component
// ---------------------------------------------------------------------------
export default function ApplicationsPage() {
  const { isAdmin } = usePermissions()

  // State
  const [applications, setApplications] = useState<Application[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Modals
  const [createOpen, setCreateOpen] = useState(false)
  const [editApp, setEditApp] = useState<Application | null>(null)
  const [statusConfirm, setStatusConfirm] = useState<{ app: Application, newStatus: AppStatus } | null>(null)
  const [actionsOpen, setActionsOpen] = useState<string | null>(null)

  // System Users
  const [users, setUsers] = useState<any[]>([])

  // Toast
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null)

  // -----------------------------------------------------------------------
  // Data fetching
  // -----------------------------------------------------------------------
  const fetchApplications = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const data = await applicationsApi.list({ page, page_size: pageSize })
      setApplications(data.items)
      setTotal(data.total)
    } catch (e: any) {
      setError(e.message || 'Failed to load applications')
    } finally {
      setLoading(false)
    }
  }, [page, pageSize])

  const fetchUsers = useCallback(async () => {
    if (!isAdmin) return
    try {
      const data = await api.get<any>('/api/v1/users?page=1&page_size=100')
      setUsers(data.items)
    } catch (e) {
      console.error('Failed to fetch users', e)
    }
  }, [isAdmin])

  useEffect(() => {
    fetchApplications()
    fetchUsers()
  }, [fetchApplications, fetchUsers])

  const totalPages = Math.ceil(total / pageSize)

  // -----------------------------------------------------------------------
  // Create Application Form
  // -----------------------------------------------------------------------
  function CreateAppForm({ onClose }: { onClose: () => void }) {
    const [form, setForm] = useState({
      name: '',
      slug: '',
      description: '',
      environment: 'DEVELOPMENT' as AppEnvironment,
      owner_id: ''
    })
    const [submitting, setSubmitting] = useState(false)
    const [formError, setFormError] = useState('')

    // Auto-generate slug
    useEffect(() => {
      if (form.name && !form.slug) {
        setForm(f => ({ ...f, slug: f.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)+/g, '') }))
      }
    }, [form.name])

    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault()
      setFormError('')
      if (!form.name.trim()) { setFormError('Name is required'); return }
      if (!form.slug.trim()) { setFormError('Slug is required'); return }
      if (!form.owner_id) { setFormError('Owner is required'); return }

      setSubmitting(true)
      try {
        await applicationsApi.create(form)
        setToast({ message: 'Application registered successfully', type: 'success' })
        onClose()
        fetchApplications()
      } catch (e: any) {
        setFormError(e.message || 'Failed to register application')
      } finally {
        setSubmitting(false)
      }
    }

    return (
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-1">Application Name</label>
          <input
            type="text"
            value={form.name}
            onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            placeholder="My E-Commerce App"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-1">App Slug</label>
          <input
            type="text"
            value={form.slug}
            onChange={e => setForm(f => ({ ...f, slug: e.target.value }))}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            placeholder="my-ecommerce-app"
          />
          <p className="mt-1 text-xs text-zinc-500">URL-safe unique identifier</p>
        </div>
        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-1">Description</label>
          <textarea
            value={form.description}
            onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            placeholder="Main e-commerce storefront"
            rows={2}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-1">Environment</label>
          <select
            value={form.environment}
            onChange={e => setForm(f => ({ ...f, environment: e.target.value as AppEnvironment }))}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="DEVELOPMENT">Development</option>
            <option value="STAGING">Staging</option>
            <option value="PRODUCTION">Production</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-1">Owner</label>
          <select
            value={form.owner_id}
            onChange={e => setForm(f => ({ ...f, owner_id: e.target.value }))}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">Select an owner</option>
            {users.map(u => (
              <option key={u.id} value={u.id}>{u.full_name || u.email}</option>
            ))}
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
            {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Register App'}
          </button>
        </div>
      </form>
    )
  }

  // -----------------------------------------------------------------------
  // Edit Application Form
  // -----------------------------------------------------------------------
  function EditAppForm({ app, onClose }: { app: Application; onClose: () => void }) {
    const [form, setForm] = useState({
      name: app.name,
      description: app.description || '',
      environment: app.environment,
      owner_id: app.owner_id
    })
    const [submitting, setSubmitting] = useState(false)
    const [formError, setFormError] = useState('')

    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault()
      setFormError('')
      if (!form.name.trim()) { setFormError('Name is required'); return }
      if (!form.owner_id) { setFormError('Owner is required'); return }

      setSubmitting(true)
      try {
        await applicationsApi.update(app.id, form)
        setToast({ message: 'Application updated successfully', type: 'success' })
        onClose()
        fetchApplications()
      } catch (e: any) {
        setFormError(e.message || 'Failed to update application')
      } finally {
        setSubmitting(false)
      }
    }

    return (
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-1">Application Name</label>
          <input
            type="text"
            value={form.name}
            onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-1">Description</label>
          <textarea
            value={form.description}
            onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            rows={2}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-1">Environment</label>
          <select
            value={form.environment}
            onChange={e => setForm(f => ({ ...f, environment: e.target.value as AppEnvironment }))}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="DEVELOPMENT">Development</option>
            <option value="STAGING">Staging</option>
            <option value="PRODUCTION">Production</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-1">Owner</label>
          <select
            value={form.owner_id}
            onChange={e => setForm(f => ({ ...f, owner_id: e.target.value }))}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">Select an owner</option>
            {users.map(u => (
              <option key={u.id} value={u.id}>{u.full_name || u.email}</option>
            ))}
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
            {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Save Changes'}
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
      await applicationsApi.changeStatus(statusConfirm.app.id, { status: statusConfirm.newStatus })
      setToast({ message: `Application status changed to ${statusConfirm.newStatus}`, type: 'success' })
      setStatusConfirm(null)
      fetchApplications()
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
  return (
    <div className="space-y-6 max-w-7xl">
      <PageHeader
        title="Applications"
        description="Register applications to integrate with SentinelSOC for event ingestion and monitoring."
      />

      {/* Toolbar */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex-1" />
        {isAdmin && (
          <button
            onClick={() => setCreateOpen(true)}
            className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 transition-colors"
          >
            <Plus className="h-4 w-4" />
            Register Application
          </button>
        )}
      </div>

      {/* Error state */}
      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4" />
          {error}
          <button onClick={fetchApplications} className="ml-auto text-red-300 hover:text-white underline text-xs">Retry</button>
        </div>
      )}

      {/* Table */}
      <div className="rounded-xl border border-zinc-800 bg-[#0a0a0a] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-zinc-800 text-left">
                <th className="px-5 py-3 text-xs font-medium uppercase tracking-wider text-zinc-500">Application</th>
                <th className="px-5 py-3 text-xs font-medium uppercase tracking-wider text-zinc-500">Environment</th>
                <th className="px-5 py-3 text-xs font-medium uppercase tracking-wider text-zinc-500">Status</th>
                <th className="px-5 py-3 text-xs font-medium uppercase tracking-wider text-zinc-500">Owner</th>
                <th className="px-5 py-3 text-xs font-medium uppercase tracking-wider text-zinc-500">Registered</th>
                <th className="px-5 py-3 text-xs font-medium uppercase tracking-wider text-zinc-500 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/50">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-5 py-12 text-center">
                    <Loader2 className="h-6 w-6 animate-spin text-zinc-500 mx-auto" />
                    <p className="mt-2 text-sm text-zinc-500">Loading applications…</p>
                  </td>
                </tr>
              ) : applications.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-5 py-12 text-center">
                    <Database className="h-10 w-10 text-zinc-600 mx-auto mb-3" />
                    <h3 className="text-lg font-medium text-zinc-300">No applications registered</h3>
                    <p className="mt-1 text-sm text-zinc-500">
                      Register an application to begin integrating events.
                    </p>
                  </td>
                </tr>
              ) : (
                applications.map(app => (
                  <tr key={app.id} className="group hover:bg-zinc-900/50 transition-colors">
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-zinc-800 border border-zinc-700 text-indigo-400">
                          <Database className="h-5 w-5" />
                        </div>
                        <div>
                          <Link href={`/applications/${app.id}`} className="text-sm font-medium text-indigo-400 hover:text-indigo-300 transition-colors">
                            {app.name}
                          </Link>
                          <p className="text-xs text-zinc-500">{app.slug}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-3">
                      <EnvBadge env={app.environment} />
                    </td>
                    <td className="px-5 py-3">
                      <StatusBadge status={app.status} />
                    </td>
                    <td className="px-5 py-3 text-sm text-zinc-400">
                      {app.owner_name}
                    </td>
                    <td className="px-5 py-3 text-sm text-zinc-400">
                      {formatDate(app.created_at)}
                    </td>
                    <td className="px-5 py-3 text-right">
                      {isAdmin ? (
                        <div className="relative inline-block">
                          <button
                            onClick={() => setActionsOpen(actionsOpen === app.id ? null : app.id)}
                            className="rounded-lg p-1.5 text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300 transition-colors"
                          >
                            <MoreHorizontal className="h-4 w-4" />
                          </button>
                          {actionsOpen === app.id && (
                            <>
                              <div className="fixed inset-0 z-30" onClick={() => setActionsOpen(null)} />
                              <div className="absolute right-0 z-40 mt-1 w-44 rounded-lg border border-zinc-800 bg-[#111] shadow-xl py-1">
                                <Link
                                  href={`/applications/${app.id}`}
                                  className="flex w-full items-center gap-2 px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-800 transition-colors"
                                >
                                  View Details
                                </Link>
                                <button
                                  onClick={() => { setActionsOpen(null); setEditApp(app) }}
                                  className="flex w-full items-center gap-2 px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-800 transition-colors"
                                >
                                  Edit App Settings
                                </button>
                                <div className="my-1 border-t border-zinc-800" />
                                {app.status === 'ACTIVE' && (
                                  <>
                                    <button
                                      onClick={() => { setActionsOpen(null); setStatusConfirm({ app, newStatus: 'INACTIVE' }) }}
                                      className="flex w-full items-center gap-2 px-3 py-2 text-sm text-amber-400 hover:bg-amber-500/10 transition-colors"
                                    >
                                      Mark Inactive
                                    </button>
                                    <button
                                      onClick={() => { setActionsOpen(null); setStatusConfirm({ app, newStatus: 'SUSPENDED' }) }}
                                      className="flex w-full items-center gap-2 px-3 py-2 text-sm text-red-400 hover:bg-red-500/10 transition-colors"
                                    >
                                      Suspend App
                                    </button>
                                  </>
                                )}
                                {app.status !== 'ACTIVE' && (
                                  <button
                                    onClick={() => { setActionsOpen(null); setStatusConfirm({ app, newStatus: 'ACTIVE' }) }}
                                    className="flex w-full items-center gap-2 px-3 py-2 text-sm text-emerald-400 hover:bg-emerald-500/10 transition-colors"
                                  >
                                    Activate App
                                  </button>
                                )}
                              </div>
                            </>
                          )}
                        </div>
                      ) : (
                        <Link href={`/applications/${app.id}`} className="text-sm font-medium text-indigo-400 hover:text-indigo-300">
                          View
                        </Link>
                      )}
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
              Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)} of {total} applications
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

      {/* Create Application Modal */}
      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="Register Application">
        <CreateAppForm onClose={() => setCreateOpen(false)} />
      </Modal>

      {/* Edit Application Modal */}
      <Modal open={!!editApp} onClose={() => setEditApp(null)} title="Edit Application">
        {editApp && <EditAppForm app={editApp} onClose={() => setEditApp(null)} />}
      </Modal>

      {/* Status Confirm Dialog */}
      <ConfirmDialog
        open={!!statusConfirm}
        onClose={() => setStatusConfirm(null)}
        onConfirm={handleStatusChange}
        loading={statusLoading}
        destructive={statusConfirm?.newStatus === 'SUSPENDED'}
        title={`Change Status to ${statusConfirm?.newStatus}`}
        message={`Are you sure you want to change the status of ${statusConfirm?.app.name} to ${statusConfirm?.newStatus}?`}
        confirmLabel="Change Status"
      />

      {/* Toast notifications */}
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  )
}
