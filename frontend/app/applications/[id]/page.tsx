"use client"

import { useState, useEffect, useCallback } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { applicationsApi } from "@/lib/api/applications"
import type { Application } from "@/lib/types/application"
import type { ApiKey } from "@/lib/types/api_key"
import { usePermissions } from "@/lib/permissions"
import {
  ChevronLeft,
  Loader2,
  AlertTriangle,
  Database,
  Activity,
  Code,
  Key,
  Plus,
  Copy,
  CheckCircle2,
  Trash2,
  Clock
} from "lucide-react"

export default function ApplicationDetailPage() {
  const params = useParams()
  const router = useRouter()
  const id = params.id as string

  const { hasPermission } = usePermissions()
  const canManage = hasPermission('APPLICATIONS_MANAGE')

  const [application, setApplication] = useState<Application | null>(null)
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Modal states
  const [showGenerateModal, setShowGenerateModal] = useState(false)
  const [newKeyName, setNewKeyName] = useState('')
  const [newKeySecret, setNewKeySecret] = useState('')
  const [generating, setGenerating] = useState(false)
  const [copied, setCopied] = useState(false)

  const fetchApplicationData = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const appData = await applicationsApi.get(id)
      setApplication(appData)
      
      const keysData = await applicationsApi.listApiKeys(id)
      setApiKeys(keysData)
    } catch (e: any) {
      setError(e.message || 'Failed to load application details')
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    fetchApplicationData()
  }, [fetchApplicationData])

  const handleGenerateKey = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newKeyName.trim()) return
    
    setGenerating(true)
    try {
      const res = await applicationsApi.createApiKey(id, { name: newKeyName })
      setNewKeySecret(res.api_key)
      setApiKeys(prev => [res, ...prev])
    } catch (e: any) {
      alert(e.message || 'Failed to generate API Key')
    } finally {
      setGenerating(false)
    }
  }

  const handleCopySecret = () => {
    navigator.clipboard.writeText(newKeySecret)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const closeSecretModal = () => {
    setShowGenerateModal(false)
    setNewKeySecret('')
    setNewKeyName('')
  }

  const handleRevoke = async (keyId: string) => {
    if (!confirm('Revoke this API key? Any application using this credential will immediately lose access to SentinelSOC.')) return
    
    try {
      await applicationsApi.revokeApiKey(id, keyId, false)
      setApiKeys(prev => prev.map(k => k.id === keyId ? { ...k, is_active: false } : k))
    } catch (e: any) {
      alert(e.message || 'Failed to revoke API key')
    }
  }

  if (loading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-zinc-500" />
      </div>
    )
  }

  if (error || !application) {
    return (
      <div className="space-y-6">
        <Link href="/applications" className="inline-flex items-center text-sm font-medium text-zinc-400 hover:text-white transition-colors">
          <ChevronLeft className="mr-1 h-4 w-4" />
          Back to Applications
        </Link>
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-6 text-center">
          <AlertTriangle className="mx-auto h-10 w-10 text-red-400 mb-3" />
          <h2 className="text-lg font-semibold text-white">Application Not Found</h2>
          <p className="mt-1 text-sm text-red-400">{error || 'The requested application does not exist or you do not have access.'}</p>
          <button onClick={() => router.push('/applications')} className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 transition-colors">
            Return to Directory
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-7xl relative">
      <Link href="/applications" className="inline-flex items-center text-sm font-medium text-zinc-400 hover:text-white transition-colors">
        <ChevronLeft className="mr-1 h-4 w-4" />
        Back to Applications
      </Link>

      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-zinc-800 border border-zinc-700 text-indigo-400">
            <Database className="h-8 w-8" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">{application.name}</h1>
            <div className="mt-1 flex items-center gap-3 text-sm text-zinc-400">
              <span>Slug: {application.slug}</span>
              <span className="h-1 w-1 rounded-full bg-zinc-600" />
              <span>Owner: {application.owner_name}</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
            application.environment === 'PRODUCTION' ? 'bg-indigo-500/15 text-indigo-400' :
            application.environment === 'STAGING' ? 'bg-amber-500/15 text-amber-400' :
            'bg-zinc-500/15 text-zinc-400'
          }`}>
            {application.environment}
          </span>
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
            application.status === 'ACTIVE' ? 'bg-emerald-500/15 text-emerald-400' :
            application.status === 'INACTIVE' ? 'bg-zinc-500/15 text-zinc-400' :
            'bg-red-500/15 text-red-400'
          }`}>
            {application.status}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column: Details */}
        <div className="space-y-6 md:col-span-1">
          <div className="rounded-xl border border-zinc-800 bg-[#0a0a0a] p-5">
            <h3 className="text-sm font-medium text-zinc-200 mb-4 flex items-center gap-2">
              <Activity className="h-4 w-4 text-zinc-400" />
              Application Details
            </h3>
            <div className="space-y-4">
              <div>
                <p className="text-xs text-zinc-500 mb-1">Description</p>
                <p className="text-sm text-zinc-300">{application.description || 'No description provided.'}</p>
              </div>
              <div>
                <p className="text-xs text-zinc-500 mb-1">Application ID</p>
                <p className="text-sm text-zinc-300 font-mono text-xs">{application.id}</p>
              </div>
              <div>
                <p className="text-xs text-zinc-500 mb-1">Registered On</p>
                <p className="text-sm text-zinc-300">{new Date(application.created_at).toLocaleString()}</p>
              </div>
              <div>
                <p className="text-xs text-zinc-500 mb-1">Last Updated</p>
                <p className="text-sm text-zinc-300">{new Date(application.updated_at).toLocaleString()}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Integrations */}
        <div className="space-y-6 md:col-span-2">
          <div className="rounded-xl border border-zinc-800 bg-[#0a0a0a] p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <Code className="h-5 w-5 text-zinc-400" />
                <h3 className="text-lg font-semibold text-white">Integration</h3>
              </div>
              {canManage && (
                <button
                  onClick={() => setShowGenerateModal(true)}
                  className="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium bg-indigo-600 text-white hover:bg-indigo-700 px-4 py-2"
                >
                  <Plus className="h-4 w-4" />
                  Generate API Key
                </button>
              )}
            </div>

            <div className="space-y-4">
              <div className="flex items-center gap-2 text-sm font-medium text-zinc-300 border-b border-zinc-800 pb-2">
                <Key className="h-4 w-4 text-indigo-400" />
                API Keys
              </div>

              {apiKeys.length === 0 ? (
                <div className="text-center py-8 text-zinc-500 text-sm">
                  No API keys generated yet.
                </div>
              ) : (
                <div className="space-y-3">
                  {apiKeys.map(key => {
                    const isExpired = key.expires_at && new Date(key.expires_at) < new Date()
                    let statusLabel = key.is_active ? 'Active' : 'Revoked'
                    let statusClass = key.is_active ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
                    
                    if (key.is_active && isExpired) {
                      statusLabel = 'Expired'
                      statusClass = 'bg-amber-500/10 text-amber-400'
                    }

                    return (
                      <div key={key.id} className="flex items-center justify-between p-4 rounded-lg border border-zinc-800 bg-zinc-900/50">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-zinc-200 text-sm">{key.name}</span>
                            <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium uppercase ${statusClass}`}>
                              {statusLabel}
                            </span>
                          </div>
                          <div className="font-mono text-xs text-zinc-500">
                            {key.key_prefix}••••••••
                          </div>
                          <div className="flex items-center gap-4 text-xs text-zinc-500 mt-2">
                            <span className="flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              Created {new Date(key.created_at).toLocaleDateString()}
                            </span>
                            {key.last_used_at ? (
                              <span>Last used {new Date(key.last_used_at).toLocaleDateString()}</span>
                            ) : (
                              <span>Never used</span>
                            )}
                          </div>
                        </div>
                        {canManage && key.is_active && !isExpired && (
                          <button
                            onClick={() => handleRevoke(key.id)}
                            className="p-2 text-zinc-500 hover:text-red-400 hover:bg-red-500/10 rounded-md transition-colors"
                            title="Revoke API Key"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Generate Modal */}
      {showGenerateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-xl border border-zinc-800 bg-zinc-950 p-6 shadow-2xl">
            {!newKeySecret ? (
              <>
                <h3 className="text-lg font-semibold text-white mb-4">Generate API Key</h3>
                <form onSubmit={handleGenerateKey} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-zinc-400 mb-1">Key Name</label>
                    <input
                      type="text"
                      required
                      value={newKeyName}
                      onChange={e => setNewKeyName(e.target.value)}
                      placeholder="e.g. Production Backend"
                      className="w-full rounded-lg border border-zinc-800 bg-zinc-900 px-4 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>
                  <div className="flex justify-end gap-3 mt-6">
                    <button
                      type="button"
                      onClick={() => setShowGenerateModal(false)}
                      className="rounded-lg px-4 py-2 text-sm font-medium text-zinc-400 hover:text-white"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={generating || !newKeyName.trim()}
                      className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                    >
                      {generating ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                      Generate
                    </button>
                  </div>
                </form>
              </>
            ) : (
              <>
                <div className="text-center mb-6">
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/10 mb-4">
                    <CheckCircle2 className="h-6 w-6 text-emerald-500" />
                  </div>
                  <h3 className="text-lg font-semibold text-white">API Key Created</h3>
                </div>

                <div className="rounded-lg bg-amber-500/10 border border-amber-500/20 p-4 mb-6">
                  <div className="flex gap-3">
                    <AlertTriangle className="h-5 w-5 text-amber-500 shrink-0" />
                    <p className="text-sm text-amber-500/90 leading-relaxed">
                      This key will only be shown once. Please copy it now and store it securely. You will not be able to see it again.
                    </p>
                  </div>
                </div>

                <div className="relative mb-6">
                  <div className="w-full rounded-lg border border-zinc-700 bg-zinc-900 p-4 pr-12 font-mono text-sm text-zinc-300 break-all">
                    {newKeySecret}
                  </div>
                  <button
                    onClick={handleCopySecret}
                    className="absolute right-2 top-2 p-2 text-zinc-400 hover:text-white rounded-md hover:bg-zinc-800 transition-colors"
                    title="Copy to clipboard"
                  >
                    {copied ? <CheckCircle2 className="h-4 w-4 text-emerald-400" /> : <Copy className="h-4 w-4" />}
                  </button>
                </div>

                <button
                  onClick={closeSecretModal}
                  className="w-full rounded-lg bg-zinc-800 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700"
                >
                  Done
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
