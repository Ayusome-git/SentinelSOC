"use client"

import { useState, useEffect, useCallback, useMemo } from 'react'
import { PageHeader } from "@/components/layout/PageHeader"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { 
  Activity, ShieldAlert, AppWindow, Zap, RefreshCw, Clock, 
  Server, AlertTriangle, AlertCircle, CheckCircle2, XCircle, Loader2
} from "lucide-react"
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { dashboardApi } from "@/lib/api/dashboard"
import { DashboardOverviewResponse } from '@/lib/types/dashboard'
import { subMinutes, subHours, subDays, formatDistanceToNow, format } from 'date-fns'
import Link from 'next/link'
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  PieChart, Pie, Cell
} from 'recharts'

const TIME_RANGES = [
  { label: 'Last 15 minutes', value: '15m', getStart: () => subMinutes(new Date(), 15) },
  { label: 'Last 1 hour', value: '1h', getStart: () => subHours(new Date(), 1) },
  { label: 'Last 6 hours', value: '6h', getStart: () => subHours(new Date(), 6) },
  { label: 'Last 24 hours', value: '24h', getStart: () => subHours(new Date(), 24) },
  { label: 'Last 7 days', value: '7d', getStart: () => subDays(new Date(), 7) },
]

const COLORS = {
  INFO: '#3b82f6', // blue-500
  LOW: '#10b981', // emerald-500
  MEDIUM: '#f59e0b', // amber-500
  HIGH: '#f97316', // orange-500
  CRITICAL: '#ef4444', // red-500
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardOverviewResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [timeRange, setTimeRange] = useState('24h')
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date())

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const rangeOption = TIME_RANGES.find(r => r.value === timeRange) || TIME_RANGES[3]
      const start = rangeOption.getStart()
      const end = new Date()
      
      const response = await dashboardApi.getOverview({
        start_date: start.toISOString(),
        end_date: end.toISOString()
      })
      setData(response)
      setLastRefreshed(new Date())
    } catch (err: any) {
      console.error("Failed to fetch dashboard data", err)
      setError(err.message || "Failed to load dashboard")
    } finally {
      setLoading(false)
    }
  }, [timeRange])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  useEffect(() => {
    if (!autoRefresh) return
    const interval = setInterval(() => {
      fetchData()
    }, 30000) // 30s
    return () => clearInterval(interval)
  }, [autoRefresh, fetchData])

  // Chart Data preparation
  const timelineData = useMemo(() => {
    if (!data?.event_timeline) return []
    return data.event_timeline.map(pt => ({
      ...pt,
      displayTime: format(new Date(pt.timestamp), timeRange === '7d' ? 'MMM d' : 'HH:mm')
    }))
  }, [data?.event_timeline, timeRange])

  const severityData = useMemo(() => {
    if (!data?.severity_distribution) return []
    return Object.entries(data.severity_distribution)
      .map(([name, value]) => ({ name, value }))
      .filter(item => item.value > 0)
      .sort((a, b) => b.value - a.value)
  }, [data?.severity_distribution])

  const getSeverityColor = (sev: string) => COLORS[sev as keyof typeof COLORS] || '#71717a'

  const renderBadge = (severity: string) => {
    switch (severity.toUpperCase()) {
      case 'CRITICAL': return <Badge variant="destructive">CRITICAL</Badge>
      case 'HIGH': return <Badge className="bg-orange-500 hover:bg-orange-600 text-white">HIGH</Badge>
      case 'MEDIUM': return <Badge className="bg-amber-500 hover:bg-amber-600 text-white">MEDIUM</Badge>
      case 'LOW': return <Badge className="bg-emerald-500 hover:bg-emerald-600 text-white">LOW</Badge>
      case 'INFO': return <Badge className="bg-blue-500 hover:bg-blue-600 text-white">INFO</Badge>
      default: return <Badge variant="outline">{severity}</Badge>
    }
  }

  const freshness = data?.latest_event_timestamp 
    ? formatDistanceToNow(new Date(data.latest_event_timestamp.endsWith('Z') || data.latest_event_timestamp.includes('+') ? data.latest_event_timestamp : data.latest_event_timestamp + 'Z'), { addSuffix: true })
    : 'No events received'

  if (error) {
    return (
      <div className="space-y-6 max-w-7xl">
        <PageHeader title="Security Operations Center" description="Real-time security monitoring and event telemetry" />
        <Card className="bg-red-950/20 border-red-900/50">
          <CardContent className="flex flex-col items-center justify-center h-64 space-y-4">
            <AlertCircle className="h-12 w-12 text-red-500" />
            <p className="text-zinc-200">{error}</p>
            <Button onClick={fetchData} variant="outline">Retry</Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-[1400px]">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Security Operations Center</h1>
          <p className="text-zinc-400">Real-time security monitoring and event telemetry</p>
        </div>
        
        <div className="flex items-center gap-3">
          <Select value={timeRange} onValueChange={(val) => setTimeRange(val || '')}>
            <SelectTrigger className="w-[180px] bg-zinc-900 border-zinc-800 text-white">
              <Clock className="mr-2 h-4 w-4" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-zinc-900 border-zinc-800 text-white">
              {TIME_RANGES.map(r => (
                <SelectItem key={r.value} value={r.value} className="hover:bg-zinc-800 focus:bg-zinc-800 cursor-pointer">
                  {r.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <Button 
            variant="outline" 
            size="icon"
            className={`border-zinc-800 bg-zinc-900 ${autoRefresh ? 'text-blue-400 border-blue-900/50 bg-blue-950/20' : 'text-zinc-400'}`}
            onClick={() => setAutoRefresh(!autoRefresh)}
            title={autoRefresh ? "Disable Auto-Refresh" : "Enable Auto-Refresh (30s)"}
          >
            <RefreshCw className={`h-4 w-4 ${autoRefresh ? 'animate-spin-slow' : ''}`} />
          </Button>
          
          <Button 
            variant="default" 
            onClick={fetchData} 
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            Refresh
          </Button>
        </div>
      </div>

      <div className="flex items-center justify-between text-xs text-zinc-500">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            {data ? <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" /> : <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            Ingestion Status: Operational
          </span>
          <span className="flex items-center gap-1.5">
            <Activity className="h-3.5 w-3.5" />
            Last Event: {freshness}
          </span>
        </div>
        <span>
          {autoRefresh ? (
            <span className="flex items-center gap-1.5 text-blue-400"><span className="h-2 w-2 rounded-full bg-blue-500 animate-pulse"></span> Live Auto-Refresh (30s)</span>
          ) : (
            `Last updated: ${format(lastRefreshed, 'HH:mm:ss')}`
          )}
        </span>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <Link href="/events" className="block focus:outline-none">
          <Card className="bg-zinc-900 border-zinc-800 hover:border-zinc-700 transition-colors cursor-pointer h-full">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-zinc-400">Total Events</CardTitle>
              <Activity className="h-4 w-4 text-zinc-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">
                {loading && !data ? '-' : data?.total_events.toLocaleString()}
              </div>
            </CardContent>
          </Card>
        </Link>
        <Link href="/events?severity=CRITICAL" className="block focus:outline-none">
          <Card className="bg-red-950/20 border-red-900/50 hover:border-red-800/50 transition-colors cursor-pointer h-full">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-red-400">Critical Events</CardTitle>
              <AlertTriangle className="h-4 w-4 text-red-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-500">
                {loading && !data ? '-' : data?.critical_events.toLocaleString()}
              </div>
            </CardContent>
          </Card>
        </Link>
        <Link href="/events?severity=HIGH" className="block focus:outline-none">
          <Card className="bg-orange-950/20 border-orange-900/50 hover:border-orange-800/50 transition-colors cursor-pointer h-full">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-orange-400">High Events</CardTitle>
              <ShieldAlert className="h-4 w-4 text-orange-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-500">
                {loading && !data ? '-' : data?.high_events.toLocaleString()}
              </div>
            </CardContent>
          </Card>
        </Link>
        <Card className="bg-zinc-900 border-zinc-800 h-full">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-zinc-400">Active Apps</CardTitle>
            <AppWindow className="h-4 w-4 text-zinc-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {loading && !data ? '-' : data?.active_applications.toLocaleString()}
            </div>
            <p className="text-xs text-zinc-500 mt-1">Current State</p>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900 border-zinc-800 h-full">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-zinc-400">Events / Hour</CardTitle>
            <Zap className="h-4 w-4 text-zinc-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {loading && !data ? '-' : data?.events_per_hour.toLocaleString()}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-3 lg:grid-cols-4">
        {/* Main Chart */}
        <Card className="md:col-span-2 lg:col-span-3 bg-zinc-900 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-zinc-200">Event Volume</CardTitle>
          </CardHeader>
          <CardContent>
            {loading && !data ? (
              <div className="h-[300px] flex items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-zinc-600" />
              </div>
            ) : timelineData.length === 0 ? (
              <div className="h-[300px] flex items-center justify-center border border-dashed border-zinc-800 rounded-md">
                <p className="text-zinc-500">No events found in this time range.</p>
              </div>
            ) : (
              <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={timelineData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
                    <XAxis dataKey="displayTime" stroke="#71717a" fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis stroke="#71717a" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => val >= 1000 ? `${(val/1000).toFixed(1)}k` : val} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', color: '#fff' }}
                      itemStyle={{ color: '#fff' }}
                      cursor={{fill: '#27272a', opacity: 0.4}}
                    />
                    <Bar dataKey="count" name="Events" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Severity Donut */}
        <Card className="col-span-1 bg-zinc-900 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-zinc-200">Severity</CardTitle>
          </CardHeader>
          <CardContent>
            {loading && !data ? (
              <div className="h-[300px] flex items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-zinc-600" />
              </div>
            ) : severityData.length === 0 ? (
              <div className="h-[300px] flex items-center justify-center border border-dashed border-zinc-800 rounded-md">
                <p className="text-zinc-500">No data</p>
              </div>
            ) : (
              <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={severityData}
                      cx="50%"
                      cy="45%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={2}
                      dataKey="value"
                      stroke="none"
                    >
                      {severityData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={getSeverityColor(entry.name)} />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', color: '#fff' }}
                      itemStyle={{ color: '#fff' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
                <div className="mt-[-20px] flex flex-wrap justify-center gap-3">
                  {severityData.map(entry => (
                    <div key={entry.name} className="flex items-center gap-1.5 text-xs text-zinc-400">
                      <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: getSeverityColor(entry.name) }}></span>
                      {entry.name}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Risk Summary */}
        <Card className="col-span-1 bg-zinc-900 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-zinc-200">Alert Risk Summary</CardTitle>
          </CardHeader>
          <CardContent>
            {loading && !data ? (
              <div className="h-[300px] flex items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-zinc-600" />
              </div>
            ) : (!data?.risk_summary || Object.keys(data.risk_summary).length === 0) ? (
              <div className="h-[300px] flex items-center justify-center border border-dashed border-zinc-800 rounded-md">
                <p className="text-zinc-500">No active alerts</p>
              </div>
            ) : (
              <div className="space-y-4">
                {['CRITICAL', 'HIGH', 'MODERATE', 'LOW'].map(level => {
                  const count = data.risk_summary![level] || 0;
                  return (
                    <Link key={level} href={`/alerts?risk_level=${level}`} className="flex items-center justify-between p-3 rounded border border-zinc-800 bg-zinc-950 hover:bg-zinc-800 transition-colors">
                      <span className="font-medium text-zinc-300">{level} Risk</span>
                      <Badge variant={
                        level === 'CRITICAL' ? 'destructive' :
                        level === 'HIGH' ? 'destructive' :
                        level === 'MODERATE' ? 'warning' : 'secondary'
                      }>{count}</Badge>
                    </Link>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Top Event Types */}
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-zinc-200">Top Event Types</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {(!data?.event_type_distribution || Object.keys(data.event_type_distribution).length === 0) ? (
                <p className="text-sm text-zinc-500 italic">No events recorded.</p>
              ) : (
                Object.entries(data.event_type_distribution)
                  .sort((a, b) => b[1] - a[1])
                  .map(([type, count]) => (
                    <Link key={type} href={`/events?event_type=${type}`} className="flex items-center justify-between p-2 rounded hover:bg-zinc-800/50 transition-colors">
                      <span className="text-sm font-medium text-zinc-300">{type}</span>
                      <span className="text-sm text-zinc-500">{count.toLocaleString()}</span>
                    </Link>
                  ))
              )}
            </div>
          </CardContent>
        </Card>

        {/* Application Activity */}
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-zinc-200">Application Activity</CardTitle>
            <CardDescription className="text-zinc-500">Top log sources</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {(!data?.application_activity || data.application_activity.length === 0) ? (
                <p className="text-sm text-zinc-500 italic">No applications active.</p>
              ) : (
                data.application_activity.map(app => (
                  <Link key={app.application_id} href={`/events?application_id=${app.application_id}`} className="flex items-center justify-between p-2 rounded hover:bg-zinc-800/50 transition-colors">
                    <div className="flex items-center gap-2">
                      <Server className="h-4 w-4 text-zinc-500" />
                      <span className="text-sm font-medium text-zinc-300">{app.application_name}</span>
                    </div>
                    <span className="text-sm text-zinc-500">{app.event_count.toLocaleString()}</span>
                  </Link>
                ))
              )}
            </div>
            
            {data && data.production_events > 0 && (
              <div className="mt-6 p-3 bg-zinc-800/30 rounded-md border border-zinc-800">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-zinc-400 uppercase font-semibold tracking-wider">Production Events</span>
                  <span className="text-sm font-bold text-white">{data.production_events.toLocaleString()}</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Environment Breakdown */}
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-zinc-200">Environment Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
             <div className="space-y-4">
              {(!data?.environment_distribution || Object.keys(data.environment_distribution).length === 0) ? (
                <p className="text-sm text-zinc-500 italic">No apps registered.</p>
              ) : (
                Object.entries(data.environment_distribution).map(([env, count]) => (
                  <div key={env} className="flex items-center justify-between">
                    <span className="text-sm font-medium text-zinc-300">{env}</span>
                    <span className="text-sm font-bold text-white bg-zinc-800 px-2 py-0.5 rounded">{count}</span>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Events Table */}
      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-zinc-200">Recent Security Events</CardTitle>
          <CardDescription className="text-zinc-500">Latest telemetry across all sources</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left text-zinc-400">
              <thead className="text-xs text-zinc-500 uppercase bg-zinc-900 border-b border-zinc-800">
                <tr>
                  <th className="px-4 py-3 font-medium">Time</th>
                  <th className="px-4 py-3 font-medium">Severity</th>
                  <th className="px-4 py-3 font-medium">Event Type</th>
                  <th className="px-4 py-3 font-medium">Application</th>
                  <th className="px-4 py-3 font-medium">User</th>
                  <th className="px-4 py-3 font-medium">Source IP</th>
                </tr>
              </thead>
              <tbody>
                {(!data?.recent_events || data.recent_events.length === 0) ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-zinc-500 border-b border-zinc-800/50">
                      No security events yet. Connect an application to begin sending telemetry.
                    </td>
                  </tr>
                ) : (
                  data.recent_events.map(event => (
                    <tr key={event.id} className="border-b border-zinc-800/50 hover:bg-zinc-800/20 transition-colors">
                      <td className="px-4 py-3 whitespace-nowrap">
                        {format(new Date(event.timestamp.endsWith('Z') || event.timestamp.includes('+') ? event.timestamp : event.timestamp + 'Z'), 'HH:mm:ss')}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        {renderBadge(event.severity)}
                      </td>
                      <td className="px-4 py-3 font-medium text-zinc-300 whitespace-nowrap">
                        <Link href={`/events?event_type=${event.event_type}`} className="hover:underline">
                          {event.event_type}
                        </Link>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        {event.application_name}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        {event.username || <span className="text-zinc-600">-</span>}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        {event.source_ip || <span className="text-zinc-600">-</span>}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          {data?.recent_events && data.recent_events.length > 0 && (
            <div className="mt-4 flex justify-end">
              <Link href="/events">
                <Button variant="outline" className="border-zinc-700 bg-transparent text-zinc-300 hover:bg-zinc-800">
                  View All Events
                </Button>
              </Link>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
