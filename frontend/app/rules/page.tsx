"use client"

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { PageHeader } from "@/components/layout/PageHeader"
import { usePermissions } from "@/lib/permissions"
import { rulesApi } from "@/lib/api/rules"
import { DetectionRule } from "@/lib/types/rule"
import {
  Search, Plus, Target, ChevronLeft, ChevronRight, AlertTriangle, Loader2, Play, Square, Activity
} from "lucide-react"

export default function RulesPage() {
  const router = useRouter()
  const { hasPermission, isLoading } = usePermissions()
  const canManage = hasPermission('RULES_MANAGE')
  const canRead = hasPermission('RULES_READ')

  const [rules, setRules] = useState<DetectionRule[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [severityFilter, setSeverityFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchRules = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const data = await rulesApi.list({ 
        page, 
        page_size: pageSize, 
        search: search || undefined,
        category: categoryFilter || undefined,
        severity: severityFilter || undefined
      })
      setRules(data.items)
      setTotal(data.total)
    } catch (e: any) {
      setError(e.message || 'Failed to load rules')
    } finally {
      setLoading(false)
    }
  }, [page, pageSize, search, categoryFilter, severityFilter])

  useEffect(() => {
    if (isLoading) return
    if (!canRead) {
      router.push('/dashboard')
      return
    }
    fetchRules()
  }, [isLoading, canRead, fetchRules, router])

  const toggleStatus = async (id: string, currentEnabled: boolean) => {
    try {
      await rulesApi.updateStatus(id, !currentEnabled)
      fetchRules()
    } catch (e: any) {
      console.error(e)
    }
  }

  const totalPages = Math.ceil(total / pageSize)

  if (isLoading || !canRead) return null

  return (
    <div className="space-y-6 max-w-7xl">
      <PageHeader
        title="Detection Rules"
        description="Manage security detection rules and thresholds."
      />

      <div className="flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
          <input
            type="text"
            placeholder="Search rules..."
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1) }}
            className="w-full rounded-lg border border-zinc-800 bg-zinc-900 py-2 pl-10 pr-3 text-sm text-zinc-300 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>
        
        <div className="flex gap-2">
          <select
            value={categoryFilter}
            onChange={e => { setCategoryFilter(e.target.value); setPage(1) }}
            className="rounded-lg border border-zinc-800 bg-zinc-900 py-2 px-3 text-sm text-zinc-300 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">All Categories</option>
            <option value="AUTHENTICATION">Authentication</option>
            <option value="AUTHORIZATION">Authorization</option>
            <option value="API_ABUSE">API Abuse</option>
            <option value="PRIVILEGE_ABUSE">Privilege Abuse</option>
            <option value="WEB_ATTACK">Web Attack</option>
            <option value="ANOMALY">Anomaly</option>
          </select>

          <select
            value={severityFilter}
            onChange={e => { setSeverityFilter(e.target.value); setPage(1) }}
            className="rounded-lg border border-zinc-800 bg-zinc-900 py-2 px-3 text-sm text-zinc-300 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>
        {canManage && (
          <Link
            href="/rules/create"
            className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 transition-colors"
          >
            <Plus className="h-4 w-4" />
            Create Rule
          </Link>
        )}
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4" />
          {error}
        </div>
      )}

      <div className="rounded-xl border border-zinc-800 bg-[#0a0a0a] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-zinc-800">
                <th className="px-5 py-3 text-xs font-medium uppercase text-zinc-500">Name</th>
                <th className="px-5 py-3 text-xs font-medium uppercase text-zinc-500">Category</th>
                <th className="px-5 py-3 text-xs font-medium uppercase text-zinc-500">Type</th>
                <th className="px-5 py-3 text-xs font-medium uppercase text-zinc-500">Severity</th>
                <th className="px-5 py-3 text-xs font-medium uppercase text-zinc-500">Status</th>
                <th className="px-5 py-3 text-xs font-medium uppercase text-zinc-500 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/50">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-5 py-12 text-center">
                    <Loader2 className="h-6 w-6 animate-spin text-zinc-500 mx-auto" />
                  </td>
                </tr>
              ) : rules.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-5 py-12 text-center text-sm text-zinc-500">
                    No rules found.
                  </td>
                </tr>
              ) : (
                rules.map(rule => (
                  <tr key={rule.id} className="group hover:bg-zinc-900/50 transition-colors">
                    <td className="px-5 py-4">
                      <Link href={`/rules/${rule.id}`} className="flex items-center gap-3">
                        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                          <Target className="h-5 w-5" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-zinc-200 group-hover:text-indigo-400 transition-colors">{rule.name}</p>
                          <p className="text-xs text-zinc-500 truncate max-w-xs">{rule.description || '—'}</p>
                        </div>
                      </Link>
                    </td>
                    <td className="px-5 py-4">
                      {rule.category ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-xs font-medium bg-zinc-800 text-zinc-300 border border-zinc-700">
                          {rule.category}
                        </span>
                      ) : (
                        <span className="text-zinc-500 text-sm">—</span>
                      )}
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex flex-col gap-1">
                        <span className="text-sm text-zinc-300">{rule.rule_type}</span>
                        <span className="text-xs text-zinc-500">{rule.event_type}</span>
                      </div>
                    </td>
                    <td className="px-5 py-4 text-sm">
                      <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${
                        rule.severity === 'CRITICAL' ? 'bg-red-500/10 text-red-400 border border-red-500/20' :
                        rule.severity === 'HIGH' ? 'bg-orange-500/10 text-orange-400 border border-orange-500/20' :
                        rule.severity === 'MEDIUM' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                        'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                      }`}>
                        {rule.severity}
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        rule.enabled ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' : 'bg-zinc-800 text-zinc-400 border border-zinc-700'
                      }`}>
                        {rule.enabled ? 'Enabled' : 'Disabled'}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {canManage && (
                          <button
                            onClick={() => toggleStatus(rule.id, rule.enabled)}
                            className="rounded p-1.5 text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300 transition-colors"
                            title={rule.enabled ? "Disable" : "Enable"}
                          >
                            {rule.enabled ? <Square className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                          </button>
                        )}
                        <Link
                          href={`/rules/${rule.id}`}
                          className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-1.5 text-xs font-medium text-zinc-300 hover:bg-zinc-700 transition-colors"
                        >
                          View
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {totalPages > 1 && (
          <div className="flex items-center justify-between border-t border-zinc-800 px-5 py-3">
            <p className="text-sm text-zinc-500">
              Page {page} of {totalPages}
            </p>
            <div className="flex gap-1">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="p-1.5 text-zinc-500 hover:text-zinc-300 disabled:opacity-30">
                <ChevronLeft className="h-4 w-4" />
              </button>
              <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages} className="p-1.5 text-zinc-500 hover:text-zinc-300 disabled:opacity-30">
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
