"use client"

import { useState, useEffect, useCallback } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { SeverityBadge } from "@/components/ui/SeverityBadge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { PageHeader } from "@/components/layout/PageHeader"
import { eventsApi } from "@/lib/api/events"
import { applicationsApi } from "@/lib/api/applications"
import type { SecurityEvent, EventAnalyticsResponse } from "@/lib/types/event"
import type { Application } from "@/lib/types/application"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { 
  Loader2, AlertTriangle, ShieldAlert, X, Search, Filter, 
  ChevronDown, Copy, CheckCircle2, Clock, Activity 
} from "lucide-react"
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer 
} from 'recharts'
import { format, subHours, subDays, formatISO } from 'date-fns'

// Format helper
const formatNumber = (num: number) => new Intl.NumberFormat('en-US').format(num)

// --- Components ---

function EventDetailDrawer({ 
  event, 
  onClose,
  onFilter 
}: { 
  event: SecurityEvent, 
  onClose: () => void,
  onFilter: (key: string, value: string) => void
}) {
  const [copied, setCopied] = useState<string | null>(null)

  const handleCopy = (key: string, value: string) => {
    navigator.clipboard.writeText(value)
    setCopied(key)
    setTimeout(() => setCopied(null), 2000)
  }

  if (!event) return null
  
  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div 
        className="w-full max-w-lg h-full bg-zinc-950 border-l border-zinc-800 shadow-2xl flex flex-col overflow-y-auto animate-in slide-in-from-right"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-6 border-b border-zinc-800 bg-zinc-900/50 sticky top-0 z-10">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-zinc-800 rounded-lg border border-zinc-700">
              <ShieldAlert className="h-5 w-5 text-indigo-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">Event Details</h2>
              <div className="flex items-center gap-2 mt-1">
                <p className="text-xs text-zinc-500 font-mono">{event.id}</p>
                <button onClick={() => handleCopy('id', event.id)} className="text-zinc-500 hover:text-white">
                  {copied === 'id' ? <CheckCircle2 className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                </button>
              </div>
            </div>
          </div>
          <button onClick={onClose} className="p-2 text-zinc-400 hover:text-white rounded-md hover:bg-zinc-800 transition-colors">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6 space-y-8">
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-lg border border-zinc-800 bg-[#0a0a0a]">
              <p className="text-xs text-zinc-500 mb-1">Application</p>
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-white">{event.application_name}</p>
                <button 
                  onClick={() => onFilter('application_id', event.application_id)}
                  className="text-[10px] bg-zinc-800 text-zinc-300 px-2 py-0.5 rounded hover:bg-zinc-700"
                >
                  Filter
                </button>
              </div>
            </div>
            <div className="p-4 rounded-lg border border-zinc-800 bg-[#0a0a0a]">
              <p className="text-xs text-zinc-500 mb-1">Severity</p>
              <SeverityBadge severity={event.severity} />
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-sm font-medium text-zinc-200 border-b border-zinc-800 pb-2">Overview</h3>
            <div className="grid grid-cols-2 gap-y-6 text-sm">
              <div>
                <p className="text-xs text-zinc-500 mb-1">Event Type</p>
                <div className="flex items-center gap-2">
                  <p className="text-zinc-300 font-mono text-xs">{event.event_type}</p>
                  <button onClick={() => onFilter('event_type', event.event_type)} className="text-zinc-500 hover:text-indigo-400"><Filter className="h-3 w-3" /></button>
                </div>
              </div>
              <div>
                <p className="text-xs text-zinc-500 mb-1">Timestamp</p>
                <p className="text-zinc-300">{format(new Date(event.timestamp), 'PPpp')}</p>
              </div>
              <div className="col-span-2">
                <p className="text-xs text-zinc-500 mb-1">Message</p>
                <p className="text-zinc-300 bg-zinc-900 p-3 rounded-md border border-zinc-800 mt-1">{event.message || '—'}</p>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-sm font-medium text-zinc-200 border-b border-zinc-800 pb-2">Context</h3>
            <div className="grid grid-cols-2 gap-y-6 text-sm">
              <div>
                <p className="text-xs text-zinc-500 mb-1">Source IP</p>
                {event.source_ip ? (
                  <div className="flex items-center gap-2">
                    <p className="text-zinc-300 font-mono text-xs">{event.source_ip}</p>
                    <button onClick={() => handleCopy('ip', event.source_ip!)} className="text-zinc-500 hover:text-white">
                      {copied === 'ip' ? <CheckCircle2 className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                    </button>
                    <button onClick={() => onFilter('source_ip', event.source_ip!)} className="text-zinc-500 hover:text-indigo-400"><Filter className="h-3 w-3" /></button>
                  </div>
                ) : <p className="text-zinc-500">—</p>}
              </div>
              <div>
                <p className="text-xs text-zinc-500 mb-1">Username</p>
                {event.username || event.user_id ? (
                  <div className="flex items-center gap-2">
                    <p className="text-zinc-300">{event.username || event.user_id}</p>
                    <button onClick={() => onFilter('username', event.username || event.user_id!)} className="text-zinc-500 hover:text-indigo-400"><Filter className="h-3 w-3" /></button>
                  </div>
                ) : <p className="text-zinc-500">—</p>}
              </div>
              
              <div className="col-span-2">
                <p className="text-xs text-zinc-500 mb-1">User Agent</p>
                <p className="text-zinc-300 text-xs break-all bg-zinc-900 p-2 rounded border border-zinc-800">{event.user_agent || '—'}</p>
              </div>

              <div>
                <p className="text-xs text-zinc-500 mb-1">HTTP Method</p>
                <p className="text-zinc-300 font-mono">{event.http_method || '—'}</p>
              </div>
              <div>
                <p className="text-xs text-zinc-500 mb-1">Path</p>
                {event.request_path ? (
                  <div className="flex items-center gap-2">
                    <p className="text-zinc-300 break-all">{event.request_path}</p>
                    <button onClick={() => onFilter('request_path', event.request_path!)} className="text-zinc-500 hover:text-indigo-400 min-w-4"><Filter className="h-3 w-3" /></button>
                  </div>
                ) : <p className="text-zinc-500">—</p>}
              </div>

              <div className="col-span-2">
                <p className="text-xs text-zinc-500 mb-1">Request ID</p>
                {event.request_id ? (
                  <div className="flex items-center gap-2">
                    <p className="text-zinc-300 font-mono text-xs break-all">{event.request_id}</p>
                    <button onClick={() => handleCopy('req', event.request_id!)} className="text-zinc-500 hover:text-white">
                      {copied === 'req' ? <CheckCircle2 className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                    </button>
                    <button onClick={() => onFilter('request_id', event.request_id!)} className="text-zinc-500 hover:text-indigo-400"><Filter className="h-3 w-3" /></button>
                  </div>
                ) : <p className="text-zinc-500">—</p>}
              </div>
              
              <div className="col-span-2">
                <p className="text-xs text-zinc-500 mb-1">Session ID</p>
                {event.session_id ? (
                  <div className="flex items-center gap-2">
                    <p className="text-zinc-300 font-mono text-xs break-all">{event.session_id}</p>
                    <button onClick={() => handleCopy('sess', event.session_id!)} className="text-zinc-500 hover:text-white">
                      {copied === 'sess' ? <CheckCircle2 className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                    </button>
                    <button onClick={() => onFilter('session_id', event.session_id!)} className="text-zinc-500 hover:text-indigo-400"><Filter className="h-3 w-3" /></button>
                  </div>
                ) : <p className="text-zinc-500">—</p>}
              </div>
            </div>
          </div>

          {event.metadata && Object.keys(event.metadata).length > 0 && (
            <div className="space-y-4">
              <h3 className="text-sm font-medium text-zinc-200 border-b border-zinc-800 pb-2">Metadata</h3>
              <div className="rounded-lg border border-zinc-800 bg-[#0a0a0a] p-4 overflow-x-auto">
                <pre className="text-xs text-zinc-300 font-mono">
                  {JSON.stringify(event.metadata, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// --- Main Page ---

export default function EventsPage() {
  const router = useRouter()
  const searchParams = useSearchParams()

  const [events, setEvents] = useState<SecurityEvent[]>([])
  const [analytics, setAnalytics] = useState<EventAnalyticsResponse | null>(null)
  const [apps, setApps] = useState<Application[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // State from URL
  const page = parseInt(searchParams.get('page') || '1')
  const pageSize = 50
  
  const search = searchParams.get('search') || ''
  const severity = searchParams.get('severity') || ''
  const eventType = searchParams.get('event_type') || ''
  const appId = searchParams.get('application_id') || ''
  const sourceIp = searchParams.get('source_ip') || ''
  const username = searchParams.get('username') || ''
  const requestPath = searchParams.get('request_path') || ''
  const requestId = searchParams.get('request_id') || ''
  const sessionId = searchParams.get('session_id') || ''
  const timeRange = searchParams.get('time_range') || '24h'
  
  const [searchInput, setSearchInput] = useState(search)
  const [showFilters, setShowFilters] = useState(false)
  const [selectedEvent, setSelectedEvent] = useState<SecurityEvent | null>(null)

  // Calculate dates based on timeRange
  const getDateRange = useCallback(() => {
    const now = new Date()
    let start: Date
    switch (timeRange) {
      case '1h': start = subHours(now, 1); break;
      case '6h': start = subHours(now, 6); break;
      case '24h': start = subDays(now, 1); break;
      case '7d': start = subDays(now, 7); break;
      case '30d': start = subDays(now, 30); break;
      default: start = subDays(now, 1); break;
    }
    return {
      start_date: formatISO(start),
      end_date: formatISO(now)
    }
  }, [timeRange])

  const updateUrl = (updates: Record<string, string | null>) => {
    const params = new URLSearchParams(searchParams.toString())
    Object.entries(updates).forEach(([key, value]) => {
      if (value === null || value === '') {
        params.delete(key)
      } else {
        params.set(key, value)
      }
    })
    // Reset to page 1 if any filter changes
    if (!updates.page && Object.keys(updates).length > 0) {
      params.set('page', '1')
    }
    router.push(`/events?${params.toString()}`)
  }

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (search !== searchInput) {
        updateUrl({ search: searchInput })
      }
    }, 500)
    return () => clearTimeout(timer)
  }, [searchInput, search])

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const dates = getDateRange()
      const query = {
        application_id: appId,
        event_type: eventType,
        severity: severity,
        source_ip: sourceIp,
        username: username,
        request_path: requestPath,
        request_id: requestId,
        session_id: sessionId,
        search: search,
        start_date: dates.start_date,
        end_date: dates.end_date
      }

      // Load apps if not loaded
      if (apps.length === 0) {
        const appsData = await applicationsApi.list({ page_size: 100 })
        setApps(appsData.items)
      }

      const [eventsData, analyticsData] = await Promise.all([
        eventsApi.list({ ...query, page, page_size: pageSize }),
        eventsApi.getAnalytics(query)
      ])

      setEvents(eventsData.items)
      setAnalytics(analyticsData)
    } catch (e: any) {
      setError(e.message || 'Failed to fetch events')
    } finally {
      setLoading(false)
    }
  }, [page, appId, eventType, severity, sourceIp, username, requestPath, requestId, sessionId, search, getDateRange])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const activeFilterCount = [appId, severity, eventType, sourceIp, username, requestPath, requestId, sessionId].filter(Boolean).length

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto pb-10">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <PageHeader 
          title="Event Explorer" 
          description="Investigate and analyze security telemetry."
        />
      </div>

      {error && (
        <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-4 flex items-center gap-3 text-red-400">
          <AlertTriangle className="h-5 w-5" />
          <div className="text-sm">{error}</div>
          <button onClick={() => fetchData()} className="ml-auto text-sm font-medium hover:underline">Retry</button>
        </div>
      )}

      {/* Top Toolbar */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex flex-col sm:flex-row gap-4 items-center justify-between shadow-sm">
        <div className="relative w-full sm:max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
          <input 
            type="text"
            placeholder="Search messages, users, IPs, paths..."
            value={searchInput}
            onChange={e => setSearchInput(e.target.value)}
            className="w-full bg-zinc-950 border border-zinc-800 rounded-lg pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-shadow"
          />
        </div>
        
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <select 
            value={timeRange}
            onChange={e => updateUrl({ time_range: e.target.value })}
            className="bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-indigo-500 h-[38px]"
          >
            <option value="1h">Last 1 Hour</option>
            <option value="6h">Last 6 Hours</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
          
          <button 
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium transition-colors h-[38px] ${
              showFilters || activeFilterCount > 0 
                ? 'bg-indigo-500/10 border-indigo-500/50 text-indigo-400' 
                : 'bg-zinc-950 border-zinc-800 text-zinc-300 hover:bg-zinc-800'
            }`}
          >
            <Filter className="h-4 w-4" />
            Filters {activeFilterCount > 0 && `(${activeFilterCount})`}
          </button>
        </div>
      </div>

      {/* Expanded Filters */}
      {showFilters && (
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 shadow-sm animate-in fade-in slide-in-from-top-2">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="space-y-2">
              <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">Severity</label>
              <select 
                value={severity}
                onChange={e => updateUrl({ severity: e.target.value })}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white focus:ring-1 focus:ring-indigo-500"
              >
                <option value="">Any Severity</option>
                <option value="CRITICAL">Critical</option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
                <option value="LOW">Low</option>
                <option value="INFO">Info</option>
              </select>
            </div>
            
            <div className="space-y-2">
              <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">Application</label>
              <select 
                value={appId}
                onChange={e => updateUrl({ application_id: e.target.value })}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white focus:ring-1 focus:ring-indigo-500"
              >
                <option value="">Any Application</option>
                {apps.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">Event Type</label>
              <input 
                type="text"
                placeholder="e.g. LOGIN_FAILED"
                value={eventType}
                onChange={e => updateUrl({ event_type: e.target.value })}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">Source IP</label>
              <input 
                type="text"
                placeholder="192.168.1.1"
                value={sourceIp}
                onChange={e => updateUrl({ source_ip: e.target.value })}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">Username</label>
              <input 
                type="text"
                value={username}
                onChange={e => updateUrl({ username: e.target.value })}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">Request Path</label>
              <input 
                type="text"
                value={requestPath}
                onChange={e => updateUrl({ request_path: e.target.value })}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">Request ID</label>
              <input 
                type="text"
                value={requestId}
                onChange={e => updateUrl({ request_id: e.target.value })}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">Session ID</label>
              <input 
                type="text"
                value={sessionId}
                onChange={e => updateUrl({ session_id: e.target.value })}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white focus:ring-1 focus:ring-indigo-500"
              />
            </div>
          </div>
          
          <div className="mt-6 flex justify-end border-t border-zinc-800 pt-4">
            <button 
              onClick={() => {
                setSearchInput('')
                router.push('/events')
                setShowFilters(false)
              }}
              className="text-sm text-zinc-400 hover:text-white px-4 py-2"
            >
              Clear All
            </button>
          </div>
        </div>
      )}

      {/* Active Filter Pills */}
      {activeFilterCount > 0 && !showFilters && (
        <div className="flex flex-wrap gap-2">
          {severity && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-zinc-900 border border-zinc-800 text-xs font-medium text-zinc-300">
              Severity: {severity}
              <button onClick={() => updateUrl({ severity: null })} className="text-zinc-500 hover:text-white"><X className="h-3 w-3" /></button>
            </span>
          )}
          {appId && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-zinc-900 border border-zinc-800 text-xs font-medium text-zinc-300">
              App: {apps.find(a => a.id === appId)?.name || appId}
              <button onClick={() => updateUrl({ application_id: null })} className="text-zinc-500 hover:text-white"><X className="h-3 w-3" /></button>
            </span>
          )}
          {eventType && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-zinc-900 border border-zinc-800 text-xs font-medium text-zinc-300">
              Type: {eventType}
              <button onClick={() => updateUrl({ event_type: null })} className="text-zinc-500 hover:text-white"><X className="h-3 w-3" /></button>
            </span>
          )}
          {sourceIp && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-zinc-900 border border-zinc-800 text-xs font-medium text-zinc-300">
              IP: {sourceIp}
              <button onClick={() => updateUrl({ source_ip: null })} className="text-zinc-500 hover:text-white"><X className="h-3 w-3" /></button>
            </span>
          )}
          {username && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-zinc-900 border border-zinc-800 text-xs font-medium text-zinc-300">
              User: {username}
              <button onClick={() => updateUrl({ username: null })} className="text-zinc-500 hover:text-white"><X className="h-3 w-3" /></button>
            </span>
          )}
          {requestPath && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-zinc-900 border border-zinc-800 text-xs font-medium text-zinc-300">
              Path: {requestPath}
              <button onClick={() => updateUrl({ request_path: null })} className="text-zinc-500 hover:text-white"><X className="h-3 w-3" /></button>
            </span>
          )}
          {requestId && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-zinc-900 border border-zinc-800 text-xs font-medium text-zinc-300">
              Req ID: {requestId}
              <button onClick={() => updateUrl({ request_id: null })} className="text-zinc-500 hover:text-white"><X className="h-3 w-3" /></button>
            </span>
          )}
          {sessionId && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-zinc-900 border border-zinc-800 text-xs font-medium text-zinc-300">
              Session ID: {sessionId}
              <button onClick={() => updateUrl({ session_id: null })} className="text-zinc-500 hover:text-white"><X className="h-3 w-3" /></button>
            </span>
          )}
        </div>
      )}

      {/* Analytics Summary */}
      {analytics && (
        <div className="grid gap-6 grid-cols-1 lg:grid-cols-4">
          <div className="lg:col-span-3 bg-zinc-900 border border-zinc-800 rounded-xl p-6 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-sm font-medium text-zinc-200 flex items-center gap-2">
                <Activity className="h-4 w-4 text-indigo-400" /> Event Volume ({timeRange})
              </h3>
              <div className="text-xs text-zinc-500 font-mono bg-zinc-950 px-2 py-1 rounded border border-zinc-800">
                Total: {formatNumber(analytics.total)}
              </div>
            </div>
            <div className="h-48 w-full">
              {analytics.timeline.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={analytics.timeline}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
                    <XAxis 
                      dataKey="timestamp" 
                      tickFormatter={t => format(new Date(t), timeRange === '24h' || timeRange === '1h' || timeRange === '6h' ? 'HH:mm' : 'MMM d')} 
                      stroke="#71717a" 
                      fontSize={10}
                      tickLine={false}
                      axisLine={false}
                      dy={10}
                    />
                    <YAxis 
                      stroke="#71717a" 
                      fontSize={10} 
                      tickLine={false} 
                      axisLine={false}
                      tickFormatter={v => v >= 1000 ? `${(v/1000).toFixed(1)}k` : v}
                      dx={-10}
                    />
                    <RechartsTooltip 
                      contentStyle={{ backgroundColor: '#09090b', borderColor: '#27272a', borderRadius: '8px', fontSize: '12px' }}
                      labelFormatter={t => format(new Date(t as string | number), 'PPpp')}
                    />
                    <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} maxBarSize={40} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-zinc-500 text-sm">
                  No data available for this range
                </div>
              )}
            </div>
          </div>
          
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 shadow-sm flex flex-col">
            <h3 className="text-sm font-medium text-zinc-200 mb-4 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-orange-400" /> Severities
            </h3>
            <div className="flex-1 overflow-y-auto space-y-3">
              {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'].map(s => {
                const count = analytics.severity_counts[s] || 0
                if (count === 0 && Object.keys(analytics.severity_counts).length > 0) return null
                return (
                  <div key={s} className="flex items-center justify-between group cursor-pointer" onClick={() => updateUrl({ severity: s })}>
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${
                        s === 'CRITICAL' ? 'bg-red-500' :
                        s === 'HIGH' ? 'bg-orange-500' :
                        s === 'MEDIUM' ? 'bg-amber-500' :
                        s === 'LOW' ? 'bg-blue-500' :
                        'bg-zinc-500'
                      }`} />
                      <span className="text-xs text-zinc-400 group-hover:text-white transition-colors">{s}</span>
                    </div>
                    <span className="text-xs font-mono text-zinc-300">{formatNumber(count)}</span>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* Events Table */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader className="bg-zinc-950/50">
              <TableRow className="border-zinc-800 hover:bg-transparent">
                <TableHead className="text-zinc-500 font-medium text-xs uppercase tracking-wider w-[180px]">Timestamp</TableHead>
                <TableHead className="text-zinc-500 font-medium text-xs uppercase tracking-wider w-[100px]">Severity</TableHead>
                <TableHead className="text-zinc-500 font-medium text-xs uppercase tracking-wider w-[200px]">Event Type</TableHead>
                <TableHead className="text-zinc-500 font-medium text-xs uppercase tracking-wider w-[160px]">Application</TableHead>
                <TableHead className="text-zinc-500 font-medium text-xs uppercase tracking-wider">Context</TableHead>
                <TableHead className="text-zinc-500 font-medium text-xs uppercase tracking-wider text-right">Source IP</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading && events.length === 0 ? (
                Array(5).fill(0).map((_, i) => (
                  <TableRow key={i} className="border-zinc-800 hover:bg-transparent">
                    <TableCell><Skeleton className="h-4 w-[150px]" /></TableCell>
                    <TableCell><Skeleton className="h-5 w-[80px]" /></TableCell>
                    <TableCell><Skeleton className="h-5 w-[150px]" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-[120px]" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-[250px]" /></TableCell>
                    <TableCell className="text-right"><Skeleton className="h-4 w-[100px] ml-auto" /></TableCell>
                  </TableRow>
                ))
              ) : events.length === 0 ? (
                <TableRow className="border-zinc-800 hover:bg-transparent">
                  <TableCell colSpan={6} className="h-48 text-center text-zinc-500 text-sm">
                    No security events match the current filters.
                  </TableCell>
                </TableRow>
              ) : (
                events.map(event => (
                  <TableRow 
                    key={event.id} 
                    className="border-zinc-800 hover:bg-zinc-800/80 cursor-pointer transition-colors group"
                    onClick={() => setSelectedEvent(event)}
                  >
                    <TableCell className="text-zinc-300 text-xs whitespace-nowrap">
                      {format(new Date(event.timestamp), 'yyyy-MM-dd HH:mm:ss')}
                    </TableCell>
                    <TableCell>
                      <SeverityBadge severity={event.severity} />
                    </TableCell>
                    <TableCell>
                      <div className="font-mono text-[11px] text-zinc-300 truncate max-w-[180px]" title={event.event_type}>
                        {event.event_type}
                      </div>
                    </TableCell>
                    <TableCell className="text-xs text-zinc-400 truncate max-w-[140px]">
                      {event.application_name}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2 text-xs truncate max-w-[300px]">
                        {event.username || event.user_id ? (
                          <span className="text-zinc-300 bg-zinc-800 px-1.5 py-0.5 rounded">{event.username || event.user_id}</span>
                        ) : null}
                        {event.request_path ? (
                          <span className="text-zinc-500 font-mono">{event.request_path}</span>
                        ) : (
                          <span className="text-zinc-600 truncate">{event.message}</span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="font-mono text-[11px] text-zinc-400 text-right">
                      {event.source_ip || '—'}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Pagination Footer */}
        {analytics && (
          <div className="flex items-center justify-between border-t border-zinc-800 bg-zinc-950/50 px-6 py-3">
            <div className="text-xs text-zinc-500">
              Showing <span className="font-medium text-zinc-300">{events.length > 0 ? (page - 1) * pageSize + 1 : 0}</span> to <span className="font-medium text-zinc-300">{Math.min(page * pageSize, analytics.total)}</span> of <span className="font-medium text-zinc-300">{formatNumber(analytics.total)}</span> results
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => updateUrl({ page: String(Math.max(1, page - 1)) })}
                disabled={page === 1 || loading}
                className="rounded border border-zinc-800 bg-zinc-900 px-3 py-1 text-xs font-medium text-zinc-300 hover:bg-zinc-800 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                onClick={() => updateUrl({ page: String(page + 1) })}
                disabled={page * pageSize >= analytics.total || loading || analytics.total === 0}
                className="rounded border border-zinc-800 bg-zinc-900 px-3 py-1 text-xs font-medium text-zinc-300 hover:bg-zinc-800 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {selectedEvent && (
        <EventDetailDrawer 
          event={selectedEvent} 
          onClose={() => setSelectedEvent(null)} 
          onFilter={(key, value) => {
            updateUrl({ [key]: value })
            setSelectedEvent(null)
          }}
        />
      )}
    </div>
  )
}
