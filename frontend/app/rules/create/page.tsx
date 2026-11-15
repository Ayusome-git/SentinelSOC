"use client"

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { PageHeader } from "@/components/layout/PageHeader"
import { rulesApi } from "@/lib/api/rules"
import { usePermissions } from "@/lib/permissions"
import { ArrowLeft, Loader2, Target, AlertTriangle } from "lucide-react"

export default function CreateRulePage() {
  const router = useRouter()
  const { hasPermission, isLoading } = usePermissions()
  const canManage = hasPermission('RULES_MANAGE')

  const [form, setForm] = useState({
    name: '',
    description: '',
    rule_type: 'THRESHOLD',
    category: 'AUTHENTICATION',
    event_type: '',
    severity: 'MEDIUM',
    threshold: 5,
    window_seconds: 300,
    group_by: 'source_ip',
    distinct_field: '',
    pattern: '',
    enabled: true
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  if (isLoading) return null
  if (!canManage) {
    router.push('/rules')
    return null
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    
    if (!form.name.trim()) return setError('Name is required')
    if (!form.event_type.trim()) return setError('Event Type is required')
    
    if (form.rule_type === 'THRESHOLD') {
      if (!form.group_by.trim()) return setError('Group By field is required for Threshold rules')
      if (form.threshold < 1) return setError('Threshold must be at least 1')
      if (form.window_seconds < 1) return setError('Window must be at least 1 second')
    } else if (form.rule_type === 'PATTERN') {
      if (!form.pattern.trim()) return setError('Pattern is required for Pattern rules')
    } else if (form.rule_type === 'SEQUENCE') {
      if (form.window_seconds < 1) return setError('Window must be at least 1 second')
    }

    setSubmitting(true)
    try {
      const payload: any = { ...form }
      if (form.rule_type === 'PATTERN') {
        delete payload.threshold
        delete payload.window_seconds
        delete payload.group_by
        delete payload.distinct_field
      } else if (form.rule_type === 'SEQUENCE') {
        delete payload.threshold
        delete payload.group_by
        delete payload.distinct_field
        delete payload.pattern
      } else {
        delete payload.pattern
      }

      await rulesApi.create(payload)
      router.push('/rules')
    } catch (err: any) {
      setError(err.message || 'Failed to create rule')
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center gap-4 mb-6">
        <Link href="/rules" className="rounded-full p-2 hover:bg-zinc-800 text-zinc-400 hover:text-white transition-colors">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <PageHeader title="Create Detection Rule" description="Define a new security threshold rule." />
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
            <div className="space-y-2">
              <label className="text-sm font-medium text-zinc-300">Rule Name <span className="text-red-400">*</span></label>
              <input
                type="text"
                value={form.name}
                onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                className="w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
                placeholder="e.g. Multiple Failed Logins"
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium text-zinc-300">Event Type <span className="text-red-400">*</span></label>
              <input
                type="text"
                value={form.event_type}
                onChange={e => setForm(f => ({ ...f, event_type: e.target.value }))}
                className="w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
                placeholder="e.g. AUTH_FAILED"
              />
            </div>

            <div className="space-y-2 md:col-span-2">
              <label className="text-sm font-medium text-zinc-300">Description</label>
              <textarea
                value={form.description}
                onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                className="w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none min-h-[80px]"
                placeholder="Describe what this rule detects..."
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-zinc-300">Rule Type</label>
              <select
                value={form.rule_type}
                onChange={e => setForm(f => ({ ...f, rule_type: e.target.value }))}
                className="w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
              >
                <option value="THRESHOLD">Threshold</option>
                <option value="PATTERN">Pattern</option>
                <option value="SEQUENCE">Sequence</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-zinc-300">Category</label>
              <select
                value={form.category}
                onChange={e => setForm(f => ({ ...f, category: e.target.value }))}
                className="w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
              >
                <option value="AUTHENTICATION">Authentication</option>
                <option value="AUTHORIZATION">Authorization</option>
                <option value="API_ABUSE">API Abuse</option>
                <option value="PRIVILEGE_ABUSE">Privilege Abuse</option>
                <option value="WEB_ATTACK">Web Attack</option>
                <option value="ANOMALY">Anomaly</option>
              </select>
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
            
            {form.rule_type === 'PATTERN' && (
              <div className="space-y-2 md:col-span-2">
                <label className="text-sm font-medium text-zinc-300">Pattern (Regex) <span className="text-red-400">*</span></label>
                <input
                  type="text"
                  value={form.pattern}
                  onChange={e => setForm(f => ({ ...f, pattern: e.target.value }))}
                  className="w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
                  placeholder="e.g. (?i)(\.\./|\.\.\\|/etc/passwd)"
                />
              </div>
            )}

            {form.rule_type === 'THRESHOLD' && (
              <>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-zinc-300">Group By Field <span className="text-red-400">*</span></label>
                  <input
                    type="text"
                    value={form.group_by}
                    onChange={e => setForm(f => ({ ...f, group_by: e.target.value }))}
                    className="w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
                    placeholder="e.g. source_ip"
                  />
                  <p className="text-xs text-zinc-500">The event field used to group occurrences.</p>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-zinc-300">Distinct Field (Optional)</label>
                  <input
                    type="text"
                    value={form.distinct_field}
                    onChange={e => setForm(f => ({ ...f, distinct_field: e.target.value }))}
                    className="w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
                    placeholder="e.g. username"
                  />
                  <p className="text-xs text-zinc-500">Count unique values of this field instead of total events.</p>
                </div>
              </>
            )}

            {(form.rule_type === 'THRESHOLD' || form.rule_type === 'SEQUENCE') && (
              <>
                {form.rule_type === 'THRESHOLD' && (
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
                )}
                
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
              </>
            )}

            <div className="space-y-2 md:col-span-2 flex items-center gap-3 pt-2">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.enabled}
                  onChange={e => setForm(f => ({ ...f, enabled: e.target.checked }))}
                  className="w-4 h-4 rounded border-zinc-700 text-indigo-600 focus:ring-indigo-600 bg-zinc-900"
                />
                <span className="text-sm font-medium text-zinc-300">Enable this rule immediately</span>
              </label>
            </div>
          </div>

          <div className="border-t border-zinc-800 pt-6 flex items-center justify-end gap-3">
            <Link
              href="/rules"
              className="px-4 py-2 rounded-lg border border-zinc-700 bg-zinc-800 text-sm font-medium text-zinc-300 hover:bg-zinc-700 transition-colors"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 rounded-lg bg-indigo-600 text-sm font-medium text-white hover:bg-indigo-700 transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Create Rule'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
