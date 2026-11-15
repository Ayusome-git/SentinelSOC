"use client"

import { useState, useEffect, useCallback } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { PageHeader } from "@/components/layout/PageHeader"
import { rulesApi } from "@/lib/api/rules"
import { usePermissions } from "@/lib/permissions"
import { ArrowLeft, Loader2, Target, AlertTriangle } from "lucide-react"

export default function EditRulePage() {
  const params = useParams()
  const router = useRouter()
  const { hasPermission, isLoading } = usePermissions()
  const canManage = hasPermission('RULES_MANAGE')

  const [form, setForm] = useState({
    name: '',
    description: '',
    severity: 'MEDIUM',
    threshold: 5,
    window_seconds: 300,
    enabled: true
  })
  
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const fetchRule = useCallback(async () => {
    try {
      const data = await rulesApi.get(params.id as string)
      setForm({
        name: data.name,
        description: data.description || '',
        severity: data.severity,
        threshold: data.threshold ?? 5,
        window_seconds: data.window_seconds ?? 300,
        enabled: data.enabled
      })
    } catch (err: any) {
      setError(err.message || 'Failed to fetch rule')
    } finally {
      setLoading(false)
    }
  }, [params.id])

  useEffect(() => {
    fetchRule()
  }, [fetchRule])

  if (isLoading || loading) return <div className="flex justify-center p-12"><Loader2 className="h-8 w-8 animate-spin text-zinc-500" /></div>
  if (!canManage) {
    router.push(`/rules/${params.id}`)
    return null
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    
    if (!form.name.trim()) return setError('Name is required')
    if (form.threshold < 1) return setError('Threshold must be at least 1')
    if (form.window_seconds < 1) return setError('Window must be at least 1 second')

    setSubmitting(true)
    try {
      await rulesApi.update(params.id as string, form)
      router.push(`/rules/${params.id}`)
    } catch (err: any) {
      setError(err.message || 'Failed to update rule')
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center gap-4 mb-6">
        <Link href={`/rules/${params.id}`} className="rounded-full p-2 hover:bg-zinc-800 text-zinc-400 hover:text-white transition-colors">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <PageHeader title="Edit Detection Rule" description="Update rule configuration." />
      </div>

      <div className="rounded-xl border border-zinc-800 bg-[#0a0a0a] overflow-hidden">
        <div className="border-b border-zinc-800 bg-zinc-900/50 px-6 py-4 flex items-center gap-3">
          <Target className="h-5 w-5 text-indigo-400" />
          <h2 className="text-lg font-medium text-white">Rule Configuration</h2>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {error && (
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2 md:col-span-2">
              <label className="text-sm font-medium text-zinc-300">Rule Name <span className="text-red-400">*</span></label>
              <input
                type="text"
                value={form.name}
                onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                className="w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
              />
            </div>

            <div className="space-y-2 md:col-span-2">
              <label className="text-sm font-medium text-zinc-300">Description</label>
              <textarea
                value={form.description}
                onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                className="w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none min-h-[80px]"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-zinc-300">Severity</label>
              <select
                value={form.severity}
                onChange={e => setForm(f => ({ ...f, severity: e.target.value }))}
                className="w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
              >
                <option value="INFO">Info</option>
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
                <option value="CRITICAL">Critical</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-zinc-300">Threshold (Count) <span className="text-red-400">*</span></label>
              <input
                type="number"
                min="1"
                value={form.threshold}
                onChange={e => setForm(f => ({ ...f, threshold: parseInt(e.target.value) || 1 }))}
                className="w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-zinc-300">Time Window (Seconds) <span className="text-red-400">*</span></label>
              <input
                type="number"
                min="1"
                value={form.window_seconds}
                onChange={e => setForm(f => ({ ...f, window_seconds: parseInt(e.target.value) || 60 }))}
                className="w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
              />
            </div>

            <div className="space-y-2 md:col-span-2 flex items-center gap-3 pt-2">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.enabled}
                  onChange={e => setForm(f => ({ ...f, enabled: e.target.checked }))}
                  className="w-4 h-4 rounded border-zinc-700 text-indigo-600 focus:ring-indigo-600 bg-zinc-900"
                />
                <span className="text-sm font-medium text-zinc-300">Rule Enabled</span>
              </label>
            </div>
          </div>

          <div className="border-t border-zinc-800 pt-6 flex items-center justify-end gap-3">
            <Link
              href={`/rules/${params.id}`}
              className="px-4 py-2 rounded-lg border border-zinc-700 bg-zinc-800 text-sm font-medium text-zinc-300 hover:bg-zinc-700 transition-colors"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 rounded-lg bg-indigo-600 text-sm font-medium text-white hover:bg-indigo-700 transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
