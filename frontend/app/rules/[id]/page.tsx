"use client"

import { useState, useEffect, useCallback } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { PageHeader } from "@/components/layout/PageHeader"
import { rulesApi } from "@/lib/api/rules"
import { DetectionRule } from "@/lib/types/rule"
import { usePermissions } from "@/lib/permissions"
import { ArrowLeft, Loader2, Target, AlertTriangle, Edit2, Play, Square, Calendar, User, LayoutGrid } from "lucide-react"

export default function RuleDetailPage() {
  const params = useParams()
  const router = useRouter()
  const { hasPermission, isLoading } = usePermissions()
  const canManage = hasPermission('RULES_MANAGE')

  const [rule, setRule] = useState<DetectionRule | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchRule = useCallback(async () => {
    try {
      const data = await rulesApi.get(params.id as string)
      setRule(data)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch rule')
    } finally {
      setLoading(false)
    }
  }, [params.id])

  useEffect(() => {
    fetchRule()
  }, [fetchRule])

  const toggleStatus = async () => {
    if (!rule) return
    try {
      const updated = await rulesApi.updateStatus(rule.id, !rule.enabled)
      setRule(updated)
    } catch (e: any) {
      console.error(e)
    }
  }

  if (loading) return <div className="flex justify-center p-12"><Loader2 className="h-8 w-8 animate-spin text-zinc-500" /></div>
  if (error) return <div className="text-red-400 p-6">{error}</div>
  if (!rule) return null

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center gap-4 mb-6">
        <Link href="/rules" className="rounded-full p-2 hover:bg-zinc-800 text-zinc-400 hover:text-white transition-colors">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <PageHeader title={rule.name} description="Rule details and configuration." />
        <div className="ml-auto flex items-center gap-3">
          {canManage && (
            <>
              <button
                onClick={toggleStatus}
                className="flex items-center gap-2 rounded-lg border border-zinc-700 bg-zinc-800 px-4 py-2 text-sm font-medium text-zinc-300 hover:bg-zinc-700 transition-colors"
              >
                {rule.enabled ? <Square className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                {rule.enabled ? 'Disable' : 'Enable'}
              </button>
              <Link
                href={`/rules/${rule.id}/edit`}
                className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 transition-colors"
              >
                <Edit2 className="h-4 w-4" />
                Edit Rule
              </Link>
            </>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          <div className="rounded-xl border border-zinc-800 bg-[#0a0a0a] overflow-hidden">
            <div className="border-b border-zinc-800 bg-zinc-900/50 px-6 py-4 flex items-center gap-3">
              <Target className="h-5 w-5 text-indigo-400" />
              <h2 className="text-lg font-medium text-white">Rule Configuration</h2>
            </div>
            <div className="p-6 grid grid-cols-2 gap-6">
              <div>
                <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-1">Status</p>
                <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  rule.enabled ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' : 'bg-zinc-800 text-zinc-400 border border-zinc-700'
                }`}>
                  {rule.enabled ? 'Enabled' : 'Disabled'}
                </span>
              </div>
              <div>
                <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-1">Severity</p>
                <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${
                  rule.severity === 'CRITICAL' ? 'bg-red-500/10 text-red-400 border border-red-500/20' :
                  rule.severity === 'HIGH' ? 'bg-orange-500/10 text-orange-400 border border-orange-500/20' :
                  rule.severity === 'MEDIUM' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                  'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                }`}>
                  {rule.severity}
                </span>
              </div>
              <div className="col-span-2">
                <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-1">Description</p>
                <p className="text-sm text-zinc-300">{rule.description || 'No description provided.'}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-1">Event Type</p>
                <p className="text-sm font-medium text-zinc-200">{rule.event_type}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-1">Group By</p>
                <p className="text-sm font-medium text-zinc-200">{rule.group_by}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-1">Threshold</p>
                <p className="text-sm font-medium text-zinc-200">{rule.threshold} occurrences</p>
              </div>
              <div>
                <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-1">Time Window</p>
                <p className="text-sm font-medium text-zinc-200">{rule.window_seconds} seconds</p>
              </div>
            </div>
          </div>
        </div>
        
        <div className="space-y-6">
          <div className="rounded-xl border border-zinc-800 bg-[#0a0a0a] overflow-hidden">
             <div className="border-b border-zinc-800 bg-zinc-900/50 px-6 py-4">
              <h2 className="text-sm font-medium text-white">Metadata</h2>
            </div>
            <div className="p-6 space-y-4">
              <div className="flex items-center gap-3 text-sm">
                <Calendar className="h-4 w-4 text-zinc-500" />
                <div>
                  <p className="text-zinc-500">Created</p>
                  <p className="text-zinc-300">{new Date(rule.created_at).toLocaleString()}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 text-sm">
                <LayoutGrid className="h-4 w-4 text-zinc-500" />
                <div>
                  <p className="text-zinc-500">Application Scope</p>
                  <p className="text-zinc-300">{rule.application_id ? rule.application_id : 'Global'}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 text-sm">
                <Target className="h-4 w-4 text-zinc-500" />
                <div>
                  <p className="text-zinc-500">Rule Type</p>
                  <p className="text-zinc-300">{rule.rule_type}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
